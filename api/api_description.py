"""What the generated description says about the OEDB endpoints.

The scenario-bundle half of `api/v0` got this treatment in #2475; this is the
other half, and it exists for the same reason. Every fact a client needs is
either in a signature or in prose, and only the ones in a signature are covered
by the drift guard -- so a status code, a parameter or a payload key that stops
being true makes the committed artifact disagree with a fresh generation and
the build says so.

Until this landed the OEDB endpoints were described by a **second**,
hand-written document (`oedb-rest-api/schema.json`) embedded on its own page.
Keeping it was a deliberate cost when the generated reference was built, priced
against what it appeared to carry. Measured, it carried almost nothing: all 49
of its request bodies were `"schema": {}`, its 64 operations shared 4 distinct
descriptions, and two of its paths (`advanced/has_sequence`, `has_type`) name
endpoints this platform does not route. So there was nothing to port and the
duplication bought nothing. It is retired, and this module is what replaces it.

**The serializers here describe; they do not validate.** Nothing in the request
path calls them -- these views read `request.data` by hand and have done for
years. Naming that plainly is the point of putting them here rather than in
`api/serializers.py`, where every other class is load-bearing. The risk it
creates is the one `oekg/read_serializers.py` also carries: a description that
drifts from the code with nothing to notice. Here the drift is bounded by how
little of it there is -- these payloads are dicts the views index into by key,
and the keys are named in the view a few lines below the annotation.

**One shape covers the whole `advanced/` block.** Those ~30 endpoints are one
view class produced by a factory (`api.helper.create_ajax_handler`), so the
envelope -- a `query` and an optional session -- is annotated once where the
factory builds it.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse
from rest_framework import serializers


def describes(description):
    """A JSON response that carries a body, described rather than schema'd."""
    return OpenApiResponse(response=OpenApiTypes.OBJECT, description=description)


# --------------------------------------------------------------------------
# What more than one OEDB endpoint answers.
# --------------------------------------------------------------------------

REFUSALS = {
    400: describes(
        "The request could not be carried out as sent: a payload key missing "
        "or holding something this endpoint cannot use, a column name that is "
        "not a Postgres identifier, or a query the database refused. The body "
        "carries `reason` or `error` naming which."
    ),
    401: describes("No credentials, or credentials this platform does not know."),
    403: describes(
        "Authenticated, but not permitted: the table belongs to somebody else, "
        "or is under embargo, or the operation needs a level of permission on "
        "it that this account does not hold."
    ),
    404: describes("No table of that name on this platform."),
    409: describes("A table of that name already exists. Table names are global."),
}

#: What every OEDB endpoint can answer, whatever it was asked to do.
ALWAYS = (400, 401, 403, 404)


def responses(success, *codes, also=None):
    """A success plus the refusals this endpoint can give.

    ``codes`` picks from the shared table; ``also`` is for a refusal only this
    endpoint gives, or one whose wording is its own.
    """
    described = {code: REFUSALS[code] for code in (codes or ALWAYS)}
    described.update(success)
    described.update(also or {})
    return described


TABLE = OpenApiParameter(
    name="table",
    location=OpenApiParameter.PATH,
    required=True,
    type=str,
    description=(
        "The table's name on this platform. **Names are global**: a table is "
        "addressed by name alone and no two tables share one, whichever topic "
        "they are published under."
    ),
)


# --------------------------------------------------------------------------
# The `advanced/` block: one envelope, thirty-odd actions.
# --------------------------------------------------------------------------


class AdvancedRequestSerializer(serializers.Serializer):
    """The envelope every `advanced/` endpoint takes.

    `query` is the action's own payload and its keys differ per endpoint --
    `{"table": ...}` for `has_table`, a where-clause structure for `search`.
    It is read leniently: an object, a JSON **string** holding one, or a
    one-element list holding either. That is not a design, it is what
    `_internal_execute` accepts, and a client sending the object is doing the
    plain thing.

    The two identifiers are how a sequence of calls shares one database
    session: `connection/open` hands back a `connection_id`, `cursor/open` a
    `cursor_id`, and passing them here puts this call inside that transaction.
    Without them the call runs on its own and commits by itself.
    """

    query = serializers.JSONField(
        required=False,
        help_text="This endpoint's own payload. See its description.",
    )
    connection_id = serializers.CharField(
        required=False, help_text="From `advanced/connection/open`."
    )
    cursor_id = serializers.CharField(
        required=False, help_text="From `advanced/cursor/open`."
    )


class AdvancedResponseSerializer(serializers.Serializer):
    """What every `advanced/` endpoint answers with.

    The result is under `content`, always -- the endpoints differ in what they
    put there, not in where. The two identifiers come back when the call ran
    inside a session, so a client can thread the next call onto the same one.
    """

    content = serializers.JSONField(
        help_text="The action's result. Its shape is the action's own."
    )
    connection_id = serializers.CharField(required=False)
    cursor_id = serializers.CharField(required=False)


ADVANCED_SESSION_NOTE = (
    "Part of the **advanced** interface: a thin, authenticated passthrough to "
    "the database that exists to be driven by a client library rather than by "
    "hand. A call carrying no `connection_id` runs and commits on its own; one "
    "carrying the pair from `connection/open` and `cursor/open` joins that "
    "transaction, which is what lets several calls be committed or rolled back "
    "together."
)


# --------------------------------------------------------------------------
# The table endpoints.
# --------------------------------------------------------------------------

#: Several of these read their payload out of a `query` key rather than off the
#: top level, and the ones that do are not consistent about it -- `move_publish`
#: accepts either. Stated per endpoint rather than assumed, because a client
#: that guesses wrong gets a `KeyError` rendered as a 400 with nothing useful
#: in it.
QUERY_WRAPPER = "The payload sits under a `query` key rather than at the top level."

IS_SANDBOX = OpenApiParameter(
    name="is_sandbox",
    location=OpenApiParameter.QUERY,
    required=False,
    type=bool,
    description=(
        "**Which schema the table is created in, and the one thing worth "
        "getting right here.** Send `true` and the table lands in the sandbox "
        "schema, which is where anything not meant to be published belongs. "
        "Omit it and the table is created in the public `data` schema, "
        "visible to everyone -- there is no confirmation step and no undo but "
        "deleting the table."
    ),
)

ROW_FILTERS = [
    OpenApiParameter(
        name="column",
        location=OpenApiParameter.QUERY,
        required=False,
        type=str,
        description=(
            "Return only this column. Repeat the parameter for several. Each "
            "must be a Postgres identifier; anything else is refused rather "
            "than ignored."
        ),
    ),
    OpenApiParameter(
        name="where",
        location=OpenApiParameter.QUERY,
        required=False,
        type=str,
        description=(
            "A filter, as `column=value`, `column>value`, `column<value` or "
            "the negated forms. Repeat the parameter to apply several. Not "
            "accepted together with a row id in the path -- the id already "
            "names the row."
        ),
    ),
    OpenApiParameter(
        name="orderby",
        location=OpenApiParameter.QUERY,
        required=False,
        type=str,
        description="Sort by this column. Not accepted together with a row id.",
    ),
    OpenApiParameter(
        name="limit",
        location=OpenApiParameter.QUERY,
        required=False,
        type=int,
        description="At most this many rows. Not accepted together with a row id.",
    ),
    OpenApiParameter(
        name="offset",
        location=OpenApiParameter.QUERY,
        required=False,
        type=int,
        description="Skip this many rows first. Not accepted together with a row id.",
    ),
    OpenApiParameter(
        name="form",
        location=OpenApiParameter.QUERY,
        required=False,
        type=str,
        description="`csv` returns the rows as CSV instead of JSON.",
    ),
]

DELIMITER = OpenApiParameter(
    name="delimiter",
    location=OpenApiParameter.QUERY,
    required=True,
    type=str,
    description=(
        "The CSV delimiter of the body. **Required**: it is not guessed, "
        "because guessing it wrong loads a whole file into the wrong columns."
    ),
)


class TableCreateSerializer(serializers.Serializer):
    """The body of a table create: columns, constraints and metadata.

    Under `query`, and the reason is historical rather than principled -- the
    same wrapper the `advanced/` endpoints use, kept here because clients send
    it.
    """

    query = serializers.JSONField(
        help_text=(
            "`columns` (required) is a list of `{name, data_type, "
            "is_nullable, ...}`; `constraints` is a list of constraint "
            "definitions; `metadata` is an OEMetadata document. Without "
            "`metadata` a minimal one is generated from the columns."
        )
    )
    embargo = serializers.JSONField(
        required=False,
        help_text=(
            "An embargo to apply once the table exists. Also accepted inside "
            "`query`."
        ),
    )


class TableAlterSerializer(serializers.Serializer):
    """The body of a change to an existing table's columns or constraints.

    Top level, not under `query` -- unlike the create on the same URL, which
    is the kind of thing only a description can warn about.
    """

    type = serializers.CharField(
        help_text="`column` or `constraint`: which kind of change this is."
    )
    action = serializers.CharField(
        required=False, help_text="`ADD` or `DROP`, for a constraint change."
    )
    name = serializers.CharField(required=False, help_text="For a column change.")
    constraint_type = serializers.CharField(
        required=False,
        help_text="`FOREIGN KEY`, `PRIMARY KEY`, `UNIQUE` or `CHECK`.",
    )
    constraint_name = serializers.CharField(required=False)
    constraint_parameter = serializers.CharField(
        required=False, help_text="What the constraint applies to -- a column name."
    )
    reference_table = serializers.CharField(required=False)
    reference_column = serializers.CharField(required=False)


class QueryWrappedSerializer(serializers.Serializer):
    """A payload this endpoint reads out of a `query` key."""

    query = serializers.JSONField()


class RowSerializer(QueryWrappedSerializer):
    """One row, or the values to set on the rows a filter selects.

    Column names are the keys. On a `PUT` an `id` in the payload must match
    the one in the path if it is sent at all: an id never changes.
    """


class SparqlSerializer(serializers.Serializer):
    """A read-only SPARQL query against the OEKG."""

    query = serializers.CharField(
        help_text=(
            "The query. **Reads only** -- anything that would update or delete "
            "is refused, whatever the caller's permissions."
        )
    )
    format = serializers.CharField(
        required=False,
        help_text=(
            "The result format the graph store should use. Defaults to "
            "`json`; anything else is returned with the store's own content "
            "type rather than parsed."
        ),
    )


# --------------------------------------------------------------------------
# The legacy schema-qualified table addresses.
# --------------------------------------------------------------------------

#: `/api/v0/schema/<anything>/tables/...` is an older spelling of
#: `/api/v0/tables/...`, still routed. Its schema segment is **not captured**
#: (`api/urls.py`, `pgsql_qualifier`), so no view has ever received it: any
#: value routes to the same table, because table names are global.
LEGACY_TABLE_PREFIX = "/api/v0/schema/"

#: How the generator renders that route on its own. Django's `simplify_regex`
#: leaves an uncaptured group as the character class it was written with, so
#: the address arrives in the description as something no client can call.
LEGACY_TABLE_PATTERN = "/api/v0/schema/[\\w\\d_]/tables/"

LEGACY_TABLE_PATH = "/api/v0/schema/{schema}/tables/"

LEGACY_SCHEMA_PARAMETER = {
    "in": "path",
    "name": "schema",
    "required": True,
    "schema": {"type": "string"},
    "description": (
        "**Ignored.** This segment is not captured by the route, so no value "
        "of it changes where the request goes: table names are global on this "
        "platform and the table is found by name alone. It is here because "
        "the address requires a segment, not because it selects anything."
    ),
}

LEGACY_TABLE_NOTE = (
    "\n\n**Deprecated.** This is the older, schema-qualified spelling of the "
    "same endpoint. Use `{canonical}` instead: it reaches the same view, and "
    "the `{{schema}}` segment here selects nothing."
)


def name_the_legacy_table_routes(result, generator, request, public):
    """Make the legacy table addresses callable, and say they are superseded.

    A drf-spectacular postprocessing hook. Three things are wrong with those
    paths as generated, and all three are consequences of one cause -- the
    route's schema segment is an uncaptured group:

    - **The address cannot be called.** It arrives as
      `/api/v0/schema/[\\w\\d_]/tables/...`, the character class the route was
      written with. Renamed here to `{schema}`, which is what a reader needs to
      build a request.
    - **The segment looks like it selects something.** It does not, and the
      parameter added here says so. The retired hand-written description
      documented it as though picking it mattered, which is the more
      expensive of the two mistakes.
    - **Nothing said it was the older spelling.** Marked deprecated, with the
      canonical address named.

    Done here rather than at the route because one view serves both spellings:
    an annotation on the view would deprecate the canonical address too.
    """
    paths = result.get("paths", {})
    for path in [p for p in paths if p.startswith(LEGACY_TABLE_PATTERN)]:
        renamed = path.replace(LEGACY_TABLE_PATTERN, LEGACY_TABLE_PATH, 1)
        canonical = path.replace(LEGACY_TABLE_PATTERN, "/api/v0/tables/", 1)
        operations = paths.pop(path)
        for operation in operations.values():
            if not isinstance(operation, dict):
                continue
            operation["deprecated"] = True
            operation["parameters"] = [
                LEGACY_SCHEMA_PARAMETER,
                *operation.get("parameters", []),
            ]
            operation["description"] = operation.get(
                "description", ""
            ) + LEGACY_TABLE_NOTE.format(canonical=canonical)
        paths[renamed] = operations
    return result
