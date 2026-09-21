"""Replace a whole bundle in one call: the idempotent re-import.

The endpoint the whole API was built towards. A modelling pipeline declares
what its bundle should look like and the server makes it so -- adding what is
missing, changing what differs, and **removing what the declaration does not
mention**.

**It has a name of its own, and that is the safety property.** Full replacement
was rejected early as a verb on the bundle's own URL: in a graph an omitted key
is indistinguishable from a deleted one, and a `PUT` that anybody can reach by
habit turns every partial payload into a deletion. What was rejected was the
*accident-proneness*, not the semantics -- so the capability arrives as an
endpoint a client has to name and a precondition it has to satisfy, and the
ordinary paths stay safe. A test asserts the bundle's own URL still has no such
verb.

**Omission removes here and nowhere else in this API.** What that costs, and
where the boundary runs, is written down in `oekg.replacement`: removal goes
through the same typed containment walk a `DELETE` uses, so a node another
bundle cites is unlinked rather than destroyed, and the response says which
were which.

**One request to the store, and one entry in the history.** Never a delete
followed by a create: one request is one transaction, two would leave a window
in which the bundle does not exist, and the ledger would carry a deletion that
never happened. A replace that declares what is already there writes nothing at
all -- no triples, no version, no entry -- which is what makes the second run
of a pipeline free and its history honest.

**A pipeline holds no state between runs.** It finds its bundle with
`GET /api/v0/scenario-bundles/?acronym=...`, which answers with the identifier
and the version; if there is none it creates one; otherwise it replaces. That
is why the acronym's uniqueness is answered for here as well as on a create:
the endpoint that makes the promise is the one that has to keep it.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from functools import partial

from drf_spectacular.utils import OpenApiResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from oekg.acronyms import acronym_conflict, acronym_is_free, acronym_taken
from oekg.api_description import (
    BUNDLE_UID,
    EXPAND_LABELS,
    describes_a_guarded_write,
    json_body,
)
from oekg.api_support import OekgAPIView, shape_unavailable, store_unavailable
from oekg.bundle_bodies import bundle_response
from oekg.bundles import BUNDLE_FIELDS, BUNDLE_PARTS, bundle_referenced_iris
from oekg.dataset_links import UnaddressableTarget, link_address
from oekg.graph_store import GraphStoreError
from oekg.history import REPLACE
from oekg.labels import LABELS
from oekg.read_serializers import ScenarioBundleReplaceReadSerializer
from oekg.replacement import plan_replacement
from oekg.serializers import ScenarioBundleReplaceSerializer
from oekg.shape import ShapeUnavailable
from oekg.writes import open_bundle, refuse_renames


class ScenarioBundleReplaceAPIView(OekgAPIView):
    """`POST` declares what the whole bundle should be. Nothing else lives here."""

    permission_classes = [IsAuthenticated]
    offers_expansions = (LABELS,)

    @describes_a_guarded_write(
        {
            200: OpenApiResponse(
                response=ScenarioBundleReplaceReadSerializer,
                description=(
                    "The bundle is now what the payload declared. The body is "
                    "that bundle, in the form a write accepts it back, and "
                    "`_meta.deleted` and `_meta.unlinked` say what the "
                    "declaration removed -- a node another bundle still cites "
                    "is detached rather than destroyed, which no status code "
                    "can say. `ETag` is the new version, so a pipeline chains "
                    "its next write without reading again. A replace that "
                    "declared what was already there writes nothing: the "
                    "version is unchanged, both lists are empty, and the "
                    "history records nothing."
                ),
            )
        },
        request=ScenarioBundleReplaceSerializer,
        parameters=[BUNDLE_UID, EXPAND_LABELS],
        responses={
            400: json_body(
                "Refused, and **nothing was written**. Besides the usual "
                "payload problems: the declaration named a nested scenario, "
                "study report or dataset link that is not in this bundle -- "
                "identifiers are matched, never created from -- or declared "
                "the same one twice. A replace is also judged by what it "
                "*introduces*, so dropping a field the bundle needed is "
                "refused while a violation it already carried is not blamed "
                "on this caller."
            ),
            409: json_body(
                "Either the bundle moved between the read this replace was "
                "prepared from and the write itself, another bundle holds the "
                "acronym declared, or something outside this bundle started "
                "citing a node the replace was about to remove. Nothing was "
                "written. Read it again, apply the declaration to what comes "
                "back, and retry."
            ),
        },
    )
    def post(self, request, uid):
        """Make this bundle be exactly what the payload declares.

        **This is the only endpoint in the API where leaving something out
        removes it.** Everywhere else a key a payload does not name is
        genuinely untouched; here the payload is the whole bundle, so a field
        it omits is emptied and a scenario, study report or dataset link it
        does not list is removed. What "removed" means is the same typed
        containment walk a `DELETE` uses: a node another bundle still cites is
        unlinked instead, and the answer names both sets.

        **A nested resource keeps its identity when it names one.** Send back
        the `_meta.uid` a read gave it and the existing scenario, report or
        link is updated in place; send none and a new one is created. This is
        the single place a client's `_meta` is read rather than ignored, and it
        is what the container was built for -- without it a re-import would
        delete and recreate every part of the bundle on every run, churning
        identifiers and filling the history with deletions nobody asked for.

        **Running it twice is free.** The second call finds nothing to change,
        writes nothing, leaves the version where it is and records no history
        entry -- so a pipeline that runs nightly does not accumulate a ledger
        of changes it never made.

        Anything in the bundle this API has no vocabulary for -- a predicate no
        field table names, a shared contact's own triples -- is left alone. A
        declaration in this API's vocabulary is a declaration about this API's
        vocabulary, and silence about something a client cannot send is not
        permission to delete it.
        """
        serializer = ScenarioBundleReplaceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        try:
            write = open_bundle(request, uid)
            write.require_write(request)

            # The acronym is how a stateless pipeline finds this bundle again,
            # so the endpoint that promises the lookup answers for its
            # uniqueness. Asked here for a message that names the acronym, and
            # bound into the write below for the answer that cannot be
            # overtaken. A bundle never counts against itself, so declaring the
            # acronym it already has is not refused by its own value.
            acronym = payload["acronym"]
            if acronym_taken(write.store, acronym, uid):
                return acronym_conflict(acronym)

            known_labels = write.labels_of(bundle_referenced_iris(payload))
            refuse_renames(payload, known_labels, BUNDLE_FIELDS)
            for part in BUNDLE_PARTS:
                for nested in payload.get(part.payload_key) or []:
                    refuse_renames(nested, known_labels, part.fields)

            replacement = plan_replacement(
                write.store,
                write.pre_state,
                uid,
                payload,
                known_labels,
                address=partial(link_address, request),
            )
            if replacement.changes_nothing:
                # Nothing to write, so nothing is written -- not an empty
                # update that bumps the version and records a change nobody
                # made. The answer is still the whole bundle and its unchanged
                # entity tag, which is what the next call needs.
                return bundle_response(
                    uid,
                    write.pre_state,
                    write.version,
                    expand=self.expand,
                    meta=replacement.as_meta(),
                )

            write.apply(
                removed=replacement.removed,
                added=replacement.added,
                verb=REPLACE,
                # Two conditions in one guard: the nodes this write is about to
                # remove are still unreferenced, and the acronym is still
                # free. With the version that makes three, so a `409` names
                # none of them -- and the advice is the same for all three.
                guard=" ".join(
                    clause
                    for clause in (replacement.guard, acronym_is_free(acronym, uid))
                    if clause
                ),
            )
        except UnaddressableTarget as error:
            return Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)
        except ShapeUnavailable as error:
            return shape_unavailable(error)
        except GraphStoreError as error:
            return store_unavailable(error, "written to")

        # `write.gaps` rather than the `history_recorded` argument: it reports
        # whatever was lost after the graph committed, so a gap a later slice
        # teaches `BundleWrite` to notice arrives here without this line
        # changing. Nothing is folded in on the branch above, because nothing
        # was written there and no gap can exist.
        return bundle_response(
            uid,
            write.post_state,
            write.version,
            expand=self.expand,
            meta={**replacement.as_meta(), **write.gaps},
        )
