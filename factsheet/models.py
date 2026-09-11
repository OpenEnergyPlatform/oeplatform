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
from django.db.models import (
    CharField,
    DateTimeField,
    ForeignKey,
    IntegerField,
    JSONField,
)
from django.utils import timezone

# What wrote a row. The table predates the REST API, and rows from before it
# are kept exactly as they were rather than migrated -- so a reader has to be
# able to tell the two apart, and `verb` is what tells it: only the API sets it.
PRE_API_ERA = "pre_api"
API_ERA = "api"

# What an API row puts in the legacy payload columns. Empty, not null: the
# user interface feeds those two straight into a text-diff component that
# splits them, and one null would throw out of a page that renders every row.
EMPTY_LEGACY_PAYLOAD = ""


class OEKG_Modifications(models.Model):
    """One recorded change to a scenario bundle.

    **Extended, not replaced.** The REST API writes here rather than to a table
    of its own, because two histories split by which client did the writing is
    the completeness problem this model already has, in a new form.

    That leaves two generations of row in one table, and they are deliberately
    not reconciled:

    - **Pre-API rows** carry their changed triples in ``old_state`` /
      ``new_state`` as JSON-LD **strings inside a JSON column** -- double
      encoded, because ``Graph.serialize()`` returns a ``str``. The user
      interface's diff viewer depends on that, so rewriting them in place would
      break it while editing the one table whose value is being an unaltered
      record.
    - **API rows** carry theirs in ``removed`` / ``added`` as real structured
      JSON, and fill the columns that make the table answerable: which
      operation, which resource, and which version it produced. A timestamp
      alone cannot answer "which change produced this state". They leave the
      legacy columns **empty rather than null**: the diff viewer hands them
      straight to a component that splits them, so a null there would throw and
      take the whole page down with it -- it renders every row in one map.

    The diff is stored **losslessly and untranslated** -- no field names, no
    serializer vocabulary -- so a later shape change never re-interprets an old
    row.
    """

    bundle_id = CharField(max_length=400, default="none", db_index=True)
    old_state = JSONField(null=True, blank=True)
    new_state = JSONField(null=True, blank=True)
    user = ForeignKey("login.myuser", on_delete=models.CASCADE, null=True)
    timestamp = DateTimeField(default=timezone.now)

    # Set by the API and by nothing else, which is what makes `era` decidable.
    verb = CharField(max_length=10, null=True, blank=True)
    resource_type = CharField(max_length=400, null=True, blank=True)
    resource_uuid = CharField(max_length=400, null=True, blank=True)
    version_before = IntegerField(null=True, blank=True)
    version_after = IntegerField(null=True, blank=True)
    removed = JSONField(null=True, blank=True)
    added = JSONField(null=True, blank=True)

    @property
    def era(self) -> str:
        """Which generation of writer produced this row."""
        return API_ERA if self.verb else PRE_API_ERA


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

    @classmethod
    def users_for_bundle(cls, uid):
        # all relations for the bundle
        return cls.objects.select_related("owner_user").filter(bundle_id=uid)

    @classmethod
    def user_has_access(cls, user, uid):
        return cls.objects.filter(owner_user=user, bundle_id=uid).exists()
