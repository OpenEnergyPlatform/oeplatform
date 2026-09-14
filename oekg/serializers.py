"""Serializers for the OEKG scenario-bundle API.

Hand-written, not generated. A serializer layer can express only about 61% of
the shape -- class constraints, disjunctions and every target-by-predicate rule
need the graph -- so these carry the *structure* and the shape on the graph
carries the *constraints*. A conformance test asserts the two stay aligned.

Two behaviours are made explicit because the framework's defaults are wrong for
a closed shape:

- **An unknown key is a rejection.** The framework silently drops keys it does
  not recognise, which would let a client believe it had sent something it had
  not.
- **No identifier is accepted.** The server mints it. ``uid`` is not an
  ignored key here, it is a rejected one, so a client that tries to choose is
  told rather than quietly overridden.

Enumerated picks are checked against the shape's own ``sh:in`` lists, read from
the artifact at runtime, and a rejection quotes the shape's own message. Nothing
is copied into Python: the lists are still moving in the shape's repository.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from rest_framework import serializers

from oekg.bundles import BUNDLE_FIELDS, SCENARIO_FIELDS, STUDY_REPORT_FIELDS
from oekg.dataset_links import DIRECTIONS, TARGETS
from oekg.fields import ENUM
from oekg.shape import constraint_message, enumeration

# Everything read-only lives under one key, and writes ignore it. That is what
# lets a client send back what it read without stripping anything -- and it
# keeps the closed check structural instead of an exception list that grows.
READ_ONLY_CONTAINER = "_meta"


class ClosedSerializer(serializers.Serializer):
    """A serializer that refuses what it does not recognise."""

    def to_internal_value(self, data):
        if not isinstance(data, dict):
            raise serializers.ValidationError(
                {"detail": "Expected an object describing the resource."}
            )
        data = {key: value for key, value in data.items() if key != READ_ONLY_CONTAINER}
        unknown = sorted(set(data) - set(self.fields))
        if unknown:
            raise serializers.ValidationError(
                {name: "Unknown field. The bundle shape is closed." for name in unknown}
            )
        return super().to_internal_value(data)


class NodeReferenceSerializer(ClosedSerializer):
    """A contact, organisation or funder: referenced by IRI, or minted here."""

    iri = serializers.CharField(required=False, allow_blank=False, allow_null=True)
    label = serializers.CharField()


class PartSerializer(ClosedSerializer):
    """A framework or model factsheet: bundle-local, with a link out."""

    label = serializers.CharField()
    # has-iri is a string on these nodes per the shape -- it points at a
    # factsheet page and is not the node's identity. Nullable because a read of
    # a framework without one returns null, and a read must be sendable back.
    iri = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class EnumeratedListField(serializers.ListField):
    """A list of IRIs the shape's sh:in list for this property allows."""

    child = serializers.CharField()

    def __init__(self, property_iri, **kwargs):
        self.property_iri = str(property_iri)
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        values = super().to_internal_value(data)
        allowed = enumeration(self.property_iri)
        if not allowed:
            return values
        unknown = [value for value in values if value not in allowed]
        if unknown:
            message = constraint_message(self.property_iri)
            raise serializers.ValidationError(
                [
                    f"{value} is not one of the {len(allowed)} values the shape "
                    f"allows here." + (f" {message}" if message else "")
                    for value in unknown
                ]
            )
        return values


class EnumeratedFieldsMixin:
    """Declares the enumerated fields from the same table that builds triples.

    Read from the shape at runtime rather than copied into Python: the lists
    are still moving in the shape's repository, and a rejection quotes the
    shape's own message rather than a second wording that could disagree.
    """

    field_table = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.field_table:
            if field.kind == ENUM:
                self.fields[field.name] = EnumeratedListField(
                    field.predicate, required=False
                )


class ScenarioSerializer(EnumeratedFieldsMixin, ClosedSerializer):
    """One scenario factsheet -- a sub-resource, not a field of its bundle.

    What makes it one is the shape: it carries its own has-uuid. That uuid is
    **not** a field here, because the server mints it; a client supplies no
    identifier anywhere in this API.
    """

    field_table = SCENARIO_FIELDS

    label = serializers.CharField()
    acronym = serializers.CharField()
    abstract = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    study_regions = NodeReferenceSerializer(many=True, required=False)
    interacting_regions = NodeReferenceSerializer(many=True, required=False)
    # The shape types these as xsd:dateTime, so they are parsed rather than
    # passed through: a value that is not a date is this layer's to refuse, not
    # the store's.
    years = serializers.ListField(child=serializers.DateTimeField(), required=False)


class ScenarioBundleSerializer(EnumeratedFieldsMixin, ClosedSerializer):
    """The closed bundle field set -- these and nothing else."""

    label = serializers.CharField()
    # The trim is stated rather than inherited, because uniqueness depends on
    # it: the value the uniqueness check compares and the value the write
    # stores are this one, so normalising here normalises both at once. The
    # user interface's check normalises one side only, which is exactly why it
    # misses duplicates.
    acronym = serializers.CharField(trim_whitespace=True)
    # Nullable for the same reason: an absent abstract reads as null, and the
    # round trip a client (and, later, replace) depends on has to survive it.
    abstract = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    contacts = NodeReferenceSerializer(many=True, required=False)
    organisations = NodeReferenceSerializer(many=True, required=False)
    funders = NodeReferenceSerializer(many=True, required=False)
    frameworks = PartSerializer(many=True, required=False)
    models = PartSerializer(many=True, required=False)

    field_table = BUNDLE_FIELDS


class StudyReportSerializer(EnumeratedFieldsMixin, ClosedSerializer):
    """One study report -- the publication a bundle is written up in.

    A sub-resource for the same reason a scenario is: the shape gives it its
    own has-uuid, which the server mints, so it is not a field here.

    What the shape requires of one, and therefore what is required here: a
    label, at least one author, and exactly one publication date. The doi and
    the reference are optional, and the reference is singular because the shape
    allows at most one.
    """

    field_table = STUDY_REPORT_FIELDS

    label = serializers.CharField()
    doi = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    # The shape types this as xsd:dateTime, so it is parsed rather than passed
    # through: a value that is not a date is this layer's to refuse.
    publication_date = serializers.DateTimeField()
    authors = NodeReferenceSerializer(many=True)
    # A URL, and the node's IRI rather than a literal on it: the thing this
    # points at is the cited document. Not a NodeReferenceSerializer, because
    # there is no label to send and no node to mint.
    reference = serializers.URLField(required=False, allow_blank=True, allow_null=True)


class ScenarioBundleCreateSerializer(ScenarioBundleSerializer):
    """The bundle field set **plus** its nested sub-resources, for `POST` only.

    The asymmetry is the whole point and it is structural rather than a flag: a
    bundle `POST` builds its scenarios and study reports with it, and a bundle
    `PATCH` uses the class above, which has no such key and therefore refuses
    one. That is what lets a pipeline create a whole bundle in one call without
    giving any call the power to drop its parts by omitting them.

    Dataset links are deliberately **not** here. They hang off a scenario
    rather than off the bundle, and they are add-and-remove only, so there is
    no partial update of one to reason about -- nesting them would make a
    create the one place their fields could be written together.
    """

    scenarios = ScenarioSerializer(many=True, required=False)
    study_reports = StudyReportSerializer(many=True, required=False)


class DatasetLinkSerializer(ClosedSerializer):
    """A scenario's link to data on this platform: three keys, all required.

    Not a field table, because a dataset link has no fields of its own: the
    label, the URL and the identifier the shape requires are all derived from
    these three. That is also why there is no partial form of this serializer --
    a link is added or removed, never edited.
    """

    # "input" or "output": which way the data flowed.
    type = serializers.ChoiceField(choices=[d.name for d in DIRECTIONS])
    # "table" or "dataset": whether this points at one OEP Table or at an OEP
    # Dataset catalogue entry. The two are not equivalent -- a table reference
    # is reproducible, a dataset reference stays current as its membership
    # changes -- and choosing between them is the client's call.
    ref = serializers.ChoiceField(choices=[t.name for t in TARGETS])
    # The name of that table or dataset on this platform. Not checked against
    # the platform: a link may outlive what it points at, and a read says
    # whether it still resolves.
    name = serializers.CharField()
