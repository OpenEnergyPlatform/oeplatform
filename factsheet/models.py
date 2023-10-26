from django.db import models
from django.utils import timezone


class HistoryOfOEKG(models.Model):
    triple_subject = models.TextField()
    triple_predicate = models.TextField()
    triple_object = models.TextField()
    type_of_action = models.CharField(max_length=100)
    user = models.CharField(max_length=200)
    timestamp = models.DateTimeField(default=timezone.now)


class ScenarioBundleAccessControl(models.Model):
    owner_user = models.ForeignKey(
        "login.myuser",
        on_delete=models.CASCADE,
        related_name="scenario_bundle_creator",
        null=False,
    )
    uid = models.TextField()
