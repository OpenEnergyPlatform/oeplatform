"""What the generated description says about these endpoints, written once.

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

**Success responses carry a description, not a serializer.** Every response in
this API is the writable payload *plus* `_meta`, and `_meta` is not the same
from one endpoint to the next -- it carries the version, and it grows a key
when something was lost after the graph committed. A schema claiming the
response is the request serializer would be wrong in exactly the direction that
hurts: a client would treat `_meta` as surplus and strip it, and `_meta` is
where the version its next write has to send lives. Client generation is out of
scope for this description (WF-13), so the honest description is the useful one.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import inspect

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema

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


def expands(*values, description):
    """`?expand=` as this endpoint offers it.

    Declared only where the response actually carries the expansion. The
    parameter is parsed once per view rather than once per handler, so a delete
    below a bundle tolerates one too -- but a removal report has nowhere to put
    resolved labels, and a parameter documented where it does nothing is worse
    than one left undocumented.
    """
    return OpenApiParameter(
        name="expand",
        location=OpenApiParameter.QUERY,
        required=False,
        type=str,
        enum=list(values),
        description=(
            description + " Comma-separated, so asking for two is asking once. "
            "A value this endpoint does not offer is refused with `400` rather "
            "than ignored, and the refusal happens before anything is written."
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


def describes(description):
    """A response that carries a body. JSON unless the operation says otherwise.

    Named for what it does rather than for what it returns. The obvious name is
    `body`, and it is taken: half the read paths in this API already call their
    assembled payload that, so importing it shadows theirs.
    """
    return OpenApiResponse(response=OpenApiTypes.OBJECT, description=description)


#: The refusals shared across these endpoints, each said once. An endpoint that
#: can refuse for a reason of its own overrides the entry rather than adding a
#: second code, so a client never meets one status meaning two things.
REFUSALS = {
    400: describes(
        "Refused, and **nothing was written**. The payload named a key the "
        "closed bundle shape does not have, or a value the shape's own `sh:in` "
        "list does not allow, or the change would introduce a violation of the "
        "OEKG shape -- `violations` then names them, and "
        "`pre_existing_violations` counts the ones this write is not blamed "
        "for. A write is judged by what it *introduces*, so a bundle that was "
        "already non-conforming can still be repaired through this API."
    ),
    401: describes(
        "No credentials, or credentials this platform does not recognise. "
        "Reads here need none; writes do."
    ),
    403: describes(
        "Authenticated, but not an owner of this scenario bundle. A bundle "
        "with no recorded owner is administrator-only."
    ),
    404: describes("No such scenario bundle, or no such resource within it."),
    409: describes(
        "The bundle moved between the read this write was prepared from and "
        "the write itself, so **nothing was written**. Read it again, apply "
        "the change to what comes back, and retry."
    ),
    412: describes(
        "`If-Match` named a version, and it is not the current one. Nothing "
        "was written. The response says which version the bundle is at."
    ),
    428: describes(
        "`If-Match` was absent, so this write did not say which version it was "
        "editing and nothing was written. The response names the current "
        "entity tag to send."
    ),
    429: describes(
        "Throttled. These endpoints are public to read, so they carry a "
        "ceiling for anonymous callers and a separate one per account. "
        "`Retry-After` says how long to wait."
    ),
    503: describes(
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


def paging(page_size, maximum):
    """`page` and `page_size`, as every collection in this API spells them.

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
                f"How many entries a page holds. Defaults to {page_size} and "
                f"is capped at {maximum}: this endpoint is public, and no "
                "public collection here has an unbounded mode."
            ),
        ),
    ]


def _responses(codes, success, extra):
    described = {code: REFUSALS[code] for code in codes}
    described.update(success)
    described.update(extra or {})
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
        responses=_responses(refusals, {200: success}, responses),
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


describes_a_removal = describes_a_guarded_write(
    # Written once and applied to every delete below a bundle, so the
    # description a client reads cannot drift from the one `removed` actually
    # implements.
    {
        200: describes(
            "Removed. The body names what was **deleted** and what was only "
            "**unlinked**, which no status code can say: a node another bundle "
            "still cites is kept and detached rather than destroyed. Only the "
            "downgraded nodes are listed -- the shared regions, authors and "
            "ontology terms every delete detaches are the rule, not the news."
        )
    },
)
