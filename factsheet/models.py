"""
SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.db import models
from django.db.models import CharField, DateTimeField, ForeignKey, JSONField
from django.utils import timezone


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
    bundle_id = CharField(max_length=400, default="none")

    @classmethod
    def load_by_uid(cls, uid):
        return ScenarioBundleAccessControl.objects.filter(bundle_id=uid).first()
