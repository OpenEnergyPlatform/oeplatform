# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut # noqa: E501
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import re
from copy import deepcopy
from typing import Any

from django.db import transaction
from django.db.models import Q, QuerySet
from django.utils import timezone
from oemetadata.v2.v20.example import OEMETADATA_V20_EXAMPLE
from oemetadata.v2.v20.template import OEMETADATA_V20_TEMPLATE

from dataedit.models import Dataset, Table, Topic
from login.permissions import WRITE_PERM
from oeplatform.settings import PSEUDO_TOPIC_DRAFT


class DatasetNameTaken(Exception):
    """Raised when creating a dataset under a name that already exists."""


def name_taken(name: str) -> str:
    """What a create under the taken ``name`` is told."""
    return (
        f"A dataset named '{name}' already exists. Names are permanent "
        "identifiers and can not be reused."
    )


def normalize_dataset_name(title: str) -> str | None:
    """Derive the permanent URL name from a human-styled title: lowercase,
    every run of non-alphanumeric characters becomes one underscore. The
    title keeps the user's preferred styling; the name keys URLs and the
    oemetadata document. Returns None when nothing usable remains."""
    name = (title or "").lower()
    name = re.sub(r"[^a-z0-9]+", "_", name).strip("_")
    name = name[:60].strip("_")
    return name or None


def dataset_title(dataset: Dataset) -> str:
    """What a Dataset is called where a user reads it: its title, or its
    name when it has none."""
    return (dataset.metadata or {}).get("title") or dataset.name


def assemble_dataset_metadata(
    validated_data: dict[str, Any], oemetadata: dict = OEMETADATA_V20_TEMPLATE
) -> dict[str, Any]:
    # set the context
    oemetadata = deepcopy(oemetadata)
    oemetadata["@context"] = OEMETADATA_V20_EXAMPLE["@context"]
    # resources are never stored on the dataset; they are assembled live
    # from the member tables on every read
    oemetadata.pop("resources", None)

    oemetadata["@id"] = validated_data.get("at_id")
    oemetadata["name"] = validated_data["name"]
    oemetadata["title"] = validated_data["title"]
    oemetadata["description"] = validated_data["description"]

    return oemetadata


def create_dataset(validated_data: dict[str, Any], creator) -> Dataset:
    """Create a creator-owned dataset from validated dataset-level fields.

    Shared by the JSON API and the dashboard UI so both enforce the same
    rules. Raises DatasetNameTaken on a name collision (the name is the
    permanent identifier, so it must be unique).

    A new Dataset is a draft, and its first Modification is its creation:
    ``modified_at`` is ``created_at``, to the microsecond.
    """
    name = validated_data["name"]
    if Dataset.objects.filter(name=name).exists():
        raise DatasetNameTaken(name_taken(name))

    metadata = assemble_dataset_metadata(validated_data)
    dataset = Dataset.objects.create(metadata=metadata, name=name, creator=creator)
    # ``created_at`` is ``auto_now_add``, which overwrites any value given to
    # ``create``, so the copy follows it
    Dataset.objects.filter(pk=dataset.pk).update(modified_at=dataset.created_at)
    dataset.modified_at = dataset.created_at
    return dataset


def assignable_tables(user) -> QuerySet[Table]:
    """Every Table ``user`` may assign to a Dataset of their own: the one
    curation rule, which the dashboard's row actions, the Dataset tab's
    picker and the dataset assign API all read.

    Curation model: anyone may assign a published Table that is not under an
    active embargo; its holders have no say. A draft, or a Table under an
    active embargo, only a user holding Data editor or above on it, directly
    or through an Organization they are a member of (owners staging a
    release). There is no platform-admin exemption: only grants count, so a
    Table offered anywhere is a Table this rule accepts.
    """
    writable = user.get_tables_queryset(min_permission_level=WRITE_PERM)
    freely_assignable = Q(is_publish=True) & ~Q(embargos__date_ended__gt=timezone.now())
    return Table.objects.filter(
        freely_assignable | Q(id__in=writable.values("id"))
    ).distinct()


def user_may_assign_table(user, table: Table) -> bool:
    """Whether ``user`` may assign ``table`` to a Dataset of their own, under
    ``assignable_tables``. One query."""
    return assignable_tables(user).filter(pk=table.pk).exists()


def assignable_tables_for(user, dataset: Dataset, search: str = "") -> QuerySet[Table]:
    """Tables the user may assign to the dataset under the curation rules,
    excluding tables already assigned: the dashboard picker."""
    tables = assignable_tables(user).exclude(
        id__in=dataset.tables.values_list("id", flat=True)
    )

    if search:
        tables = tables.filter(
            Q(name__icontains=search) | Q(human_readable_name__icontains=search)
        )

    return tables.order_by("name").prefetch_related("topics")


@transaction.atomic
def assign_table(dataset: Dataset, table: Table) -> None:
    """Add a table to a dataset and seed the dataset's topics additively:
    the table's topics are added (except the draft pseudo-topic), existing
    topics are never removed, so creator-curated removals survive. Both
    writes, or neither."""
    dataset.tables.add(table)
    dataset.topics.add(*table.topics.exclude(name=PSEUDO_TOPIC_DRAFT))


def set_dataset_topics(dataset: Dataset, topic_names: list[str]) -> None:
    """Replace the creator-curated topic set. Unknown names are ignored and
    the draft pseudo-topic can never become a dataset topic: the Dataset
    action service refuses both by name before it calls this
    (``dataset_actions.validated_topics``); the old dashboard edit still
    relies on the silence, until it moves onto the service (#2624)."""
    topics = Topic.objects.filter(name__in=topic_names).exclude(name=PSEUDO_TOPIC_DRAFT)
    dataset.topics.set(topics)


def update_dataset(dataset: Dataset, validated_data: dict[str, Any]) -> Dataset:
    """Update the editable dataset-level fields (title, description, @id).

    The name is immutable and always taken from the existing dataset; a
    missing @id keeps the stored one.
    """
    data = dict(validated_data)
    data["name"] = dataset.name
    if not data.get("at_id"):
        data["at_id"] = dataset.metadata.get("@id")

    dataset.metadata = assemble_dataset_metadata(data)
    dataset.save()
    return dataset
