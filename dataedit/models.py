from enum import Enum

from django.contrib.postgres.search import SearchVectorField
from django.core.exceptions import ValidationError
from django.db import models

# django.contrib.postgres.fields.JSONField is deprecated.
from django.db.models import (
    BooleanField,
    CharField,
    DateTimeField,
    ForeignKey,
    IntegerField,
    JSONField,
)
from django.utils import timezone

# Create your models here.


class TableRevision(models.Model):
    table = CharField(max_length=1000, null=False)
    schema = CharField(max_length=1000, null=False)
    date = DateTimeField(max_length=1000, null=False, default=timezone.now)
    created = DateTimeField(null=False, default=timezone.now)
    path = CharField(max_length=1000, null=False)
    size = IntegerField(null=False)
    last_accessed = DateTimeField(null=False, default=timezone.now)


class Tagable(models.Model):
    name = CharField(max_length=1000, null=False)

    class Meta:
        abstract = True


class Schema(Tagable):
    class Meta:
        unique_together = (("name"),)


class Table(Tagable):
    schema = models.ForeignKey(Schema, on_delete=models.CASCADE)
    search = SearchVectorField(default="")
    # Add field to store oemetadata related to the table and avoide performance issues
    # due to oem string (json) parsing like when reading the oem form comment on table
    oemetadata = JSONField(null=True)
    is_reviewed = BooleanField(default=False, null=False)

    @classmethod
    def load(cls, schema, table):
        table_obj = Table.objects.get(
            name=table, schema=Schema.objects.get_or_create(name=schema)[0]
        )

        return table_obj

    def set_is_reviewed(self):
        self.is_reviewed = True
        self.save()

    class Meta:
        unique_together = (("name",),)


class View(models.Model):
    name = CharField(max_length=50, null=False)
    table = CharField(max_length=1000, null=False)
    schema = CharField(max_length=1000, null=False)
    VIEW_TYPES = (("table", "table"), ("map", "map"), ("graph", "graph"))
    type = CharField(max_length=10, null=False, choices=VIEW_TYPES)
    options = JSONField(null=False, default=dict)
    is_default = BooleanField(default=False)

    def __str__(self):
        return '{}/{}--"{}"({})'.format(
            self.schema, self.table, self.name, self.type.upper()
        )


class Filter(models.Model):
    column = CharField(max_length=100, null=False)
    FILTER_TYPES = (("equal", "equal"), ("range", "range"))
    type = CharField(max_length=10, null=False, choices=FILTER_TYPES)
    value = JSONField(null=False)
    view = ForeignKey(View, on_delete=models.CASCADE, related_name="filter")


class PeerReview(models.Model):
    table = CharField(max_length=1000, null=False)
    schema = CharField(max_length=1000, null=False)
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

    # laden
    @classmethod
    def load(cls, schema, table):
        """
        Load the current reviewer user.
        The current review is review is determened by the latest date started.

        Args:
            schema (string): Schema name
            table (string): Table name

        Returns:
            opr (PeerReview): PeerReview object related to the latest date started.
        """
        opr = (
            PeerReview.objects.filter(table=table, schema=schema)
            .order_by("-date_started")
            .first()
        )
        return opr

    # TODO: CAUTION unifinished work ... fix: includes all id´s and not just the
    # related ones (reviews on same table) .. procudes false results
    def get_prev_and_next_reviews(self, schema, table):
        """
        Sets the prev_review and next_review fields based on the date_started field of
        the PeerReview objects associated with the same table.
        """
        # Get all the PeerReview objects associated with the same schema and table name
        peer_reviews = PeerReview.objects.filter(table=table, schema=schema).order_by(
            "date_started"
        )

        current_index = None
        for index, review in enumerate(peer_reviews):
            if review.id == self.id:
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
        if not self.contributor == self.reviewer:
            # Call the parent class's save method to save the PeerReview instance
            super().save(*args, **kwargs)

            # TODO: This causes errors if review list ist empty
            # prev_review, next_review = self.get_prev_and_next_reviews(
            #   self.schema, self.table
            # )

            # print(prev_review.id, next_review)
            # print(prev_review, next_review)
            # Create a new PeerReviewManager entry for this PeerReview
            # pm_new = PeerReviewManager(opr=self, prev_review=prev_review)

            if review_type == "save":
                # Handle save status
                pm_new = PeerReviewManager(
                    opr=self, status=ReviewDataStatus.SAVED.value
                )

            elif review_type == "submit":
                # Handle submit status
                pm_new = PeerReviewManager(
                    opr=self, status=ReviewDataStatus.SUBMITTED.value
                )
                pm_new.set_next_reviewer()

            elif review_type == "finished":
                # TODO: fails if the review is completed without submitting
                # (finish in one run)
                pm_new = PeerReviewManager(
                    opr=self, status=ReviewDataStatus.FINISHED.value
                )
                self.is_finished = True
                self.date_finished = timezone.now()
                # Call the parent class's save method to save the PeerReview instance
                super().save(*args, **kwargs)

            pm_new.save()

            # if prev_review is not None:
            #     pm_prev = PeerReviewManager.objects.get(opr=prev_review)
            #     pm_prev.next_review = next_review
            #     pm_prev.save()
        else:
            raise ValidationError("Contributor and reviewer cannot be the same.")

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
    Model representing the manager of a peer review.

        - It handles the 1:n relation between table and open peer reviews.
        - It tracks the days open for the peer review.
        - It tracks the state of the peer review as it can be SAVED, SUBMITTED (stated)
          or FINISHED.
        - It determines who is next in the process between reviewer and contributor.
        - it provides information about the previous and next review.
        - It provides several methods that provide generic filters for the peerReviews
            (like filter by table, contributor ...)
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
        # print(self.is_open_since, self.status)
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
        Set the order on which peer will be requred to perform a action to
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
    def load_contributor(schema, table):
        """
        Get the contributor for the table a review is started.

        Args:
            schema (str): Schema name.
            table (str): Table name.

        Returns:
            User: The contributor user.
        """
        current_table = Table.load(schema=schema, table=table)
        try:
            table_holder = (
                current_table.userpermission_set.filter(table=current_table.id)
                .first()
                .holder
            )
        except AttributeError:
            table_holder = None
        return table_holder

    @staticmethod
    def load_reviewer(schema, table):
        """
            Get the reviewer for the table a review is started.
        .
            Args:
                schema (str): Schema name.
                table (str): Table name.

            Returns:
                User: The reviewer user.
        """
        current_review = PeerReview.load(schema=schema, table=table)
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
    def filter_opr_by_table(schema, table):
        """
        Filter peer reviews by schema and table.

        Args:
            schema (str): Schema name.
            table (str): Table name.

        Returns:
            QuerySet: Filtered peer reviews.
        """
        return PeerReview.objects.filter(schema=schema, table=table)

    def filter_opr_by_id(opr_id):
        return PeerReview.objects.filter(id=opr_id).first()
