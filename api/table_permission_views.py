"""A Table's Holders through the REST API (#2570, spec #2551, WF-08 decision 12).

The third entry point onto the permission service, beside the access drawer
and the Table's permission page. Nothing here decides who may do what: every
read is ``login.table_roles.table_access`` and every write one of its
functions, called with ``via="api"``, so each rule holds here exactly as it
does there and the log line names this entry point.

What this module adds is the translation into this API's conventions:

- a Holder is addressed by the service's own key, ``user:<pk>`` or
  ``org:<pk>``, in the URL;
- the service's refusals become statuses: ``InvalidRequest`` 400 (with the
  ``field`` it names), ``NotAllowed`` 403, and ``LastAdmin`` and
  ``ConfirmationNeeded`` both 409, told apart by ``code``. A request naming a
  Holder the Table does not have is 404 rather than the service's 400, because
  it is the URL that names nothing;
- a confirmation cannot be a dialog, so a 409 with ``code:
  confirmation_needed`` is answered by sending the same request again with
  ``confirm`` -- in the body of a ``PATCH``, as a query parameter of a
  ``DELETE``, whose body a client cannot rely on being sent.

Reading needs a login and no role. The Table's permission page already shows
every Table's Holders to anyone, so restricting the API further would protect
nothing; the login is there because the answer is the viewer's
(``can_manage``, ``you``).

The serializers below describe the payloads for the generated reference; the
views read ``request.data`` by key and leave every check to the service, so a
rule is never stated twice.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import serializers, status
from rest_framework.request import Request
from rest_framework.views import APIView

from api.api_description import TABLE, describes, responses
from api.api_tags import TABLE_PERMISSIONS
from api.error import APIError
from api.helper import JsonLikeResponse, api_exception
from api.utils import table_or_404
from login import table_roles
from login.table_roles import (
    ORGANIZATION,
    ROLES,
    USER,
    ConfirmationNeeded,
    InvalidRequest,
    LastAdmin,
    NotAllowed,
)

VIA = "api"

#: What a 409 carries in ``code``, so a client can tell "ask and send again"
#: from "this cannot be done as it stands".
CONFIRMATION_NEEDED = "confirmation_needed"
LAST_ADMIN = "last_admin"


# --------------------------------------------------------------------------
# What the reference says. These describe; the service validates.
# --------------------------------------------------------------------------


class RoleSerializer(serializers.Serializer):
    level = serializers.IntegerField(help_text="The stored level, as sent in writes.")
    label = serializers.CharField()
    description = serializers.CharField()


class HolderSerializer(serializers.Serializer):
    holder = serializers.CharField(
        help_text="The Holder's key, `user:<id>` or `org:<id>`: its address below "
        "`permissions/`."
    )
    kind = serializers.ChoiceField(choices=[USER, ORGANIZATION])
    id = serializers.IntegerField()
    name = serializers.CharField()
    level = serializers.IntegerField()
    role = serializers.CharField(help_text="The level's name.")
    roles = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="The levels this Holder may be changed to. An organization "
        "stops at Data maintainer; one holding Admin from before that rule keeps "
        "it in this list, and can only be lowered.",
    )
    you = serializers.BooleanField(
        help_text="Whether this is the caller, or an organization they belong to."
    )
    members = serializers.IntegerField(
        required=False, help_text="An organization's member count."
    )


class HolderListSerializer(serializers.Serializer):
    table = serializers.CharField()
    can_manage = serializers.BooleanField(
        help_text="Whether the caller is a Table admin here and may write."
    )
    roles = RoleSerializer(many=True, help_text="Every role a Holder can be given.")
    holders = HolderSerializer(many=True, help_text="Users first, then organizations.")


class HolderAddSerializer(serializers.Serializer):
    user = serializers.CharField(
        required=False, help_text="A user, by name. Give this or `organization`."
    )
    organization = serializers.IntegerField(
        required=False,
        help_text="An organization the caller is a member of, by id.",
    )
    level = serializers.IntegerField(help_text="One of the levels under `roles`.")


class HolderChangeSerializer(serializers.Serializer):
    level = serializers.IntegerField(help_text="Required: one of the Holder's `roles`.")
    confirm = serializers.BooleanField(
        required=False,
        help_text="`true` after a 409 with `code: confirmation_needed`.",
    )


HOLDER = OpenApiParameter(
    name="holder",
    location=OpenApiParameter.PATH,
    required=True,
    type=str,
    description="The Holder's key as the list gives it: `user:<id>` or `org:<id>`.",
)

CONFIRM = OpenApiParameter(
    name="confirm",
    location=OpenApiParameter.QUERY,
    required=False,
    type=bool,
    description="`true` after a 409 with `code: confirmation_needed`.",
)

ADMIN_ONLY = (
    "Needs a login and Table admin on the table: Admin, directly or through an "
    "organization, or platform admin. The same rules hold as in the table's "
    "access drawer and permission page."
)

REFUSED = describes(
    "The request cannot be carried out as sent: a level outside the offered "
    "roles, Admin for an organization, an organization the caller is not a "
    "member of, or a user that does not exist. `reason` says which and "
    "`field` names the input. Nothing was written."
)

NOT_ADMIN = describes("Not a Table admin on this table. Nothing was written.")

NO_HOLDER = describes(
    "No table of that name, or the table has no such Holder -- which a "
    "repeated delete also meets."
)

CONFLICT = describes(
    "Nothing was written, and `code` says why. `last_admin`: the table must "
    "keep a user with direct Admin -- give someone else Admin first; "
    "confirming does not change this answer. `confirmation_needed`: the "
    "change would take the caller's own Admin, or all their access, away. "
    "`reason` says which; send the same request again with `confirm` to make "
    "it."
)


# --------------------------------------------------------------------------
# The views.
# --------------------------------------------------------------------------


def _refusal(error) -> JsonResponse:
    """The service's refusal as this API's answer."""
    if isinstance(error, InvalidRequest):
        status_code = 404 if error.field == "holder" else 400
        return JsonResponse(
            {"reason": error.message, "field": error.field}, status=status_code
        )
    if isinstance(error, NotAllowed):
        return JsonResponse({"reason": error.message}, status=403)
    code = LAST_ADMIN if isinstance(error, LastAdmin) else CONFIRMATION_NEEDED
    return JsonResponse({"reason": error.message, "code": code}, status=409)


REFUSALS = (InvalidRequest, NotAllowed, LastAdmin, ConfirmationNeeded)


def _signed_in(request):
    if request.user.is_anonymous:
        raise APIError("Authentication required", 401)
    return request.user


def _body(request) -> dict:
    """The payload's keys, or none for a body that is not an object."""
    return request.data if isinstance(request.data, dict) else {}


def _confirmed(value) -> bool:
    """Only an explicit yes confirms."""
    return value is True or str(value).lower() == "true"


def _holder(holder) -> dict:
    body = {
        "holder": holder.key,
        "kind": holder.kind,
        "id": holder.pk,
        "name": holder.name,
        "level": holder.level,
        "role": holder.role,
        "roles": [role.level for role in holder.roles],
        "you": holder.you,
    }
    if holder.kind == ORGANIZATION:
        body["members"] = holder.members
    return body


def _holder_after(user, table, key, status_code=200) -> JsonResponse:
    """The Holder as the list now shows it."""
    holder = table_roles.table_access(user, table).holder(key)
    return JsonResponse(_holder(holder), status=status_code)


@extend_schema(tags=[TABLE_PERMISSIONS])
class TablePermissionsAPIView(APIView):
    """A Table's Holders: list them, add one."""

    @extend_schema(
        operation_id="tables_permissions_list",
        summary="List a table's Holders",
        description=(
            "The users and organizations holding a role on the table, each "
            "with its level and the levels it may be changed to, plus every "
            "role a Holder can be given. Needs a login and no role: the "
            "table's permission page shows the same list to anyone. "
            "`can_manage` says whether the caller may write."
        ),
        parameters=[TABLE],
        responses=responses(
            {200: OpenApiResponse(HolderListSerializer, "The table's Holders.")},
            401,
            404,
        ),
    )
    @api_exception
    @method_decorator(never_cache)
    def get(self, request: Request, table: str) -> JsonLikeResponse:
        table_obj = table_or_404(table=table)
        access = table_roles.table_access(_signed_in(request), table_obj)
        return JsonResponse(
            {
                "table": table_obj.name,
                "can_manage": access.can_manage,
                "roles": [
                    {
                        "level": role.level,
                        "label": role.label,
                        "description": role.description,
                    }
                    for role in ROLES
                ],
                "holders": [_holder(holder) for holder in access.holders],
            }
        )

    @extend_schema(
        summary="Give a user or an organization a role on a table",
        description=(
            "Adds a Holder: a user by name, at any role, or an organization "
            "the caller is a member of, at Data maintainer at most -- Admin is "
            "given to users only. A Holder the table already has is refused; "
            "change its role instead. " + ADMIN_ONLY
        ),
        parameters=[TABLE],
        request=HolderAddSerializer,
        responses=responses(
            {201: OpenApiResponse(HolderSerializer, "The new Holder.")},
            401,
            404,
            also={400: REFUSED, 403: NOT_ADMIN},
        ),
    )
    @api_exception
    def post(self, request: Request, table: str) -> JsonLikeResponse:
        table_obj = table_or_404(table=table)
        user = _signed_in(request)
        data = _body(request)
        named = [kind for kind in ("user", "organization") if kind in data]
        if len(named) > 1:
            return _refusal(
                InvalidRequest("Name a user or an organization, not both.", "kind")
            )
        kind = {"user": USER, "organization": ORGANIZATION}.get(
            named[0] if named else None, ""
        )
        who = data.get(named[0]) if named else None
        try:
            change = table_roles.add(
                user, table_obj, kind, who, data.get("level"), via=VIA
            )
        except REFUSALS as error:
            return _refusal(error)
        return _holder_after(
            user, table_obj, f"{change.kind}:{change.pk}", status.HTTP_201_CREATED
        )


@extend_schema(tags=[TABLE_PERMISSIONS])
class TableHolderAPIView(APIView):
    """One Holder of a Table: change its role, remove it."""

    @extend_schema(
        summary="Change a Holder's role on a table",
        description=(
            "Gives the Holder another of its `roles`. The role it already "
            "holds changes nothing and answers 200. A change that would leave "
            "the table without a user holding direct Admin is refused; one "
            "that takes the caller's own Admin away asks for `confirm` first. "
            + ADMIN_ONLY
        ),
        parameters=[TABLE, HOLDER],
        request=HolderChangeSerializer,
        responses=responses(
            {200: OpenApiResponse(HolderSerializer, "The Holder as it now stands.")},
            401,
            also={400: REFUSED, 403: NOT_ADMIN, 404: NO_HOLDER, 409: CONFLICT},
        ),
    )
    @api_exception
    def patch(self, request: Request, table: str, holder: str) -> JsonLikeResponse:
        table_obj = table_or_404(table=table)
        user = _signed_in(request)
        data = _body(request)
        try:
            table_roles.change(
                user,
                table_obj,
                holder,
                data.get("level"),
                via=VIA,
                confirmed=_confirmed(data.get("confirm")),
            )
        except REFUSALS as error:
            return _refusal(error)
        return _holder_after(user, table_obj, holder)

    @extend_schema(
        summary="Remove a Holder from a table",
        description=(
            "Takes the Holder's role away; removal is the only way to no "
            "access. The last user holding direct Admin cannot be removed. "
            "Removing the caller's own Admin, or all their access, asks for "
            "`confirm` first -- as a query parameter here, because a client "
            "cannot rely on a DELETE's body being sent. " + ADMIN_ONLY
        ),
        parameters=[TABLE, HOLDER, CONFIRM],
        request=None,
        responses=responses(
            {204: OpenApiResponse(description="Removed. No body.")},
            401,
            also={403: NOT_ADMIN, 404: NO_HOLDER, 409: CONFLICT},
        ),
    )
    @api_exception
    def delete(self, request: Request, table: str, holder: str) -> JsonLikeResponse:
        table_obj = table_or_404(table=table)
        user = _signed_in(request)
        try:
            table_roles.remove(
                user,
                table_obj,
                holder,
                via=VIA,
                confirmed=_confirmed(request.query_params.get("confirm")),
            )
        except REFUSALS as error:
            return _refusal(error)
        return HttpResponse(status=status.HTTP_204_NO_CONTENT)
