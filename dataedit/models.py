"""
SPDX-FileCopyrightText: 2025 Pierre Francois <https://github.com/Bachibouzouk> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Pierre Francois <https://github.com/Bachibouzouk> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Daryna Barabanova <https://github.com/Darynarli> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Tom Heimbrodt <https://github.com/tom-heimbrodt>
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Daryna Barabanova <https://github.com/Darynarli> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Stephan Uller <https://github.com/steull> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 user <https://github.com/Darynarli> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import json
import logging
import re
from datetime import datetime, timedelta
from enum import Enum
from typing import Union

from django.contrib.postgres.search import SearchVectorField
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import (
    BooleanField,
    CharField,
    DateTimeField,
    ForeignKey,
    IntegerField,
    JSONField,
    QuerySet,
)
from django.urls import reverse
from django.utils import timezone

from oeplatform.securitysettings import SCHEMA_DATA, SCHEMA_DEFAULT_TEST_SANDBOX


class TableRevision(models.Model):
    table = CharField(max_length=1000, null=False)
    date = DateTimeField(max_length=1000, null=False, default=timezone.now)
    created = DateTimeField(null=False, default=timezone.now)
    path = CharField(max_length=1000, null=False)
    size = IntegerField(null=False)
    last_accessed = DateTimeField(null=False, default=timezone.now)


class Tagable(models.Model):
    name = CharField(max_length=1000, null=False)

    class Meta:
        abstract = True


class Topic(models.Model):
    name = CharField(max_length=128, primary_key=True)


class Tag(models.Model):
    name_normalized = CharField(max_length=40, primary_key=True)
    usage_count = IntegerField(default=0, null=False)
    name = CharField(max_length=40, null=False)
    color = IntegerField(default=int("2E3638", 16), null=False)
    usage_tracked_since = DateTimeField(null=False, default=timezone.now)

    @classmethod
    def get_name_normalized(cls, name: str | None) -> str | None:
        name_norm = name or ""
        name_norm = name_norm.lower()
        name_norm = re.sub("[^a-z0-9]+", "_", name_norm)
        name_norm = name_norm.strip("_")
        name_norm = name_norm[:40]  # max len
        if not name_norm:  # no empty string
            name_norm = None
        return name_norm

    @classmethod
    def get_name_clean(cls, name: str | None) -> str | None:
        name_clean = name or ""
        re.sub(r"\s+", " ", name_clean)
        name_clean = name_clean.strip()
        if not name_clean:  # no empty string
            name_clean = None
        return name_clean

    def save(self, *args, **kwargs):
        if not self.pk:  # create, not update
            self.name = self.get_name_clean(self.name)
            self.name_normalized = self.get_name_normalized(self.name)
            if isinstance(self.color, str) and self.color[0] == "#":
                self.color = self.color_from_hex(self.color)
        super().save(*args, **kwargs)

    @property
    def color_hex(self) -> str:
        return "#" + format(self.color, "06X")

    @staticmethod
    def color_from_hex(color_hex: str) -> int:
        return int(color_hex[1:], 16)

    def increment_usage_count(self):
        self.usage_count += 1
        self.save()

    @staticmethod
    def increment_usage_count_many(tag_ids: list[str]) -> None:
        if not tag_ids:
            return
        for tag_id in tag_ids:
            tag = Tag.get_or_none(tag_id)
            if not tag:
                continue
            tag.increment_usage_count()

    @staticmethod
    def get_or_none(pk: str) -> Union["Tag", None]:
        return Tag.objects.filter(pk=pk).first()

    @staticmethod
    def get_or_create_from_name(name: str) -> "Tag":
        pk = Tag.get_name_normalized(name)
        if not pk:
            raise ValueError("Invalid tag name")
        tag = Tag.get_or_none(pk=pk)
        if not tag:
            tag = Tag(name=name)
            tag.save()
        return tag


class Table(Tagable):
    """
    Represents a table within the database.

    Attributes:
        search (SearchVectorField): A field for full-text search.
        oemetadata (JSONField): A field to store oemetadata related
            to the table.
        is_reviewed (BooleanField): A flag indicating whether
            the table is reviewed.

    Note:
        The oemetadata field helps avoid performance issues due to
        JSON string parsing.
    """

    search = SearchVectorField(default="")

    # TODO: Maybe oemetadata should be stored in a separate table and
    # imported via FK here
    oemetadata = JSONField(null=True)
    is_reviewed = BooleanField(default=False, null=False)
    is_publish = BooleanField(null=False, default=False)
    human_readable_name = CharField(max_length=1000, null=True)
    is_sandbox = BooleanField(null=False, default=False)
    topics = models.ManyToManyField(Topic, related_name="tables")
    tags = models.ManyToManyField(Tag, related_name="tables")

    class Meta:
        unique_together = (("name",),)

    def get_absolute_url(self):
        return reverse("dataedit:view", kwargs={"pk": self.pk})

    @property
    def oedb_schema(self) -> str:
        return SCHEMA_DEFAULT_TEST_SANDBOX if self.is_sandbox else SCHEMA_DATA

    @classmethod
    def load(cls, name: str) -> "Table":
        """
        Load a table object from the database given its name.

        Args:
            name (str): The name of the table.

        Returns:
            Table: The loaded table object.

        Raises:
            DoesNotExist: If no table with the given name exists
            in the database.
        """

        table_obj = Table.objects.get(name=name)

        return table_obj

    @classmethod
    def get_or_none(cls, name: str) -> Union["Table", None]:
        return Table.objects.filter(name=name).first()

    def set_is_reviewed(self):
        """
        Mark the table as reviewed and save the change to the database.
        """
        self.is_reviewed = True
        self.save()

    # TODO: Use function when implementing the publish button
    def set_is_published(self, topic_name: str):
        """
        Mark the table as published
        and save the change to the database.
        """
        topic = Topic.objects.get(name=topic_name)
        self.is_publish = True
        self.topics.add(topic)
        self.save()

    # TODO: Use function when implementing the publish button. It should be
    # possible to unpublish a table. This button should be next to the tables
    # listed in Published on the profile page.
    def set_not_published(self):
        """
        Mark the table as not published (making it a draft table again)
        and save the change to the database.
        """
        self.is_publish = False
        self.save()

    # used in api action every time the table metadata is updated
    def set_human_readable_name(self, current_name, readable_table_name: str):
        """
        Set the readable table name for this table.
        The function attempts to retrieve a string form the tables
        oemetadata object. The name is read from the "title" field.

        return: str
        """
        # avoid writing none values & writing non changes
        # non changes mean that the oemetadata was updated
        # but not the title field
        if readable_table_name and readable_table_name is not current_name:
            self.human_readable_name = readable_table_name
            self.save()

    def get_readable_table_name(self) -> str:
        """get readable table name from metadata

        Args:
            table_obj (object): django orm

        Returns:
            str
        """

        def read_label_only_for_first_resource_element(
            table_name: str, oemetadata: dict
        ) -> str:
            """
            Extracts the readable name from oemetadata and appends the real name
            in parenthesis.
            If oemetadata is not a JSON-dictionary or does not contain a field 'Name'
            None is returned.

            :param table: Name to append

            :param comment: String containing a JSON-dictionary according to @Metadata

            :return: Readable name appended by the true table name as string or None
            """
            try:
                if oemetadata.get("resources")[0]:
                    return (
                        oemetadata.get("resources", [])[0]["title"].strip()
                        + " ("
                        + table_name
                        + ")"
                    )

                else:
                    return None

            except Exception:
                return None

        try:
            label = read_label_only_for_first_resource_element(
                self.name, self.oemetadata
            )
        except Exception as e:
            raise e
        return label


class Embargo(models.Model):
    DURATION_CHOICES = [
        ("6_months", "6 Months"),
        ("1_year", "1 Year"),
    ]

    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name="embargoes")
    date_started = models.DateTimeField(auto_now_add=True)
    date_ended = models.DateTimeField()
    duration = models.CharField(max_length=10, choices=DURATION_CHOICES)

    def is_active(self):
        return datetime.now() < self.date_ended

    def remaining_days(self):
        return (self.date_ended - datetime.now()).days if self.is_active() else 0

    def __str__(self):
        return f"Table {self.table} in embargo until {self.date_ended.strftime('%Y-%m-%d')}"  # noqa: E501

    def save(self, *args, **kwargs):
        if not self.date_started:
            self.date_started = timezone.now()
        if self.duration == "6_months":
            self.date_ended = self.date_started + timedelta(weeks=26)
        elif self.duration == "1_year":
            self.date_ended = self.date_started + timedelta(weeks=52)
        else:
            self.date_ended = None

        super().save(*args, **kwargs)


class View(models.Model):
    name = CharField(max_length=50, null=False)
    table = CharField(max_length=1000, null=False)
    VIEW_TYPES = (("table", "table"), ("map", "map"), ("graph", "graph"))
    type = CharField(max_length=10, null=False, choices=VIEW_TYPES)
    options = JSONField(null=False, default=dict)
    is_default = BooleanField(default=False)

    def __str__(self):
        return '{}--"{}"({})'.format(self.table, self.name, self.type.upper())


class Filter(models.Model):
    column = CharField(max_length=100, null=False)
    FILTER_TYPES = (("equal", "equal"), ("range", "range"))
    type = CharField(max_length=10, null=False, choices=FILTER_TYPES)
    value = JSONField(null=False)
    view = ForeignKey(View, on_delete=models.CASCADE, related_name="filter")


class PeerReview(models.Model):
    """
    Represents a peer review in the database.

    Attributes:
        table (CharField): Name of the table being reviewed.
        reviewer (ForeignKey): The user who reviews.
        contributor (ForeignKey): The user who contributes.
        is_finished (BooleanField): Whether the review is finished.
        date_started (DateTimeField): When the review started.
        date_submitted (DateTimeField): When the review was submitted.
        date_finished (DateTimeField): When the review finished.
        review (JSONField): The review data in JSON format.
    """

    table = CharField(max_length=1000, null=False)
    reviewer = ForeignKey(
        "login.myuser", on_delete=models.CASCADE, related_name="reviewed_by", null=True
    )
    contributor = ForeignKey(
        "login.myuser",
        on_delete=models.CASCADE,
        related_name="review_received",
        null=True,
    )
    is_finished = BooleanField(null=False, default=False)
    date_started = DateTimeField(max_length=1000, null=False, default=timezone.now)
    date_submitted = DateTimeField(max_length=1000, null=True, default=None)
    date_finished = DateTimeField(max_length=1000, null=True, default=None)
    review = JSONField(null=True)
    # TODO: Maybe oemetadata should be stored in a separate table and imported
    # via FK here / change also for Tables model
    oemetadata = JSONField(null=False, default=dict)

    # laden
    @classmethod
    def load(cls, table: str) -> Union["PeerReview", None]:
        """
        Load the current reviewer user.
        The current review is review is determened by the latest date started.

        Args:
            table (string): Table name

        Returns:
            opr (PeerReview): PeerReview object related to the latest
            date started.
        """
        opr = PeerReview.objects.filter(table=table).order_by("-date_started").first()
        return opr

    # TODO: CAUTION unfinished work ... fix: includes all id´s and not just the
    # related ones (reviews on same table) .. procedures false results
    def get_prev_and_next_reviews(self, table: str):
        """
        Sets the prev_review and next_review fields based on the date_started
        field of the PeerReview objects associated with the same table.
        """
        # Get all the PeerReview objects associated with the same table name
        peer_reviews = PeerReview.objects.filter(table=table).order_by("date_started")

        current_index = None
        for index, review in enumerate(peer_reviews):
            if review.pk == self.pk:
                current_index = index
                break

        prev_review = None
        next_review = None

        if current_index is not None:
            if current_index > 0:
                prev_review = peer_reviews[current_index - 1]

            if current_index < len(peer_reviews) - 1:
                next_review = peer_reviews[current_index + 1]

        return prev_review, next_review

    def save(self, *args, **kwargs):
        review_type = kwargs.pop("review_type", None)
        pm_new = None

        if not self.contributor == self.reviewer:
            super().save(*args, **kwargs)
            # TODO: This causes errors if review list ist empty

            if review_type == "save":
                pm_new = PeerReviewManager(
                    opr=self, status=ReviewDataStatus.SAVED.value
                )

            elif review_type == "submit":
                result = self.set_version_of_metadata_for_review(table=self.table)
                if result[0]:
                    logging.info(result[1])
                elif result[0] is False:
                    logging.info(result[1])

                pm_new = PeerReviewManager(
                    opr=self, status=ReviewDataStatus.SUBMITTED.value
                )
                pm_new.set_next_reviewer()

            elif review_type == "finished":
                result = self.set_version_of_metadata_for_review(table=self.table)
                if result[0]:
                    logging.info(result[1])
                elif result[0] is False:
                    logging.info(result[1])

                pm_new = PeerReviewManager(
                    opr=self, status=ReviewDataStatus.FINISHED.value
                )
                self.is_finished = True
                self.date_finished = timezone.now()
                super().save(*args, **kwargs)

            if pm_new:
                pm_new.save()

        else:
            raise ValidationError("Contributor and reviewer cannot be the same.")

    def delete(self, *args, **kwargs):
        """
        Custom delete method to remove related PeerReviewManager entries.
        """
        # Remove related records in PeerReviewManager
        PeerReviewManager.objects.filter(opr=self).delete()

        super().delete(*args, **kwargs)

    def update(self, *args, **kwargs):
        """
        Update the peer review if the latest peer review is not finished yet
        but either saved or submitted.

        """

        review_type = kwargs.pop("review_type", None)
        if not self.contributor == self.reviewer:
            current_pm = PeerReviewManager.load(opr=self)
            if review_type == "save":
                current_pm.status = ReviewDataStatus.SAVED.value
            elif review_type == "submit":
                current_pm.status = ReviewDataStatus.SUBMITTED.value
                current_pm.set_next_reviewer()
            elif review_type == "finished":
                self.is_finished = True
                self.date_finished = timezone.now()
                current_pm.status = ReviewDataStatus.FINISHED.value

            # update peere review manager related to this peer review entry
            current_pm.save()
            super().save(*args, **kwargs)
        else:
            raise ValidationError("Contributor and reviewer cannot be the same.")

    def set_version_of_metadata_for_review(self, table: str, *args, **kwargs):
        """
        Once the peer review is started, we save the current version of the
        oemetadata that is present on the table to the peer review instance
        to be able to do the review to a fixed state of the metadata.

        A started review means a reviewer saves / submits or finishes (in case
        the review is completed in one go) a review.

        Args:
            table (str): Table name

        Returns:
            State (tuple): Bool value that indicates weather there is already
            a version of oemetadata available for this review & readable
            status message.
        """
        table_oemetdata = Table.load(name=table).oemetadata

        if self.oemetadata is None:
            self.oemetadata = table_oemetdata
            super().save(*args, **kwargs)

            return (
                True,
                f"Set current version of table's: '{table}' " "oemetadata for review.",
            )

        return (
            False,
            f"This tables (name: {table}) review "
            "already got a version of oemetadata.",
        )

    def update_all_table_peer_reviews_after_table_moved(self, *args, topic, **kwargs):
        if isinstance(self.review, str):
            review_data = json.loads(self.review)
        else:
            review_data = self.review

        review_data["topic"] = topic

        self.review = review_data

        super().save(*args, **kwargs)

    @property
    def days_open(self):
        if self.date_started is None:
            return None  # Review has not started yet
        elif self.is_finished:
            return (self.date_finished - self.date_started).days  # Review has finished
        else:
            return (timezone.now() - self.date_started).days  # Review is still open


class ReviewDataStatus(Enum):
    SAVED = "SAVED"
    SUBMITTED = "SUBMITTED"
    FINISHED = "FINISHED"


class Reviewer(Enum):
    CONTRIBUTOR = "contributor"
    REVIEWER = "reviewer"


class PeerReviewManager(models.Model):
    """
    Manages peer review processes.

    This model handles the 1:n relation between table and open peer reviews.
    It tracks the days open for the peer review and its state.
    It determines who is next in the process between reviewer and contributor.
    It provides information about the previous and next review.
    It offers several methods that provide generic filters for the peer reviews.

    Attributes:
        opr (ForeignKey): The associated peer review.
        current_reviewer (CharField): The current reviewer.
        status (CharField): The current status of the review.
        is_open_since (CharField): How long the review has been open.
        prev_review (ForeignKey): The previous review in the process.
        next_review (ForeignKey): The next review in the process.
    """

    REVIEW_STATUS = [(status.value, status.name) for status in ReviewDataStatus]
    REVIEWER_CHOICES = [(choice.value, choice.name) for choice in Reviewer]

    opr = ForeignKey(
        PeerReview, on_delete=models.CASCADE, related_name="review_id", null=False
    )
    current_reviewer = models.CharField(
        choices=REVIEWER_CHOICES, max_length=20, default=Reviewer.REVIEWER.value
    )
    status = models.CharField(
        choices=REVIEW_STATUS, max_length=10, default=ReviewDataStatus.SAVED.value
    )
    is_open_since = models.CharField(null=True, max_length=10)
    prev_review = ForeignKey(
        PeerReview,
        on_delete=models.CASCADE,
        related_name="prev_review",
        null=True,
        default=None,
    )  # TODO: add logic
    next_review = ForeignKey(
        PeerReview,
        on_delete=models.CASCADE,
        related_name="next_review",
        null=True,
        default=None,
    )  # TODO: add logic

    @classmethod
    def load(cls, opr):
        """
        Load the peer review manager associated with the given peer review.

        Args:
            opr (PeerReview): The peer review.

        Returns:
            PeerReviewManager: The peer review manager.
        """
        peer_review_manager = PeerReviewManager.objects.get(opr=opr)
        return peer_review_manager

    def save(self, *args, **kwargs):
        """
        Override the save method to perform additional logic
        before saving the peer review manager.
        """
        # Set is_open_since field if it is None
        if self.is_open_since is None:
            # Get the associated PeerReview instance
            peer_review = self.opr

            # Set is_open_since based on the days_open property of the
            # PeerReview instance
            days_open = peer_review.days_open
            if days_open is not None:
                self.is_open_since = str(days_open)
        # Call the parent class's save method to save the PeerReviewManager instance
        super().save(*args, **kwargs)

    @classmethod
    def update_open_since(cls, opr=None, *args, **kwargs):
        """
        Update the "is_open_since" field of the peer review manager.

        Args:
            opr (PeerReview): The peer review.
            If None, use the peer review associated with the manager.

        """
        if opr is not None:
            peer_review = PeerReviewManager.objects.get(opr=opr)
        else:
            peer_review = cls.opr

        days_open = peer_review.opr.days_open
        peer_review.is_open_since = str(days_open)

        # Call the parent class's save method to save the PeerReviewManager instance
        peer_review.save(*args, **kwargs)

    def set_next_reviewer(self):
        """
        Set the order on which peer will be required to perform a action to
        continue with the process.
        """
        # TODO:check for user identifies as ...
        if self.current_reviewer == Reviewer.REVIEWER.value:
            self.current_reviewer = Reviewer.CONTRIBUTOR.value
        else:
            self.current_reviewer = Reviewer.REVIEWER.value
        self.save()

    def whos_turn(self):
        """
        Get the user and role (contributor or reviewer) whose turn it is.

        Returns:
            Tuple[str, User]: The role and user.
        """
        role, result = None, None
        peer_review = self.opr
        if self.current_reviewer == Reviewer.REVIEWER.value:
            role = Reviewer.REVIEWER.value
            result = peer_review.reviewer
        else:
            role = Reviewer.CONTRIBUTOR.value
            result = peer_review.contributor

        return role, result

    @staticmethod
    def load_contributor(table: str):
        """
        Get the contributor for the table a review is started.

        Args:
            table (str): Table name.

        Returns:
            User: The contributor user.
        """
        current_table = Table.load(name=table)
        try:
            table_holder = (
                current_table.userpermission_set.filter(table=current_table.pk)
                .first()
                .holder
            )
        except AttributeError:
            table_holder = None
        return table_holder

    @staticmethod
    def load_reviewer(table: str):
        """
        Get the reviewer for the table a review is started.

        Args:
            table (str): Table name.

        Returns:
            User: The reviewer user.
        """
        current_review = PeerReview.load(table=table)
        if current_review and hasattr(current_review, "reviewer"):
            return current_review.reviewer
        else:
            return None

    @staticmethod
    def filter_opr_by_reviewer(reviewer_user):
        """
        Filter peer reviews by reviewer, excluding those with current peer
        is contributor and the data status "SAVED" in the peer review manager.

        Args:
            reviewer_user (User): The reviewer user.

        Returns:
            QuerySet: Filtered peer reviews.
        """
        return PeerReview.objects.filter(reviewer=reviewer_user).exclude(
            review_id__current_reviewer=Reviewer.CONTRIBUTOR.value,
            review_id__status=ReviewDataStatus.SAVED.value,
        )

    @staticmethod
    def filter_latest_open_opr_by_reviewer(reviewer_user):
        """
        Get the last open peer review for the given contributor.

        Args:
            contributor_user (User): The contributor user.

        Returns:
            PeerReview: Last open peer review or None if not found.
        """
        try:
            return (
                PeerReview.objects.filter(reviewer=reviewer_user, is_finished=False)
                .exclude(
                    review_id__current_reviewer=Reviewer.CONTRIBUTOR.value,
                    review_id__status=ReviewDataStatus.SAVED.value,
                )
                .latest("date_started")
            )
        except PeerReview.DoesNotExist:
            return None

    @staticmethod
    def filter_opr_by_contributor(contributor_user):
        """
        Filter peer reviews by contributor, excluding those with current peer
        is reviewer and the data status "SAVED" in the peer review manager.

        Args:
            contributor_user (User): The contributor user.

        Returns:
            QuerySet: Filtered peer reviews.
        """

        return PeerReview.objects.filter(contributor=contributor_user).exclude(
            review_id__current_reviewer=Reviewer.REVIEWER.value,
            review_id__status=ReviewDataStatus.SAVED.value,
        )

    @staticmethod
    def filter_latest_open_opr_by_contributor(contributor_user):
        """
        Get the last open peer review for the given contributor.

        Args:
            contributor_user (User): The contributor user.

        Returns:
            PeerReview: Last open peer review or None if not found.
        """
        try:
            return (
                PeerReview.objects.filter(
                    contributor=contributor_user, is_finished=False
                )
                .exclude(
                    review_id__current_reviewer=Reviewer.REVIEWER.value,
                    review_id__status=ReviewDataStatus.SAVED.value,
                )
                .latest("date_started")
            )
        except PeerReview.DoesNotExist:
            return None

    @staticmethod
    def filter_opr_by_table(table: str) -> QuerySet[PeerReview]:
        """
        Filter peer reviews by table.

        Args:
            table (str): Table name.

        Returns:
            QuerySet: Filtered peer reviews.
        """
        return PeerReview.objects.filter(table=table)

    @staticmethod
    def get_opr_by_id(opr_id) -> PeerReview:
        return PeerReview.objects.get(id=opr_id)
