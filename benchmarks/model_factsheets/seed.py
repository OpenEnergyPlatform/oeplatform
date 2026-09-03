"""Build a factsheet corpus in the current (test) database.

Rows are generated from `profile.FieldProfile`, so column widths and word
counts match production even though every value is nonsense. Nothing here
touches production or a developer database - `run.py` only ever calls it
against a Django TEST database it created itself.
"""

from __future__ import annotations

import random

from django.contrib.postgres.fields import ArrayField
from django.db import models as dj_models
from django.db import transaction

from benchmarks.model_factsheets.profile import Corpus, FieldProfile

#: Columns that must not be generated: identity, files, relations.
SKIP = {"id", "basicfactsheet_ptr", "logo", "tags"}


def _fillable(model_cls):
    """Concrete, generatable columns of the factsheet model."""
    out = []
    for f in model_cls._meta.get_fields():
        if not hasattr(f, "attname") or f.attname in SKIP:
            continue
        if isinstance(f, (dj_models.AutoField, dj_models.ImageField)):
            continue
        if f.many_to_many or f.one_to_one:
            continue
        out.append(f)
    return out


def _value(f, prof: FieldProfile, rng: random.Random):
    if isinstance(f, ArrayField):
        text = prof.text_for(f.attname, rng)
        return [t for t in text.split(" ") if t][:6]
    if isinstance(f, dj_models.BooleanField):
        # 119 of 192 columns are booleans; on production most are unset.
        return rng.choice([True, False, None]) if f.null else rng.random() < 0.3
    if isinstance(f, dj_models.DateField):
        return None
    text = prof.text_for(f.attname, rng)
    max_len = getattr(f, "max_length", None)
    return text[:max_len] if max_len else text


def seed(corpus: Corpus, model_cls, tag_cls, echo=print) -> dict:
    """Create `corpus.tags` tags and `corpus.models` factsheets, then link.

    Returns the counts actually written, including the total number of
    factsheet->tag edges - the number that drives the list page's payload.
    """
    rng = random.Random(corpus.seed)
    prof = FieldProfile.load()

    tag_cls.objects.all().delete()
    model_cls.objects.all().delete()

    # Tag's primary key is `name_normalized` (a CharField), and `color_hex`
    # is a read-only property over the `color` integer - both easy to get
    # wrong, both load-bearing for the through table below.
    tag_cls.objects.bulk_create(
        [
            tag_cls(
                name_normalized="bench_tag_%04d" % i,
                name="bench tag %04d" % i,
                color=rng.randrange(0xFFFFFF),
            )
            for i in range(corpus.tags)
        ]
    )
    tags = list(tag_cls.objects.order_by("pk"))
    echo("  seeded %d tags" % len(tags))

    # `Energymodel` is multi-table inheritance over the concrete
    # `BasicFactsheet`, so Django refuses bulk_create: every row is two
    # INSERTs. One transaction keeps the seed to a few seconds anyway.
    fields = _fillable(model_cls)
    with transaction.atomic():
        for i in range(corpus.models):
            kwargs = {f.attname: _value(f, prof, rng) for f in fields}
            kwargs["model_name"] = "Bench Model %04d %s" % (
                i,
                kwargs.get("model_name", ""),
            )
            model_cls.objects.create(**kwargs)
    sheets = list(model_cls.objects.order_by("pk"))
    echo("  seeded %d factsheets" % len(sheets))

    through = model_cls.tags.through
    counts = corpus.tag_counts()
    links, edges = [], 0
    # `tags` is declared on BasicFactsheet, and Energymodel/Energyframework
    # inherit it by multi-table inheritance - so the through table's FK is
    # named for the PARENT, not for the class being seeded.
    fk = next(
        f.attname
        for f in through._meta.get_fields()
        if f.many_to_one and f.related_model is not tag_cls
    )
    for sheet, n in zip(sheets, counts):
        for tag in rng.sample(tags, min(n, len(tags))):
            links.append(through(**{fk: sheet.pk, "tag_id": tag.pk}))
            edges += 1
    through.objects.bulk_create(links, batch_size=5000)
    echo(
        "  seeded %d factsheet->tag edges (mean %.1f per sheet)"
        % (edges, edges / max(1, len(sheets)))
    )

    return {"models": len(sheets), "tags": len(tags), "edges": edges}
