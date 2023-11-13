from django.db import models
from django.utils import timezone

from django.db.models import (
    CharField,
    DateTimeField,
    ForeignKey,
    JSONField,
)


class OEKG_Modifications(models.Model):
    bundle_id = CharField(max_length=400, default="none")
    old_state = JSONField()
    new_state = JSONField()
    user = ForeignKey("login.myuser", on_delete=models.CASCADE, null=True)
    timestamp = DateTimeField(default=timezone.now)


class ScenarioBundleAccessControl(models.Model):
    owner_user = models.ForeignKey(
        "login.myuser",
        on_delete=models.CASCADE,
        related_name="scenario_bundle_creator",
        null=False,
    )
    uid = models.TextField()
