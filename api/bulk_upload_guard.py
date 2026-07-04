"""Concurrency and stall guards for Bulk Upload (issue #2362).

Bulk uploads run synchronously on WSGI workers, so the platform is
protected by guards rather than infrastructure: at most one running
upload per user plus a small global cap (rejected with 429), and a
minimum-transfer-rate detector that aborts trickling clients so a
worker and an open transaction cannot be pinned indefinitely.

The guard state is in-process. That matches a single-process WSGI
deployment; a multi-worker deployment bounds concurrency per worker
process, which still caps the damage (workers x limit).

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import threading
from contextlib import contextmanager

from django.conf import settings

RETRY_AFTER_SECONDS = 60


class BulkUploadBusy(Exception):
    """Raised when no bulk upload slot is available (HTTP 429)."""


class BulkUploadGuard:
    """At most one running bulk upload per user, plus a global cap.

    The global limit is read from settings at acquire time
    (BULK_UPLOAD_MAX_CONCURRENT), so deployments and tests can tune it
    without touching the singleton.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._active_users = set()

    def acquire(self, user_key) -> None:
        limit = getattr(settings, "BULK_UPLOAD_MAX_CONCURRENT", 2)
        with self._lock:
            if user_key in self._active_users:
                raise BulkUploadBusy(
                    "Another bulk upload by this user is already running. "
                    "Wait for it to finish and retry."
                )
            if len(self._active_users) >= limit:
                raise BulkUploadBusy(
                    "Bulk upload capacity is currently full. Retry later."
                )
            self._active_users.add(user_key)

    def release(self, user_key) -> None:
        with self._lock:
            self._active_users.discard(user_key)

    @contextmanager
    def slot(self, user_key):
        self.acquire(user_key)
        try:
            yield
        finally:
            self.release(user_key)


# module-level singleton: one guard per worker process
guard = BulkUploadGuard()
