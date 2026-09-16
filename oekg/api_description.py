"""What the generated description says about these endpoints, written once.

Not to be confused with `oekg/shape.py`, which is the SHACL shape, or with
`/api/v0/schema/`, which serves the whole document this contributes to. What
is assembled here is the prose and the signatures of one API's operations.

Every fact a client needs is either in a signature or in prose. The ones that
*can* be in a signature must be, because only those are covered by the drift
guard: a parameter, a status code or a response header that stops being true
makes the committed artifact disagree with a fresh generation and the build
says so. Prose about the same fact would simply go stale in silence.

So this module is the vocabulary of the scenario-bundle API's own contract --
the required `If-Match`, the entity tag that feeds it, the three precondition
refusals, the ceilings -- and each endpoint spends it rather than restating it.
Written here rather than at the endpoints for the reason `describes_a_removal`
was written once: a description repeated eight times is a description that will
be right in six of them.

Three things about the shape of what follows are deliberate.

**The auth expectation is prose, and it is not optional.** It is the one fact
in this contract that a reader of the reference page currently has to infer
from a symbol that means the reverse: Swagger UI draws its padlock closed when
an operation's security requirements are already satisfied, and a public read
satisfies them unconditionally. So a public read renders *locked* and a write
needing a token renders *unlocked*. The security blocks are correct -- an empty
requirement object is OpenAPI for "anonymous is also acceptable" -- and are
deliberately left alone; dropping it to make the icons read the right way would
make the document claim that reading a published research record needs a login.
The words are what fix it, and a test cross-checks each sentence against the
same `security` block the icon is drawn from.

**A description is composed from the handler's own docstring**, not written
here instead of it. The prose that explains an endpoint belongs next to the
endpoint, where the next person to change it will be; what this module adds is
the sentence that is the same at every endpoint of one kind.

**Success responses carry a schema as well as a description, and the schema is
not the request serializer.** Every response here is the writable payload *plus*
`_meta`, and `_meta` differs from endpoint to endpoint: it carries the version,
it gains the resolved labels when they were asked for, and it grows a key when
something was lost after the graph had already committed. Pointing a response at
the serializer that validates the write would therefore describe a body nobody
receives, and would invite a client to treat `_meta` as surplus and strip it --
and `_meta` is where the version its next write must send lives. So
`oekg/read_serializers.py` states each read shape as *the write serializer plus
`_meta`*, by subclassing it, and `oekg/tests/test_response_schema.py` validates
a real response from every endpoint against the schema that produces. A response
schema nothing checks is a claim, and the drift guard cannot see it go stale:
the serializer and the artifact would agree with each other while both drifted
from what the view actually sends.

**Refusals carry a description and no schema.** A `400` here is either
`{"detail": ...}` or the framework's field-keyed map of validation errors, and
a schema for "one or the other" tells a client less than the sentence does.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import inspect

from drf_spectacular.openapi import AutoSchema
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers

from oekg.read_serializers import RemovalSerializer


class CollectionSchema(AutoSchema):
    """Name a collection's `GET` a list, which is what it is.

    The generator already does this for views it can recognise as list views;
    it cannot recognise these, because they are plain `APIView`s with no
    serializer or paginator attribute to read. Left alone it calls the
    collection read and the detail read of one resource `..._retrieve` both,
    then resolves the collision with a numeral -- a name no reader can map back
    to an endpoint.

    A rule rather than an id per endpoint, because the handlers are shared: one
    implementation serves scenarios and study reports, so an id written at the
    handler would name the wrong resource and an id written per subclass would
    have to be written again for the next part.
    """

    def get_operation_id(self):
        operation_id = super().get_operation_id()
        if self.method != "GET":
            return operation_id
        subject, _, action = operation_id.rpartition("_")
        return f"{subject}_list" if action == "retrieve" else operation_id


# --------------------------------------------------------------------------
# The auth expectation, in words.
# --------------------------------------------------------------------------

_PADLOCK_MET = (
    "(The reference page draws a **closed** padlock here. It marks a security "
    "requirement the reader already meets, not a protected endpoint -- on that "
    "page the closed padlock is the public one.)"
)

_PADLOCK_UNMET = (
    "(The reference page draws an **open** padlock here. It marks a security "
    "requirement not yet met -- use *Authorize* -- not an unprotected "
    "endpoint.)"
)

PUBLIC = (
    "**Public.** No authentication is required, and sending credentials "
    "changes nothing about the answer. The OEKG SPARQL endpoint already serves "
    "the same data, so a token here would protect nothing while making "
    "published research records awkward to read. " + _PADLOCK_MET
)

ANY_ACCOUNT = (
    "**Requires authentication.** Any authenticated account may create a "
    "scenario bundle, and the account that creates one becomes its owner, "
    "which is what lets it write to the bundle afterwards. " + _PADLOCK_UNMET
)

OWNER_ONLY = (
    "**Requires authentication**, and only an owner of this scenario bundle "
    "may write to it -- a bundle with no recorded owner can be changed by an "
    "administrator only. Ownership is the bundle's, whatever part of it this "
    "operation names. " + _PADLOCK_UNMET
)


# --------------------------------------------------------------------------
# Parameters and headers.
# --------------------------------------------------------------------------

IF_MATCH = OpenApiParameter(
    name="If-Match",
    location=OpenApiParameter.HEADER,
    required=True,
    type=str,
    description=(
        "The entity tag of the bundle state this write applies to, as returned "
        "in `ETag` by the read it was built from. **Required, with no "
        "opt-out**: without it a client that has never heard of the header "
        "would overwrite a change made since it read, and neither party would "
        "be told. `*` is refused as an absent header rather than honoured as a "
        "wildcard, because it satisfies the letter of the precondition while "
        "withholding the one thing the precondition is for. A weak validator "
        '(`W/"4"`) and a bare number are both read as the version they '
        "plainly name."
    ),
)

ETAG = OpenApiParameter(
    name="ETag",
    location=OpenApiParameter.HEADER,
    response=[200, 201],
    type=str,
    description=(
        "The bundle's current version. Send it back in `If-Match` on the next "
        "write. It is returned on **every** response that carries one, writes "
        "included, so a pipeline reads once per run and chains its writes; "
        "only a lost response forces a re-read. A sub-resource has no version "
        "of its own -- the tag here is always the containing bundle's."
    ),
)

LOCATION = OpenApiParameter(
    name="Location",
    location=OpenApiParameter.HEADER,
    response=[201],
    type=str,
    description=(
        "Where the created resource can be read. The identifier in it was "
        "minted by the server: this API accepts none from a client."
    ),
)


def addresses(name, description):
    """A path parameter, typed and explained.

    Declared because the generator cannot derive one here: these are plain
    `APIView`s with no queryset for it to read a field off, so an undeclared
    path parameter arrives in the description untyped and unexplained. Every
    identifier in this API is a server-minted uuid, which is worth saying once
    per parameter rather than leaving a client to infer it from an example.
    """
    return OpenApiParameter(
        name=name,
        location=OpenApiParameter.PATH,
        required=True,
        type=str,
        description=description,
    )


#: The identifiers this API's addresses are built from. All server-minted: a
#: client supplies none of them anywhere.
BUNDLE_UID = addresses(
    "uid",
    "The scenario bundle's identifier, as minted by the server on create and "
    "returned in `_meta.uid`. A pipeline holding no state finds it again with "
    "`GET /api/v0/scenario-bundles/?acronym=...`.",
)

PART_PID = addresses(
    "pid",
    "The identifier of the part this address names -- a scenario factsheet or "
    "a study report, depending on the route.",
)

SCENARIO_SID = addresses(
    "sid",
    "The identifier of the scenario factsheet these dataset links hang off.",
)

LINK_DID = addresses("did", "The dataset link's identifier.")


def expands(*values, description):
    """`?expand=` as this endpoint offers it.

    Declared only where the response actually carries the expansion, which is
    narrower than where one is accepted: the parameter is parsed once per view
    rather than once per handler, so the four deletes below a bundle take one
    and so does the bundle's own `PATCH`, and none of them acts on it. A
    removal report has nowhere to put resolved labels; the bundle patch simply
    does not resolve, unlike the part writes next to it.

    Left undocumented in both cases rather than made to work. Documentation
    describes what is there -- making an endpoint do something so that a line
    about it becomes true is a behaviour change wearing a documentation slice's
    clothes, and this one is not needed by anything.
    """
    return OpenApiParameter(
        name="expand",
        location=OpenApiParameter.QUERY,
        required=False,
        type=str,
        enum=list(values),
        description=(
            description + " A value this endpoint does not offer is refused "
            "with `400` rather than ignored, and the refusal happens before "
            "anything is written, so nothing was written when one arrives. "
            "Values are comma-separated, which matters once an endpoint offers "
            "two; none offers two yet, and the enum says which one it offers."
        ),
    )


EXPAND_LABELS = expands(
    "labels",
    description=(
        "`labels` resolves the ontology terms this resource picks into "
        "`_meta.labels`, from a small label subset rather than the full OEO."
    ),
)


# --------------------------------------------------------------------------
# Responses.
# --------------------------------------------------------------------------


def json_body(description):
    """A response carrying a JSON body, described rather than schema'd.

    Every refusal in this API is a JSON object, and so is every success bar
    one: the bundle read also serves two RDF forms, and says so itself.
    """
    return OpenApiResponse(response=OpenApiTypes.OBJECT, description=description)


def a_page_of(entry, description):
    """A collection's success: the entries, and the envelope around them.

    The envelope is built here rather than declared per endpoint because every
    collection in this API is paged by the same class, and a client told a page
    size but not the shape of a page has to guess the rest.
    """
    return OpenApiResponse(
        response=inline_serializer(
            name=f"{entry.__name__.removesuffix('Serializer')}Page",
            fields={
                "count": serializers.IntegerField(),
                "next": serializers.URLField(allow_null=True),
                "previous": serializers.URLField(allow_null=True),
                "results": entry(many=True),
            },
        ),
        description=description,
    )


#: The refusals shared across these endpoints, each said once. An endpoint that
#: can refuse for a reason of its own overrides the entry rather than adding a
#: second code, so a client never meets one status meaning two things.
REFUSALS = {
    400: json_body(
        "Refused, and **nothing was written**. The body is either `detail` "
        "with one sentence, or -- when the payload failed the serializer -- a "
        "map from field name to what was wrong with it. The payload named a key the "
        "closed bundle shape does not have, or a value the shape's own `sh:in` "
        "list does not allow, or the change would introduce a violation of the "
        "OEKG shape -- `violations` then names them, and "
        "`pre_existing_violations` counts the ones this write is not blamed "
        "for. A write is judged by what it *introduces*, so a bundle that was "
        "already non-conforming can still be repaired through this API."
    ),
    401: json_body(
        "No credentials, or credentials this platform does not recognise. "
        "Reads here need none; writes do."
    ),
    403: json_body(
        "Authenticated, but not an owner of this scenario bundle. A bundle "
        "with no recorded owner is administrator-only."
    ),
    404: json_body("No such scenario bundle, or no such resource within it."),
    409: json_body(
        "The bundle moved between the read this write was prepared from and "
        "the write itself, so **nothing was written**. Read it again, apply "
        "the change to what comes back, and retry."
    ),
    412: json_body(
        "`If-Match` named a version, and it is not the current one. Nothing "
        "was written. The response says which version the bundle is at."
    ),
    428: json_body(
        "`If-Match` was absent, so this write did not say which version it was "
        "editing and nothing was written. The response names the current "
        "entity tag to send."
    ),
    429: json_body(
        "Throttled. These endpoints are public to read, so they carry a "
        "ceiling for anonymous callers and a separate one per account. "
        "`Retry-After` says how long to wait."
    ),
    503: json_body(
        "The OEKG graph store could not be reached, or the shape this API "
        "validates against is not installed on this server. Neither is an "
        "answer about the bundle: nothing was read and nothing was written."
    ),
}

#: What any endpoint here can answer regardless of what it was asked to do.
ALWAYS = (429, 503)

#: A read of something that may not be there.
READ_REFUSALS = (400, 404, *ALWAYS)

#: A write to a bundle that already exists: who you are, what you may do, and
#: the three precondition refusals that mean three different things.
WRITE_REFUSALS = (400, 401, 403, 404, 409, 412, 428, *ALWAYS)


def paging(paginator):
    """`page` and `page_size`, as every collection in this API spells them.

    Takes the paginator rather than its two numbers: the default and the
    ceiling are that class's to state, and a call site holding them apart could
    quote a ceiling from one paginator beside a default from another.

    Declared rather than inferred: these are plain views, so nothing else tells
    a reader that a collection is paged at all, let alone where its ceiling is.
    `page`/`page_size` and not the user interface's `resultsPerPage` -- meeting
    two conventions inside one API is worse for a client than meeting one that
    differs from a legacy view it does not call.
    """
    return [
        OpenApiParameter(
            name="page",
            location=OpenApiParameter.QUERY,
            required=False,
            type=int,
            description="Which page of the result to return. 1-based.",
        ),
        OpenApiParameter(
            name="page_size",
            location=OpenApiParameter.QUERY,
            required=False,
            type=int,
            description=(
                f"How many entries a page holds. Defaults to "
                f"{paginator.page_size} and is capped at "
                f"{paginator.max_page_size}: this endpoint is public, and no "
                "public collection here has an unbounded mode."
            ),
        ),
    ]


def read_responses(success, refusals=READ_REFUSALS, extra=None):
    """A read's responses, for a caller that cannot use the decorator.

    The two part endpoints are shared by scenarios and study reports, so the
    handler cannot name the body it answers with -- only the subclass knows
    which serializer that is. Everything else about those operations stays on
    the handler; the subclass supplies the body, and needs the refusals back to
    do it, because `extend_schema` replaces a response map rather than merging
    into one.
    """
    return _responses(refusals, {200: success}, extra)


def write_responses(success, extra=None):
    """A guarded write's responses, for the same reason."""
    return _responses(WRITE_REFUSALS, success, extra)


def _responses(codes, success, extra, refusals_in=None):
    """The refusals this operation can give, plus the success it describes.

    ``refusals_in`` pins the refusals to one media type, for the one operation
    that serves its success in three. The generator reads an operation's
    content types off the view's renderers and applies them to every response
    it declares -- so without this, the bundle read would offer `404` as
    turtle, which `GraphRenderer` deliberately never does: an error body is a
    dict, and it is rendered as JSON with the response's own content type
    corrected to match. Declaring a form nothing can arrive in is the failure
    this module exists to remove, not one to introduce elsewhere.
    """

    def key(code):
        return code if refusals_in is None else (code, refusals_in)

    described = {key(code): REFUSALS[code] for code in codes}
    described.update(success)
    described.update({key(code): value for code, value in (extra or {}).items()})
    return described


def _describing(note, **schema):
    """`extend_schema`, with the auth expectation appended to the docstring.

    The docstring stays the source of the prose -- it is what the next person
    to change the endpoint reads -- and this adds the one sentence that is the
    same at every endpoint of its kind.
    """

    def decorate(handler):
        described = inspect.cleandoc(handler.__doc__ or "")
        description = f"{described}\n\n{note}" if described else note
        return extend_schema(description=description, **schema)(handler)

    return decorate


def describes_a_public_read(
    success,
    *,
    parameters=(),
    responses=None,
    refusals=READ_REFUSALS,
    refusals_in=None,
    entity_tag=True,
    **schema,
):
    """A read: public, throttled, and answering `404` for what is not there.

    ``refusals`` is narrowed by the one read with nothing to be missing: a
    filter matching no bundle is an empty page, not an absent collection.

    ``entity_tag`` is off for the two reads that carry none -- a listing is not
    one bundle's state, and a history is a ledger of events rather than a
    state. Declaring a header an endpoint does not return would send a client
    looking for the version it needs in a response that has never held one.
    """
    return _describing(
        PUBLIC,
        parameters=[*([ETAG] if entity_tag else []), *parameters],
        responses=_responses(refusals, {200: success}, responses, refusals_in),
        **schema,
    )


def describes_a_creation(success, *, parameters=(), responses=None, **schema):
    """The one write with nothing to guard: there is no bundle yet.

    So no `If-Match`, no `412`/`428`, and no `403` -- any authenticated account
    may create a bundle. The `409` it keeps is not a version conflict but an
    acronym already taken, which is a different accident with the same advice.
    """
    return _describing(
        ANY_ACCOUNT,
        parameters=[ETAG, LOCATION, *parameters],
        responses=_responses((400, 401, 409, *ALWAYS), success, responses),
        **schema,
    )


def describes_a_guarded_write(
    success, *, parameters=(), responses=None, entity_tag=True, **schema
):
    """A write to an existing bundle: owner only, and guarded on its version."""
    return _describing(
        OWNER_ONLY,
        parameters=[
            IF_MATCH,
            *([ETAG] if entity_tag else []),
            # Read off the success this write declares rather than asked for
            # separately: a write that answers `201` put the resource
            # somewhere, and where is not a fact a second argument should be
            # able to disagree about.
            *([LOCATION] if 201 in success else []),
            *parameters,
        ],
        responses=_responses(WRITE_REFUSALS, success, responses),
        **schema,
    )


def describes_a_removal(*parameters):
    """A delete below a bundle. Takes the parameters of the route it is on.

    Written once and applied to every delete below a bundle, so the description
    a client reads cannot drift from the one `removed` actually implements.
    The parameters are the one thing it cannot know for itself: a scenario's
    delete is addressed by two identifiers and a dataset link's by three.
    """
    return describes_a_guarded_write(
        {
            200: OpenApiResponse(
                response=RemovalSerializer,
                description=(
                    "Removed. The body names what was **deleted** and what "
                    "was only **unlinked**, which no status code can say: a "
                    "node another bundle still cites is kept and detached "
                    "rather than destroyed. Only the downgraded nodes are "
                    "listed -- the shared regions, authors and ontology terms "
                    "every delete detaches are the rule, not the news."
                ),
            )
        },
        parameters=list(parameters),
    )
