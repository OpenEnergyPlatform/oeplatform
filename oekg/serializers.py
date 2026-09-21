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

from urllib.parse import urlsplit

from rest_framework import serializers

from oekg.bundles import BUNDLE_FIELDS, SCENARIO_FIELDS, STUDY_REPORT_FIELDS
from oekg.dataset_links import (
    DIRECTIONS,
    EXTERNAL,
    REFERENCE_KINDS,
    reference_kind,
)
from oekg.fields import ENUM
from oekg.shape import constraint_message, enumeration

# Everything read-only lives under one key, and writes ignore it. That is what
# lets a client send back what it read without stripping anything -- and it
# keeps the closed check structural instead of an exception list that grows.
READ_ONLY_CONTAINER = "_meta"


def _is_address(value: str) -> bool:
    """Whether this is a URL at all -- a scheme and a host, and nothing more.

    Deliberately weaker than Django's URL validator, which is the point: see
    the note on `DatasetLinkSerializer.url`.
    """
    parts = urlsplit(value)
    return bool(parts.scheme and parts.netloc)


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


class DatasetLinkSerializer(ClosedSerializer):
    """A scenario's link to data: what it is, what it points at, and where.

    Not a field table, because a dataset link has no fields of its own: the
    label, the address and the identifier the shape requires all follow from
    these keys. That is also why there is no partial form of this serializer --
    a link is added or removed, never edited.

    **`ref` and `url` are two ways of saying the same thing, and they are
    checked against each other.** A client naming a platform target sends
    `ref` and `name` and lets the router derive the address; a client sending
    back a link it read sends the address it read, and then `ref` has to be the
    kind that address actually is. Anything else would let a payload claim one
    target and cite another -- and since `ref` is not stored, the claim would
    be the half that vanished.
    """

    # "input" or "output": which way the data flowed.
    type = serializers.ChoiceField(choices=[d.name for d in DIRECTIONS])
    # "table", "dataset" or "external". The first two are not equivalent -- a
    # table reference is reproducible, a dataset reference stays current as its
    # membership changes -- and choosing between them is the client's call.
    # "external" is an address this platform has no route for, which exists so
    # that a bundle holding one can be sent back whole. Null is a link that
    # stores no address at all, which the shape permits.
    ref = serializers.ChoiceField(choices=list(REFERENCE_KINDS), allow_null=True)
    # The name of that table or dataset on this platform, or -- for an external
    # link -- whatever the citation is called. Stored as the label the shape
    # requires. Not checked against the platform: a link may outlive what it
    # points at, and a read says whether it still resolves.
    name = serializers.CharField()
    # Where it points, as stored. Optional on a write that names a platform
    # target, because the router derives it; required for an external link,
    # which has nothing else to go on.
    #
    # A CharField and not a URLField, checked below instead: the addresses this
    # API mints are absolute and built from the host the request arrived on,
    # and Django's URL validator refuses an authority with no dot in it -- a
    # deployment's internal name, `testserver` in this suite. A read has to be
    # sendable back, so the field accepts what a read emits and asks only for
    # what an address actually needs.
    url = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate(self, attrs):
        ref, url = attrs.get("ref"), attrs.get("url") or None
        attrs["url"] = url
        if url is not None and not _is_address(url):
            raise serializers.ValidationError(
                {
                    "url": (
                        f"{url!r} is not an address: a dataset link stores "
                        "where it points, so this needs a scheme and a host."
                    )
                }
            )
        if url is None:
            if ref == EXTERNAL:
                raise serializers.ValidationError(
                    {
                        "url": (
                            "An external link is its address: there is nothing "
                            "else to point at. Send the url, or name a target "
                            "on this platform with ref 'table' or 'dataset'."
                        )
                    }
                )
            return attrs
        actual = reference_kind(url) or EXTERNAL
        if ref != actual:
            raise serializers.ValidationError(
                {
                    "ref": (
                        f"{url!r} is {'an' if actual == EXTERNAL else 'a'} "
                        f"{actual} address, and this payload calls it "
                        f"{ref!r}. The address is what gets stored, so a "
                        "disagreement here would be a claim that vanished."
                    )
                }
            )
        return attrs


class NestedScenarioSerializer(ScenarioSerializer):
    """A scenario as it appears *inside* a bundle payload, links and all.

    The links nest here and not on the bundle because that is where the shape
    hangs them, and they nest at all because of what `replace` does: anything
    in the graph and absent from its payload is removed, so a link a payload
    has no way to mention is a link a re-import destroys. A bundle read nests
    them for the same reason from the other side -- a client sends back what it
    read, without stripping and without losing its citations.

    A scenario's **own** endpoints use the plain serializer above and refuse
    this key: a link has its own URL there, and add-and-remove is its whole
    contract.
    """

    datasets = DatasetLinkSerializer(many=True, required=False)


class ScenarioBundleCreateSerializer(ScenarioBundleSerializer):
    """The bundle field set **plus** its nested sub-resources, for `POST` only.

    The asymmetry is the whole point and it is structural rather than a flag: a
    bundle `POST` builds its scenarios and study reports with it, and a bundle
    `PATCH` uses the class above, which has no such key and therefore refuses
    one. That is what lets a pipeline create a whole bundle in one call without
    giving any call the power to drop its parts by omitting them.

    Dataset links nest one level deeper, inside each scenario, because that is
    where the shape hangs them -- see `NestedScenarioSerializer`.
    """

    scenarios = NestedScenarioSerializer(many=True, required=False)
    study_reports = StudyReportSerializer(many=True, required=False)


#: Where a matched sub-resource's identifier lands in validated data. Not a
#: field name -- no field starts with an underscore -- so it cannot collide
#: with the closed field set it travels beside.
IDENTIFIED_BY = "_uid"


class IdentifiedMixin:
    """Reads the identifier out of `_meta`, for the one write that needs it.

    **This is the single place in the API where a client's own `_meta` is not
    ignored, and it is not an inconsistency -- it is what the container was
    built for.** A read puts everything a client cannot write under `_meta` so
    that a client can send back what it read without stripping anything; the
    replace endpoint is the endpoint that exists to be sent a whole read back.
    Its payload declares the bundle's parts, and a part it does not recognise
    is a part it creates, so a read that lost its identifiers would delete and
    recreate every scenario on every run -- churning identifiers and filling
    the history with deletions nobody asked for.

    Only `uid` is read, and only on a sub-resource. The bundle's identity is
    the URL, and everything else in `_meta` is derived from the graph.
    """

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        if isinstance(data, dict):
            meta = data.get(READ_ONLY_CONTAINER)
            uid = meta.get("uid") if isinstance(meta, dict) else None
            if uid is not None:
                value[IDENTIFIED_BY] = str(uid)
        return value


class IdentifiedDatasetLinkSerializer(IdentifiedMixin, DatasetLinkSerializer):
    """A dataset link that may name the one it already is."""


class IdentifiedScenarioSerializer(IdentifiedMixin, NestedScenarioSerializer):
    """A scenario that may name the one it already is, links and all."""

    datasets = IdentifiedDatasetLinkSerializer(many=True, required=False)


class IdentifiedStudyReportSerializer(IdentifiedMixin, StudyReportSerializer):
    """A study report that may name the one it already is."""


class ScenarioBundleReplaceSerializer(ScenarioBundleCreateSerializer):
    """The whole desired bundle: the create's payload, with identities kept.

    Same shape as a create -- deliberately, because the point of the endpoint
    is that a pipeline declares one bundle and the server makes it so, whether
    or not the bundle is there yet. What it adds is that every nested part may
    say which existing part it is, in the `_meta.uid` a read gave it.
    """

    scenarios = IdentifiedScenarioSerializer(many=True, required=False)
    study_reports = IdentifiedStudyReportSerializer(many=True, required=False)
