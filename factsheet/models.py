# SPDX-FileCopyrightText: 2025 Adel Memariani <adel.memariani@ovgu.de>
# SPDX-FileCopyrightText: 2025 Adel Memariani <memarian@haskell2go.iks.cs.ovgu.de>
# SPDX-FileCopyrightText: 2025 Adel Memariani <memariani.adel@gmail.com>
# SPDX-FileCopyrightText: 2025 Jonas Huber <38939526+jh-RLI@users.noreply.github.com>
# SPDX-FileCopyrightText: 2025 Jonas Huber <jonas.huber@rl-institut.de>
# SPDX-FileCopyrightText: 2025 jh-RLI <jonas.huber@rl-institut.de>
#
# SPDX-License-Identifier: MIT

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
