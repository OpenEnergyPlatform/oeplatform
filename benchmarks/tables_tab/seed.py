"""Seed dashboard accounts shaped like production for the tables tab.

A port of the WF-06 prototype's generator (vault, ``user-dashboard/_wayfinder/
assets/WF-06 - tables tab prototype.html``), whose mix was sized from WF-01's
production census (2026-10-01):

- ``p90``: 130 Tables (the 90th percentile of users with any), 40 %
  published, 16 % reached only through an Organization, 35 % in a Dataset;
- ``max``: 2,068 Tables (the largest account), mixed;
- ``maxreal``: 2,068 Tables as that account is measured: all draft, all
  direct, almost no Datasets.

Common to all: 11 % fail the Publish gate (a license that is not open, none
at all, or one not in the SPDX list), about 10 % of published Tables are
under embargo, 15-20 % have no title, and Topics sit mostly on published
Tables. Deterministic for a given account key.

Modified is seeded as it will look once #2558 has backfilled the data half:
about 15 % unknown, 45 % data only (marked "data"), 40 % both halves. The
stamps come from their own random stream, so the rest of an account is
seeded as before. Created is seeded as production holds it after
dataedit.0057 (measured 2026-10-05: 4,567 of 5,114 Tables lie at or below the
rollout line): about 89 % unknown ("before Nov 2025"), the rest created since
November 2025, again from a stream of its own.

Every Table carries ``metadata_kb`` of oemetadata, because the page query
decodes each row's whole document for the live Publish gate; real documents
range from a few KB to several hundred.

Used by ``run.py`` and, for the browser check, from ``manage.py shell``::

    from benchmarks.tables_tab.seed import seed_account
    seed_account("p90")
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import timedelta

TOPICS = [
    "boundaries",
    "climate",
    "demand",
    "economy",
    "emission",
    "environment",
    "grid",
    "openstreetmap",
    "policy",
    "reference",
    "scenario",
    "society",
    "supply",
]
# Each account draws its own from this pool: an Organization is shared by
# its members, so two accounts in one database must not share one.
ORGANIZATIONS = [
    "Grid Modelling Group",
    "Scenario Lab",
    "Heat Transition WG",
    "Energy Systems Analysis",
    "Open Data Team",
    "Regional Planning Unit",
    "Market Modelling",
    "Hydrogen Research Group",
    "Climate Policy Desk",
]
STRANGER_ORGANIZATION = "Partner Institute Data Team"
PEOPLE = ["Anna Schmidt", "Bao Nguyen", "Chiara Rossi", "Dmitri Volkov"]
SUBJECTS = [
    "wind_onshore",
    "wind_offshore",
    "pv_rooftop",
    "pv_openfield",
    "heat_demand",
    "power_demand",
    "gas_grid",
    "power_lines",
    "substations",
    "hydrogen_storage",
    "battery_storage",
    "biomass_plants",
    "ev_charging",
    "building_stock",
    "industry_sites",
    "household_loads",
    "district_heating",
    "heat_pumps",
    "hydro_plants",
    "emission_factors",
    "electricity_prices",
    "weather_ts",
    "population_grid",
    "land_use",
    "grid_nodes",
    "transformer_sites",
    "co2_budget",
    "power_plants",
    "capacity_factors",
    "load_profiles",
]
SUBJECT_LABELS = {
    "pv_rooftop": "PV rooftop",
    "pv_openfield": "PV open field",
    "ev_charging": "EV charging",
    "co2_budget": "CO2 budget",
    "weather_ts": "Weather time series",
}
REGIONS = {
    "de": "Germany",
    "eu": "EU",
    "nuts3": "NUTS-3 regions",
    "nrw": "North Rhine-Westphalia",
    "by": "Bavaria",
    "sh": "Schleswig-Holstein",
    "dk": "Denmark",
    "fr": "France",
    "pl": "Poland",
    "at": "Austria",
    "ch": "Switzerland",
    "nl": "Netherlands",
}
YEARS = ["2019", "2020", "2021", "2023", "2025", "2030", "2035", "2045", "2050"]
SUFFIXES = {
    "": "",
    "_raw": " (raw)",
    "_v2": " v2",
    "_hourly": ", hourly",
    "_agg": ", aggregated",
    "_scenario_a": ", scenario A",
    "_scenario_b": ", scenario B",
    "_legacy": " (legacy)",
    "_clean": " (cleaned)",
    "_weighted": ", weighted",
}
SUFFIX_KEYS = ["", "", "", ""] + [k for k in SUFFIXES if k]
TAGS = [
    "wind",
    "solar",
    "grid",
    "demand",
    "heat",
    "hydrogen",
    "storage",
    "emissions",
    "germany",
    "europe",
    "timeseries",
    "electricity",
]
GOOD_LICENSES = ["CC-BY-4.0", "CC0-1.0", "ODbL-1.0", "DL-DE-BY-2.0", "CC-BY-SA-4.0"]
# What a failing row carries: a license that is not open, none at all, and
# one that is not in the SPDX list.
BAD_LICENSES = ["CC-BY-NC-4.0", None, "Custom"]
BADGES = ["Iron", "Bronze", "Silver", "Gold", "Platinum"]
DATASETS = {
    # name: owner, None for the account itself
    "de_wind_2030": None,
    "grid_baseline": None,
    "eu_heat_atlas": None,
    "eu_renewables": "Anna Schmidt",
    "demand_profiles": "Bao Nguyen",
}
DATASET_POOL = [
    "de_wind_2030",
    "grid_baseline",
    "eu_heat_atlas",
    "eu_renewables",
    "demand_profiles",
    "de_wind_2030",
    "grid_baseline",
]


@dataclass(frozen=True)
class Account:
    n: int
    organizations: int
    published: float
    org_only: float
    both: float
    untitled: float
    in_dataset: float
    fail: float = 0.11


ACCOUNTS = {
    "p90": Account(130, 2, 0.4, 0.16, 0.02, 0.15, 0.35),
    "max": Account(2068, 3, 0.06, 0.03, 0.01, 0.2, 0.08),
    "maxreal": Account(2068, 0, 0.0, 0.0, 0.0, 0.2, 0.02),
}


def metadata(license_name, kb: float) -> dict:
    """An oemetadata v2 document of about ``kb`` kilobytes, its license
    ``license_name`` (None for no license at all)."""
    licenses = (
        [{"name": license_name, "title": license_name, "path": ""}]
        if license_name
        else []
    )
    field = {
        "name": "capacity_installed",
        "type": "double precision",
        "unit": "MW",
        "isAbout": [
            {
                "@id": "http://openenergy-platform.org/ontology/oeo/OEO_00010037",
                "name": "installed capacity",
            }
        ],
        "nullable": True,
        "description": "Installed electrical capacity of the unit, as reported "
        "by the operator in the national register.",
        "valueReference": [],
    }
    # one field is ~400 bytes serialised
    fields = [dict(field, name=f"column_{i}") for i in range(max(1, int(kb * 2.5)))]
    return {
        "@context": "https://raw.githubusercontent.com/OpenEnergyPlatform/oemetadata/production/oemetadata/latest/context.json",  # noqa: E501
        "metaMetadata": {"metadataVersion": "OEMetadata-2.0.4"},
        "resources": [
            {
                "title": "Seeded table",
                "licenses": licenses,
                "schema": {"fields": fields, "primaryKey": ["id"]},
            }
        ],
    }


def title(subject, region, year, suffix) -> str:
    label = SUBJECT_LABELS.get(subject) or subject.replace("_", " ").capitalize()
    return f"{label}, {REGIONS[region]} {year}{SUFFIXES[suffix]}"


def seed_account(
    key: str, metadata_kb: float = 6, used: set | None = None, label: str = ""
):
    """Seed account ``key`` and return its owner, ``bench_<label>`` (the
    label defaults to the key). Table names are globally unique, so pass the
    same ``used`` set when seeding several accounts into one database."""
    from django.utils import timezone

    from dataedit.models import Dataset, Embargo, PeerReview, Table, Tag, Topic
    from login.models import (
        ADMIN_PERM,
        DELETE_PERM,
        WRITE_PERM,
        GroupPermission,
        Membership,
        Organization,
        UserPermission,
        myuser,
    )

    account = ACCOUNTS[key]
    rng = random.Random(f"{key}-{account.n}")
    pick = rng.choice
    used = set(Table.objects.values_list("name", flat=True)) if used is None else used

    def user(name):
        found, _ = myuser.objects.get_or_create(
            name=name,
            defaults={
                "email": f"{name.lower().replace(' ', '.')}@bench.test",
                "did_agree": True,
                "is_mail_verified": True,
            },
        )
        return found

    label = label or key
    owner = user(f"bench_{label}")
    people = [user(name) for name in PEOPLE]
    organizations = []
    for base in rng.sample(ORGANIZATIONS, account.organizations):
        name, n = base, 1
        while Organization.objects.filter(name=name).exists():
            n += 1
            name = f"{base} {n}"
        organization = Organization.objects.create(name=name)
        Membership.objects.create(user=owner, group=organization)
        organizations.append(organization)
    stranger_org, _ = Organization.objects.get_or_create(name=STRANGER_ORGANIZATION)
    topics = {name: Topic.objects.get_or_create(name=name)[0] for name in TOPICS}
    tags = {}
    for name in TAGS:
        tag = Tag.objects.filter(pk=Tag.get_name_normalized(name)).first()
        if tag is None:
            tag = Tag(name=name)
            tag.save()
        tags[name] = tag
    datasets = {}
    for name, owner_name in DATASETS.items():
        dataset_name = f"{name}_{label}"
        creator = owner if owner_name is None else user(owner_name)
        # published, as every Dataset was when this shape was measured: a
        # stranger's draft would drop out of the account's Datasets column
        datasets[name], _ = Dataset.objects.get_or_create(
            name=dataset_name,
            defaults={"creator": creator, "published_at": timezone.now()},
        )

    now = timezone.now()
    stamps = random.Random(f"{key}-{account.n}-modified")

    def modified():
        """``(data_modified, metadata_modified)``, in the mix above."""
        roll = stamps.random()
        if roll < 0.15:
            return None, None
        data = now - timedelta(
            days=stamps.randint(0, 900), minutes=stamps.randint(0, 1439)
        )
        if roll < 0.6:
            return data, None
        return data, now - timedelta(days=stamps.randint(0, 30))

    plans = []
    for _ in range(account.n):
        while True:
            subject, region = pick(SUBJECTS), pick(list(REGIONS))
            year, suffix = pick(YEARS), pick(SUFFIX_KEYS)
            name = f"{subject}_{region}_{year}{suffix}"
            if name not in used:
                break
        used.add(name)
        published = rng.random() < account.published
        embargo = None
        if published and rng.random() < 0.1:
            embargo = now + timedelta(days=rng.randint(20, 360))
        fails = rng.random() < account.fail
        license_name = pick(BAD_LICENSES) if fails else pick(GOOD_LICENSES)
        roll = rng.random()
        if published:
            review = "reviewed" if roll < 0.3 else "in_review" if roll < 0.45 else ""
        else:
            review = "reviewed" if roll < 0.02 else "in_review" if roll < 0.07 else ""
        grants, org_grants = [], []
        x = rng.random()
        if organizations and x < account.org_only:
            level = ADMIN_PERM if rng.random() < 0.9 else DELETE_PERM
            org_grants.append((pick(organizations), level))
        elif organizations and x < account.org_only + account.both:
            grants.append(ADMIN_PERM)
            org_grants.append((pick(organizations), ADMIN_PERM))
        else:
            grants.append(ADMIN_PERM if rng.random() < 0.97 else WRITE_PERM)
        if rng.random() < 0.03:
            org_grants.append((stranger_org, DELETE_PERM))
        in_datasets = []
        if rng.random() < account.in_dataset:
            in_datasets.append(pick(DATASET_POOL))
            if rng.random() < 0.2:
                in_datasets.append(pick(DATASET_POOL))
        table_topics = []
        if published or rng.random() < 0.05:
            for _ in range(1 + rng.randrange(3) if published else 1):
                table_topics.append(pick(TOPICS))
        table_tags = [pick(TAGS) for _ in range(rng.randrange(6))]
        plans.append(
            dict(
                table=Table(
                    name=name,
                    human_readable_name=(
                        None
                        if rng.random() < account.untitled
                        else title(subject, region, year, suffix)
                    ),
                    is_publish=published,
                    oemetadata=metadata(license_name, metadata_kb),
                    **dict(zip(("data_modified", "metadata_modified"), modified())),
                ),
                embargo=embargo,
                review=review,
                badge=pick(BADGES),
                grants=grants,
                org_grants=org_grants,
                datasets=set(in_datasets),
                topics=set(table_topics),
                tags=set(table_tags),
            )
        )

    tables = Table.objects.bulk_create([plan["table"] for plan in plans])
    # after the insert, because auto_now_add overrides a value given to it
    births = random.Random(f"{key}-{account.n}-created")
    unknown, known = [], []
    for table in tables:
        (unknown if births.random() < 0.89 else known).append(table.pk)
    Table.objects.filter(pk__in=unknown).update(created=None)
    for pk in known:
        Table.objects.filter(pk=pk).update(
            created=now - timedelta(days=births.randint(0, 330))
        )
    UserPermission.objects.bulk_create(
        UserPermission(holder=owner, table=table, level=level)
        for plan, table in zip(plans, tables)
        for level in plan["grants"]
    )
    GroupPermission.objects.bulk_create(
        GroupPermission(holder=organization, table=table, level=level)
        for plan, table in zip(plans, tables)
        for organization, level in plan["org_grants"]
    )
    Embargo.objects.bulk_create(
        Embargo(table=table, date_ended=plan["embargo"], duration="1_year")
        for plan, table in zip(plans, tables)
        if plan["embargo"]
    )
    PeerReview.objects.bulk_create(
        PeerReview(
            table=table.name,
            contributor=owner,
            reviewer=people[0],
            is_finished=plan["review"] == "reviewed",
            date_finished=now if plan["review"] == "reviewed" else None,
            review={"badge": plan["badge"]} if plan["review"] == "reviewed" else {},
        )
        for plan, table in zip(plans, tables)
        if plan["review"]
    )
    Dataset.tables.through.objects.bulk_create(
        Dataset.tables.through(dataset=datasets[name], table=table)
        for plan, table in zip(plans, tables)
        for name in plan["datasets"]
    )
    Table.topics.through.objects.bulk_create(
        Table.topics.through(table=table, topic=topics[name])
        for plan, table in zip(plans, tables)
        for name in plan["topics"]
    )
    Table.tags.through.objects.bulk_create(
        Table.tags.through(table=table, tag=tags[name])
        for plan, table in zip(plans, tables)
        for name in plan["tags"]
    )
    return owner
