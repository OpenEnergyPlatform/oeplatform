"""Seed dashboard accounts for the datasets tab (#2622, spec #2613).

A port of the WF-07 prototype's fake data (vault, ``user-dashboard/
_wayfinder-datasets-tab/assets/WF-07 - datasets tab prototype.html``).
Datasets are not used on production beyond small tests, so nothing here is
sized from a census; the accounts cover every case the list has to show:

- ``empty``: no Datasets;
- ``six``: six hand-written Datasets, one per case: a published one of 14
  members with a draft and embargoed mix and two strangers' Tables; a
  published one of 2,500 members (90 drafts), the bulk-add ceiling; a draft
  with a stranger's draft member and no Topic; an empty draft (both gate
  hints); a published one of strangers' Tables only whose Modified is
  unknown; a draft ready to publish;
- ``sixty``: sixty generated ones, for paging: about 40 % published, 0 to 30
  members, 0 to 4 Topics, about 15 % with an unknown Modified.

Every Dataset sets ``published_at`` explicitly (a bare create is a draft).
Deterministic for a given account key. For the browser check, from
``manage.py shell``::

    from benchmarks.tables_tab.seed_datasets import seed_datasets
    seed_datasets("six")
"""

from __future__ import annotations

import random
from datetime import timedelta

from benchmarks.tables_tab.seed import REGIONS, SUBJECTS, TAGS, TOPICS, YEARS, title

ACCOUNTS = ("empty", "six", "sixty")

DATASET_TITLES = [
    "Onshore wind expansion",
    "Heat atlas",
    "Distribution grid baseline",
    "Hydrogen corridors",
    "Rooftop PV potential",
    "District heating networks",
    "Household load profiles",
    "Power plant register",
    "Electricity price scenarios",
    "Battery storage fleet",
]


def seed_datasets(key: str, label: str = ""):
    """Seed account ``key`` and return its owner, ``bench_ds_<label>`` (the
    label defaults to the key)."""
    from django.utils import timezone

    from dataedit.models import Dataset, Embargo, Table, Tag, Topic
    from login.models import ADMIN_PERM, UserPermission, myuser

    label = label or key
    rng = random.Random(f"datasets-{key}")
    now = timezone.now()

    def user(name):
        found, _ = myuser.objects.get_or_create(
            name=name,
            defaults={
                "email": f"{name.lower()}@bench.test",
                "did_agree": True,
                "is_mail_verified": True,
            },
        )
        return found

    owner = user(f"bench_ds_{label}")
    stranger = user(f"bench_ds_{label}_stranger")
    topics = {name: Topic.objects.get_or_create(name=name)[0] for name in TOPICS}
    tags = {}
    for name in TAGS:
        tag = Tag.objects.filter(pk=Tag.get_name_normalized(name)).first()
        if tag is None:
            tag = Tag(name=name)
            tag.save()
        tags[name] = tag

    def tables(prefix, count, published=0.6, embargoed=0.1, holder=None):
        """``count`` Tables, a draft and embargoed mix, titled like real
        ones, each with up to three tags."""
        made = Table.objects.bulk_create(
            Table(
                name=f"bds_{label}_{prefix}_{n:04d}",
                human_readable_name=(
                    None
                    if rng.random() < 0.15
                    else title(
                        rng.choice(SUBJECTS),
                        rng.choice(list(REGIONS)),
                        rng.choice(YEARS),
                        "",
                    )
                ),
                is_publish=rng.random() < published,
            )
            for n in range(count)
        )
        Embargo.objects.bulk_create(
            Embargo(
                table=table,
                date_ended=now + timedelta(days=rng.randint(20, 360)),
                duration="1_year",
            )
            for table in made
            if table.is_publish and rng.random() < embargoed
        )
        Table.tags.through.objects.bulk_create(
            Table.tags.through(table=table, tag=tags[name])
            for table in made
            for name in set(rng.sample(TAGS, rng.randrange(4)))
        )
        if holder is not None:
            UserPermission.objects.bulk_create(
                UserPermission(holder=holder, table=table, level=ADMIN_PERM)
                for table in made
            )
        return made

    def dataset(
        name, title_text, published, modified, members=(), topic_names=(), days=0
    ):
        made = Dataset.objects.create(
            name=f"{name}_{label}",
            metadata={"name": name, "title": title_text, "description": ""},
            creator=owner,
            published_at=published,
            modified_at=modified,
        )
        # after the insert, because auto_now_add overrides a value given to it
        Dataset.objects.filter(pk=made.pk).update(created_at=now - timedelta(days=days))
        Dataset.tables.through.objects.bulk_create(
            Dataset.tables.through(dataset=made, table=table) for table in members
        )
        made.topics.add(*(topics[t] for t in topic_names))
        return made

    if key == "empty":
        return owner

    if key == "six":
        own = tables("own", 130, holder=owner)
        theirs = tables("theirs", 2500, published=0.964, holder=stranger)
        their_drafts = [t for t in theirs if not t.is_publish]
        days = timedelta(days=1)
        dataset(
            "de_wind_2030",
            "Onshore wind expansion, Germany 2030",
            now - 40 * days,
            now - 2 * days,
            own[:12] + theirs[:2],
            ("climate", "openstreetmap", "supply"),
            days=200,
        )
        dataset(
            "eu_grid_everything",
            "European transmission grid, every published table",
            now - 10 * days,
            now - 1 * days,
            theirs,
            ("grid", "environment"),
            days=120,
        )
        dataset(
            "heat_draft",
            "Heat atlas, North Rhine-Westphalia",
            None,
            now - 3 * days,
            own[20:25] + their_drafts[:1],
            (),
            days=30,
        )
        dataset("empty_draft", "Hydrogen corridors", None, now, (), (), days=0)
        dataset(
            "partner_tables",
            "Partner institute load profiles",
            now - 300 * days,
            None,
            theirs[100:108],
            ("demand",),
            days=400,
        )
        dataset(
            "ready_to_publish",
            "Rooftop PV potential, Bavaria 2035",
            None,
            now - 5 * days,
            own[30:36],
            ("supply", "environment"),
            days=8,
        )
        return owner

    pool = tables("own", 130, holder=owner) + tables("theirs", 300, holder=stranger)
    for n in range(60):
        published = rng.random() < 0.4
        dataset(
            f"generated_{n:02d}",
            f"{rng.choice(DATASET_TITLES)}, "
            f"{REGIONS[rng.choice(list(REGIONS))]} {rng.choice(YEARS)}",
            now - timedelta(days=rng.randint(0, 300)) if published else None,
            (
                None
                if rng.random() < 0.15
                else now - timedelta(days=rng.randint(0, 60), hours=rng.randint(0, 23))
            ),
            rng.sample(pool, rng.randrange(31)),
            rng.sample(TOPICS, rng.randrange(5)),
            days=rng.randint(0, 330),
        )
    return owner
