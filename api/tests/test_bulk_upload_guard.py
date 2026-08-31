"""Unit tests for the bulk upload guard module (issue #2362, slice 7).

The guard module is the one place tested below the HTTP seam, by
agreement: concurrent in-flight uploads and wall-clock transfer rates
cannot be exercised through Django's synchronous test client. One
HTTP-seam test in test_bulk_upload.py covers the wiring (429).

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.test import SimpleTestCase, override_settings

from api.bulk_upload_guard import (
    BulkUploadBusy,
    BulkUploadGuard,
    BulkUploadStalled,
    StallDetector,
)


class TestBulkUploadGuard(SimpleTestCase):
    def test_second_upload_by_same_user_rejected(self):
        guard = BulkUploadGuard()
        guard.acquire("user-1")
        with self.assertRaises(BulkUploadBusy):
            guard.acquire("user-1")

    @override_settings(BULK_UPLOAD_MAX_CONCURRENT=2)
    def test_global_cap_rejects_regardless_of_user(self):
        guard = BulkUploadGuard()
        guard.acquire("user-1")
        guard.acquire("user-2")
        with self.assertRaises(BulkUploadBusy):
            guard.acquire("user-3")

    def test_release_frees_the_slot(self):
        guard = BulkUploadGuard()
        guard.acquire("user-1")
        guard.release("user-1")
        guard.acquire("user-1")  # must not raise

    def test_slot_released_when_work_raises(self):
        guard = BulkUploadGuard()
        with self.assertRaises(ValueError):
            with guard.slot("user-1"):
                raise ValueError("boom")
        guard.acquire("user-1")  # must not raise: no leak

    @override_settings(BULK_UPLOAD_MAX_CONCURRENT=1)
    def test_no_leak_after_repeated_failures(self):
        guard = BulkUploadGuard()
        for _ in range(50):
            with self.assertRaises(RuntimeError):
                with guard.slot("user-1"):
                    raise RuntimeError("upload failed")
        with guard.slot("user-1"):
            pass  # capacity fully available after 50 failures


class TestStallDetector(SimpleTestCase):
    def make_detector(self, min_rate=100, grace=10):
        self.now = 0.0
        detector = StallDetector(
            min_bytes_per_second=min_rate,
            grace_seconds=grace,
            clock=lambda: self.now,
        )
        return detector

    def test_no_check_during_grace_period(self):
        detector = self.make_detector(min_rate=100, grace=10)
        self.now = 9.0
        detector.check(bytes_transferred=0)  # 0 B/s but within grace

    def test_slow_transfer_raises_after_grace(self):
        detector = self.make_detector(min_rate=100, grace=10)
        self.now = 20.0
        with self.assertRaises(BulkUploadStalled):
            detector.check(bytes_transferred=500)  # 25 B/s < 100 B/s

    def test_fast_transfer_passes_after_grace(self):
        detector = self.make_detector(min_rate=100, grace=10)
        self.now = 20.0
        detector.check(bytes_transferred=5000)  # 250 B/s >= 100 B/s

    def test_stalled_flag_set_on_abort(self):
        detector = self.make_detector(min_rate=100, grace=0)
        self.now = 10.0
        with self.assertRaises(BulkUploadStalled):
            detector.check(bytes_transferred=1)
        self.assertTrue(detector.stalled)
