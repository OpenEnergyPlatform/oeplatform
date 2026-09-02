"""A seeded Model/Framework Factsheet corpus for the app's tests.

Not a test module (the runner collects `test*.py`), and deliberately not the
benchmark harness in `benchmarks/model_factsheets/`: that one seeds
production's *measured shape* -- 305 factsheets, 817 tags, 12,156 tag edges --
to answer "what is the curve", and is far too slow and too prod-calibrated to
run on every push. This factory seeds the same *kinds* of rows, small enough
for CI, so the read-path bounds can be asserted there. Nothing here imports
from `benchmarks`.

Three traps this encodes, all of them load-bearing:

* `Tag`'s primary key is `name_normalized`, a `CharField` -- not an integer --
  and `color_hex` is a read-only property over the `color` integer.
* `Energymodel` and `Energyframework` are multi-table inheritance over the
  concrete `BasicFactsheet`, so Django refuses `bulk_create` for them and the
  tag through-table's foreign key is named for the **parent**, not for the
  class being seeded.
* A "corrupted" factsheet carries a snapshot of the whole tag table at the
  moment it was saved, which is why the tag vocabulary has to be larger than
  the detection threshold for a corpus to be able to express corruption.

SPDX-FileCopyrightText: none
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import random
from dataclasses import dataclass, field
from typing import Any

from django.db import transaction
from django.utils import timezone

from dataedit.models import Tag
from modelview.helper import getClasses

#: Production's detection rule for a factsheet corrupted by the tag editor
#: (WF-03's census: the distribution is bimodal with a factor-6.6 gap --
#: healthy factsheets top out at 106 tags, corrupted ones start at 696, so any
#: threshold between 110 and 690 selects the same 23).
CORRUPT_THRESHOLD = 200

#: Larger than CORRUPT_THRESHOLD on purpose: a corrupted factsheet attaches the
#: whole vocabulary, so a smaller one could not produce a detectable corruption.
DEFAULT_TAGS = 260

#: Production carries ~897 legitimate tag attachments over 284 clean model
#: factsheets, i.e. about three each.
DEFAULT_HEALTHY_TAGS = 3

DEFAULT_SEED = 20260902


@dataclass
class Corpus:
    """What `seed_corpus` created, for a test to assert against."""

    sheettype: str
    factsheets: list[Any] = field(default_factory=list)
    tags: list[Tag] = field(default_factory=list)
    corrupted: list[Any] = field(default_factory=list)
    healthy: list[Any] = field(default_factory=list)
    #: Total factsheet->tag edges. This -- not the number of factsheets -- is
    #: what the list page's cost is super-linear in.
    edges: int = 0


def seed_tags(count: int = DEFAULT_TAGS) -> list[Tag]:
    """Create `count` tags, idempotently.

    Tags are shared platform-wide between Tables and Factsheets, so seeding a
    model corpus and a framework corpus in the same test must reuse the same
    vocabulary rather than collide on the primary key.
    """
    names = ["testtag-%04d" % i for i in range(count)]
    existing = set(Tag.objects.filter(pk__in=names).values_list("pk", flat=True))

    rng = random.Random(DEFAULT_SEED)
    Tag.objects.bulk_create(
        [
            Tag(
                name_normalized=name,
                name="test tag %04d" % i,
                color=rng.randrange(0xFFFFFF),
            )
            for i, name in enumerate(names)
            if name not in existing
        ]
    )
    return list(Tag.objects.filter(pk__in=names).order_by("pk"))


def seed_corpus(
    sheettype: str = "model",
    factsheets: int = 25,
    tags: int = DEFAULT_TAGS,
    corrupted: int = 2,
    healthy_tags: int = DEFAULT_HEALTHY_TAGS,
    seed: int = DEFAULT_SEED,
) -> Corpus:
    """Seed `factsheets` factsheets of `sheettype` over a `tags`-tag vocabulary.

    The first `corrupted` of them carry the whole vocabulary -- the damage the
    tag editor does today -- and the rest carry `healthy_tags` each.
    """
    cls, _ = getClasses(sheettype)
    if cls is None:
        raise ValueError("unknown sheettype: %r" % (sheettype,))
    if corrupted > factsheets:
        raise ValueError("cannot corrupt %d of %d factsheets" % (corrupted, factsheets))
    if corrupted and tags <= CORRUPT_THRESHOLD:
        raise ValueError(
            "a corrupted factsheet needs a vocabulary larger than the %d-tag "
            "detection threshold; got %d" % (CORRUPT_THRESHOLD, tags)
        )

    vocabulary = seed_tags(tags)
    corpus = Corpus(sheettype=sheettype, tags=vocabulary)

    # Multi-table inheritance: every row is two INSERTs and bulk_create is
    # refused, so one transaction keeps the seed cheap anyway.
    with transaction.atomic():
        for i in range(factsheets):
            values = {
                "model_name": "Test %s %04d" % (sheettype, i),
                "acronym": "T%04d" % i,
                "contact_email": ["test-%04d@example.org" % i],
            }
            values.update(_mandatory_values(cls, skip=values))
            corpus.factsheets.append(cls.objects.create(**values))

    corpus.corrupted = corpus.factsheets[:corrupted]
    corpus.healthy = corpus.factsheets[corrupted:]

    rng = random.Random(seed)
    through = cls.tags.through
    sheet_fk, tag_fk = _through_field_names(through)

    edges = []
    for sheet in corpus.corrupted:
        for tag in vocabulary:
            edges.append(through(**{sheet_fk: sheet.pk, tag_fk: tag.pk}))
    for sheet in corpus.healthy:
        for tag in rng.sample(vocabulary, min(healthy_tags, len(vocabulary))):
            edges.append(through(**{sheet_fk: sheet.pk, tag_fk: tag.pk}))

    through.objects.bulk_create(edges, batch_size=5000)
    corpus.edges = len(edges)
    return corpus


def _mandatory_values(cls, skip: dict) -> dict:
    """Empty-but-valid values for every NOT NULL field with no default.

    Derived rather than listed, so that adding another such field to a
    factsheet does not silently break every test in this app. Today there are
    three: `model_name`, `contact_email` and -- on frameworks only --
    `data_api`, a boolean that is NOT NULL and carries no default.
    """
    values = {}
    for f in cls._meta.get_fields():
        if not getattr(f, "concrete", False) or f.many_to_many:
            continue
        if f.primary_key or getattr(f, "auto_created", False):
            continue
        if f.null or f.has_default() or f.name in skip:
            continue
        values[f.name] = _empty_value(f)
    return values


_SCALAR_EMPTIES = {
    "BooleanField": False,
    "IntegerField": 0,
    "BigIntegerField": 0,
    "SmallIntegerField": 0,
    "FloatField": 0.0,
    "DecimalField": 0,
    "CharField": "",
    "TextField": "",
    "EmailField": "",
    "URLField": "",
}


def _empty_value(f):
    if hasattr(f, "base_field"):  # ArrayField
        return []
    internal = f.get_internal_type()
    if internal in _SCALAR_EMPTIES:
        return _SCALAR_EMPTIES[internal]
    if internal in ("DateField", "DateTimeField"):
        return timezone.now()
    return ""


def _through_field_names(through) -> tuple[str, str]:
    """The through model's two foreign keys, as (factsheet side, tag side).

    Derived rather than hardcoded: `tags` is declared on `BasicFactsheet`, so
    the factsheet-side key is named for that parent and not for the
    `Energymodel` / `Energyframework` being seeded.
    """
    sheet_fk = tag_fk = None
    for f in through._meta.get_fields():
        if not f.many_to_one:
            continue
        if f.related_model is Tag:
            tag_fk = f.attname
        else:
            sheet_fk = f.attname
    if sheet_fk is None or tag_fk is None:
        raise AssertionError(
            "could not find both foreign keys on %s" % (through.__name__,)
        )
    return sheet_fk, tag_fk
