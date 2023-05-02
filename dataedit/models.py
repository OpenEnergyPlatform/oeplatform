from django.contrib.postgres.search import SearchVectorField
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
        unique_together = (("schema", "name"),)


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
    reviewer = ForeignKey('login.myuser', on_delete=models.CASCADE, related_name='reviewed_by', null=True)
    contributor = ForeignKey('login.myuser', on_delete=models.CASCADE, related_name='review_received', null=True)
    is_finished = BooleanField(null=False, default=False)
    date_started = DateTimeField(max_length=1000, null=False, default=timezone.now)
    date_submitted = DateTimeField(max_length=1000, null=True, default=None)
    date_finished = DateTimeField(max_length=1000, null=True, default=None)
    review = JSONField(null=True)
    
    # laden
    @classmethod
    def load(cls, schema, table):
        table_obj = PeerReview.objects.get(
            table=table, schema=schema
        )
        return table_obj
    
    # CAUTION unifinished work ... fix: includes all id´s and not just the related ones (reviews on same table) .. procudes false results
    def get_prev_and_next_reviews(self, schema, table):
        """
        Sets the prev_review and next_review fields based on the date_created field of the PeerReview objects
        associated with the same data_entry.
        """
        # Get all the PeerReview objects associated with the same schema and table name
        peer_reviews = PeerReview.objects.filter(table=table, schema=schema).order_by('date_started')
        # print(f'table: {table}')
        # print(f'peer_reviews: {peer_reviews}')
        # print(f'peer_reviews.count(): {peer_reviews.count()}')

        current_index = self.id
        # print(current_index)

        # Set the prev_review and next_review fields based on the index of the current PeerReview object
        # TODO: Just include related index range (just reviews related to table)
        prev_review = None
        next_review = None
        if current_index > 0:
            prev_review = PeerReview.objects.get(id=current_index - 1)
            
        if current_index < len(peer_reviews) - 1:
            next_review = PeerReview.objects.get(id=current_index + 1)

        return prev_review, next_review

    def save(self, *args, **kwargs):
        
        # Call the parent class's save method to save the PeerReview instance
        super().save(*args, **kwargs)

        # print(self.table, self.schema)
        prev_review, next_review = self.get_prev_and_next_reviews(self.schema, self.table)
        
        # print(prev_review, next_review)
        # Create a new PeerReviewManager entry for this PeerReview
        pm_new = PeerReviewManager(opr=self, prev_review=prev_review)
        pm_new.save() 

        if prev_review is not None:
            pm_prev = PeerReviewManager.objects.get(opr=prev_review)
            pm_prev.next_review = next_review
            pm_prev.save()

    @property
    def days_open(self):
        delta = timezone.now() - self.date_started
        return delta.days

from enum import Enum


class ReviewDataStatus(Enum):
    SAVED = 'SAVED'
    SUBMITTED = 'SUBMITTED'
    FINISHED = 'FINISHED'


class Reviewer(Enum):
    CONTRIBUTOR = "contributor"
    REVIEWER = "reviewer"


class PeerReviewManager(models.Model):
    REVIEWE_STATUS = [(status.value, status.name) for status in ReviewDataStatus]
    REVIEWER_CHOICES = [(choice.value, choice.name) for choice in Reviewer]

    opr = ForeignKey(PeerReview, on_delete=models.CASCADE, related_name='review_id', null=False)
    current_reviewer = models.CharField(choices=REVIEWER_CHOICES, max_length=20, default=Reviewer.CONTRIBUTOR.value)
    status = models.CharField(choices=REVIEWE_STATUS, max_length=10, default=ReviewDataStatus.SAVED.value)
    is_open_since = models.CharField(null=True, max_length=10)
    prev_review = ForeignKey(PeerReview, on_delete=models.CASCADE, related_name='prev_review', null=True, default=None)
    next_review = ForeignKey(PeerReview, on_delete=models.CASCADE, related_name='next_review', null=True, default=None)


