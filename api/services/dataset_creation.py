# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut # noqa: E501
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import re
from copy import deepcopy
from typing import Any

from django.db.models import Q, QuerySet
from django.utils import timezone
from oemetadata.v2.v20.example import OEMETADATA_V20_EXAMPLE
from oemetadata.v2.v20.template import OEMETADATA_V20_TEMPLATE

from dataedit.models import Dataset, Table, Topic
from login.permissions import WRITE_PERM
from oeplatform.settings import PSEUDO_TOPIC_DRAFT


class DatasetNameTaken(Exception):
    """Raised when creating a dataset under a name that already exists."""


def normalize_dataset_name(title: str) -> str | None:
    """Derive the permanent URL name from a human-styled title: lowercase,
    every run of non-alphanumeric characters becomes one underscore. The
    title keeps the user's preferred styling; the name keys URLs and the
    oemetadata document. Returns None when nothing usable remains."""
    name = (title or "").lower()
    name = re.sub(r"[^a-z0-9]+", "_", name).strip("_")
    name = name[:60].strip("_")
    return name or None


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
    """
    name = validated_data["name"]
    if Dataset.objects.filter(name=name).exists():
        raise DatasetNameTaken(
            f"A dataset named '{name}' already exists. Names are permanent "
            "identifiers and can not be reused."
        )

    metadata = assemble_dataset_metadata(validated_data)
    return Dataset.objects.create(metadata=metadata, name=name, creator=creator)


def user_may_assign_table(user, table: Table) -> bool:
    """Curation model: any published table may be assigned to a dataset;
    draft tables and tables under an active embargo only by users holding
    write permission on the table (owners staging a release)."""
    from api.helper import check_embargo

    if table.is_publish and not check_embargo(table):
        return True
    return user.has_write_permissions(table.name)


def assignable_tables_for(user, dataset: Dataset, search: str = "") -> QuerySet[Table]:
    """Tables the user may assign to the dataset under the curation rules,
    excluding tables already assigned. Queryset twin of
    user_may_assign_table for the dashboard picker."""
    now = timezone.now()
    writable_ids = user.get_tables_queryset(
        min_permission_level=WRITE_PERM
    ).values_list("id", flat=True)

    freely_assignable = Q(is_publish=True) & ~Q(embargos__date_ended__gt=now)
    tables = Table.objects.filter(freely_assignable | Q(id__in=writable_ids))
    tables = tables.exclude(id__in=dataset.tables.values_list("id", flat=True))

    if search:
        tables = tables.filter(
            Q(name__icontains=search) | Q(human_readable_name__icontains=search)
        )

    return tables.distinct().order_by("name").prefetch_related("topics")


def assign_table(dataset: Dataset, table: Table) -> None:
    """Add a table to a dataset and seed the dataset's topics additively:
    the table's topics are added (except the draft pseudo-topic), existing
    topics are never removed, so creator-curated removals survive."""
    dataset.tables.add(table)
    dataset.topics.add(*table.topics.exclude(name=PSEUDO_TOPIC_DRAFT))


def set_dataset_topics(dataset: Dataset, topic_names: list[str]) -> None:
    """Replace the creator-curated topic set. Unknown names are ignored and
    the draft pseudo-topic can never become a dataset topic."""
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
