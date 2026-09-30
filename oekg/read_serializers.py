"""What a read answers with: the writable payload, and `_meta` beside it.

These exist to be *described*, never to validate: nothing in the write path
calls them, and a response is assembled from the graph rather than passed
through one. That makes them a claim, and a claim about a response can rot in
exactly the way the drift guard cannot see -- so `oekg/tests/test_response_schema.py`
takes a real response from every endpoint and validates it against the schema
these generate. A body that stops matching fails there, not in a reader's
client.

Three rules decide their shape, and all three come from WF-12:

- **A read returns exactly what a write accepts, plus `_meta`.** So each of
  these subclasses the serializer that validates the write and adds one key.
  Written as a subclass rather than as a parallel field list, because a
  parallel list is a second place for the bundle's fields to be stated and the
  two would agree only until somebody added a field.
- **Everything read-only is under `_meta`.** That is what keeps the payload's
  top level mapping one-to-one onto the closed shape, and what lets a client
  send back what it read without stripping anything.
- **`_meta` is open at the bottom.** These serializers declare the keys that
  are always there and mark as optional the ones that appear on request
  (`labels`) or on trouble (`history_recorded`, `ownership_recorded`, which are
  written only when something was lost after the graph had already committed).
  OpenAPI objects permit properties a schema does not name, which is what makes
  "declared, not exhaustive" expressible at all -- and which is why the test
  beside these validates rather than compares.

The nested sub-resources of a bundle read use the *read* serializers, not the
write ones: a nested scenario carries its own `_meta`, and a schema saying
otherwise would describe a body nobody receives.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from rest_framework import serializers

from oekg.serializers import (
    DatasetLinkSerializer,
    NestedScenarioSerializer,
    ScenarioBundleCreateSerializer,
    ScenarioSerializer,
    StudyReportSerializer,
)


class GapsMixin(serializers.Serializer):
    """The two keys that appear only when something was lost after the commit.

    The graph and the relational database cannot share a transaction, and the
    graph commits first. A history entry or an ownership row that could not be
    written afterwards is named beside the success it qualifies rather than
    turned into an error for a write that did happen -- so these are absent on
    an ordinary response and `false` when they are there. Never `true`: a
    client should not have to check something on every response to learn that
    the ordinary thing happened.
    """

    history_recorded = serializers.BooleanField(required=False)
    ownership_recorded = serializers.BooleanField(required=False)
    ownership_forgotten = serializers.BooleanField(required=False)


class LabelsMixin(serializers.Serializer):
    """`labels` is here only when `?expand=labels` asked for it.

    Every term asked about is a key, and a term the label subset has no label
    for maps to `null` -- so a client never has to tell "no label for this
    term" from "labels were not resolved".
    """

    labels = serializers.DictField(
        child=serializers.CharField(allow_null=True), required=False
    )


class ResourceReferenceSerializer(serializers.Serializer):
    """Which resource a line is about: its OEO class and its identifier.

    Both nullable, and for one reason: a row written before sub-resources
    existed names neither, and is read as a bundle write.
    """

    type = serializers.URLField(allow_null=True)
    uid = serializers.CharField(allow_null=True)


class BundleMetaSerializer(GapsMixin, LabelsMixin):
    uid = serializers.CharField()
    iri = serializers.URLField()
    version = serializers.IntegerField()


class SubResourceMetaSerializer(GapsMixin, LabelsMixin):
    uid = serializers.CharField()
    iri = serializers.URLField()
    type = serializers.URLField(help_text="The OEO class of this resource.")
    bundle = serializers.CharField()


class TableEntrySerializer(serializers.Serializer):
    """One table a dataset link resolves to, as it stands today."""

    name = serializers.CharField()
    peer_review = serializers.ChoiceField(
        choices=["finished", "in_progress"],
        allow_null=True,
        help_text=(
            "Three-valued, and `null` rather than `false` where there is no "
            "review: the peer review process postdates most of the data on "
            "this platform, so a boolean would read as a quality judgement on "
            "links that predate it. A table with several reviews reads "
            "`finished` if any of them finished."
        ),
    )


class DatasetLinkMetaSerializer(SubResourceMetaSerializer):
    target_iri = serializers.URLField(
        allow_null=True,
        help_text=(
            "The address actually stored. It is the only thing that stays true "
            "when `ref` reads `null`, which happens for a link written before "
            "this API existed that points somewhere this platform has no route "
            "for."
        ),
    )
    scenario = serializers.CharField()
    resolvable = serializers.BooleanField(
        allow_null=True,
        help_text=(
            "Whether the named target is still on this platform. `null` -- "
            "never `false` -- when the stored address is not a page here, "
            "because `false` would claim the target had been deleted."
        ),
    )
    tables = TableEntrySerializer(
        many=True,
        allow_null=True,
        help_text=(
            "What the citation means today: the one table for `ref: table`, "
            "the catalogue entry's current members for `ref: dataset`, `[]` "
            "when the named target is gone, and `null` when this server cannot "
            "say."
        ),
    )


class ScenarioReadSerializer(ScenarioSerializer):
    """A scenario at its own endpoints, where a dataset link has its own URL."""

    _meta = SubResourceMetaSerializer()


class StudyReportReadSerializer(StudyReportSerializer):
    _meta = SubResourceMetaSerializer()


class DatasetLinkReadSerializer(DatasetLinkSerializer):
    _meta = DatasetLinkMetaSerializer()


class NestedScenarioReadSerializer(NestedScenarioSerializer):
    """A scenario *inside* a bundle body: the same, plus what it cites.

    Two read shapes for one resource, because there are two write shapes: a
    scenario's own endpoints take no dataset links, and a bundle payload takes
    them nested. The read that a client sends back to `replace` has to be the
    second one, or the citations it does not mention are the citations it
    loses.
    """

    _meta = SubResourceMetaSerializer()
    datasets = DatasetLinkReadSerializer(many=True)


class ScenarioBundleReadSerializer(ScenarioBundleCreateSerializer):
    """The bundle, its parts nested, exactly as a `POST` would take it back."""

    _meta = BundleMetaSerializer()
    scenarios = NestedScenarioReadSerializer(many=True)
    study_reports = StudyReportReadSerializer(many=True)


class RemovedNodeSerializer(serializers.Serializer):
    """A node as a delete reports it back: an address and a class."""

    iri = serializers.URLField()
    type = serializers.URLField(
        allow_null=True,
        help_text=(
            "`null` for a node whose class this API does not recognise, which "
            "a response listing a bare address would not have said."
        ),
    )


class BundleReplaceMetaSerializer(BundleMetaSerializer):
    """The bundle's own `_meta`, plus the account of what the replace removed.

    In `_meta` and not beside the fields, for the reason every read-only value
    here is: the top level of a bundle body is exactly what a write accepts, and
    a client that read a replace's answer can send it straight back.
    """

    deleted = RemovedNodeSerializer(many=True)
    unlinked = RemovedNodeSerializer(many=True)


class ScenarioBundleReplaceReadSerializer(ScenarioBundleReadSerializer):
    """What a replace answers with: the bundle it made, and what it took out."""

    _meta = BundleReplaceMetaSerializer()


class SummaryCountsSerializer(serializers.Serializer):
    scenarios = serializers.IntegerField()
    study_reports = serializers.IntegerField()


class SummaryMetaSerializer(serializers.Serializer):
    uid = serializers.CharField()
    iri = serializers.URLField()
    version = serializers.IntegerField()
    counts = SummaryCountsSerializer()


class ScenarioBundleSummarySerializer(serializers.Serializer):
    """Enough to find a bundle and decide which one, and nothing else.

    Not a bundle with fields left out: the two a human recognises a bundle by
    stay at the top level, where a bundle read has them too, and everything a
    client cannot write is in `_meta`. The version is there because it is what
    a pipeline's next write must send.
    """

    label = serializers.CharField(allow_null=True)
    acronym = serializers.CharField(allow_null=True)
    _meta = SummaryMetaSerializer()


class HistoryChangeSerializer(serializers.Serializer):
    """One field's worth of a write, rendered at read time from the triples."""

    field = serializers.CharField(
        allow_null=True,
        help_text=(
            "`null` for a triple this cannot attribute to a field -- the type "
            "and label a minted contact brings with it, say. Reported rather "
            "than dropped, because dropping it would make the summary look "
            "complete when it is not."
        ),
    )
    predicate = serializers.URLField()
    removed = serializers.ListField(child=serializers.CharField())
    added = serializers.ListField(child=serializers.CharField())


class BundleHistoryEntrySerializer(serializers.Serializer):
    era = serializers.CharField(
        help_text=(
            "Which generation of row this is. Entries written before this API "
            "existed record no verb and no field-level summary."
        )
    )
    verb = serializers.CharField(allow_null=True)
    actor = serializers.CharField(
        allow_null=True, help_text="A username, not an internal identifier."
    )
    timestamp = serializers.DateTimeField()
    resource = ResourceReferenceSerializer(
        help_text="The class and identifier the write was about."
    )
    acronym = serializers.CharField(
        allow_null=True,
        help_text=(
            "Set on a whole-bundle delete and nowhere else: after that write "
            "there is no bundle left to read an acronym off, so the line "
            "carries it."
        ),
    )
    version_before = serializers.IntegerField(allow_null=True)
    version_after = serializers.IntegerField(allow_null=True)
    changes = HistoryChangeSerializer(
        many=True,
        allow_null=True,
        help_text=(
            "`null` rather than `[]` where there cannot be a summary -- an "
            "empty list would say that nothing changed, and what is known is "
            "that nothing recorded *what* changed."
        ),
    )
    triples = serializers.DictField(required=False)


class RemovalMetaSerializer(GapsMixin):
    bundle = serializers.CharField()
    resource = ResourceReferenceSerializer()
    # Only a dataset link is addressed below a scenario, so only its removal
    # names one.
    scenario = serializers.CharField(required=False)


class RemovalSerializer(serializers.Serializer):
    """What a delete came to: two lists, because one status code cannot say.

    `unlinked` holds only the nodes the typed containment walk **downgraded** --
    ones something outside this bundle still cites, so they were detached
    rather than destroyed. The shared regions, authors and ontology terms every
    delete detaches are the rule that always applies, and listing them would
    bury the line that is news.
    """

    deleted = RemovedNodeSerializer(many=True)
    unlinked = RemovedNodeSerializer(many=True)
    _meta = RemovalMetaSerializer()


class BundleRemovalMetaSerializer(GapsMixin):
    uid = serializers.CharField()
    iri = serializers.URLField()
    acronym = serializers.CharField(allow_null=True)
    version_before = serializers.IntegerField()


class BundleRemovalSerializer(serializers.Serializer):
    deleted = RemovedNodeSerializer(many=True)
    unlinked = RemovedNodeSerializer(many=True)
    _meta = BundleRemovalMetaSerializer()
