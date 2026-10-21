"""The generic 400 must be traceable from the log alone.

`{"reason": "Invalid request"}` says nothing, deliberately -- the body must
not leak internals. That makes the log line the only account of what happened,
and it used to carry `str(exc)` and nothing else: no exception type, no
traceback, no path. Diagnosing #2488 from production logs was not possible,
which is most of why it survived.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import json

from django.test import RequestFactory, SimpleTestCase

from api.helper import api_exception


class CatchAllLogsTheCauseTest(SimpleTestCase):

    def _raise_through_the_handler(self, exc):
        @api_exception
        def view(request):
            raise exc

        request = RequestFactory().post("/api/v0/advanced/search")
        with self.assertLogs("oeplatform", level="ERROR") as captured:
            response = view(request)
        return response, captured.records[0]

    def test_the_response_stays_generic(self):
        response, _ = self._raise_through_the_handler(RuntimeError("secret internals"))

        self.assertEqual(400, response.status_code)
        self.assertEqual({"reason": "Invalid request"}, json.loads(response.content))
        self.assertNotIn(b"secret internals", response.content)

    def test_the_log_line_names_the_type_the_path_and_the_traceback(self):
        _, record = self._raise_through_the_handler(RuntimeError("the real cause"))

        message = record.getMessage()
        self.assertIn("RuntimeError", message)
        self.assertIn("/api/v0/advanced/search", message)
        self.assertIn("the real cause", message)
        self.assertIsNotNone(
            record.exc_info, "logged without a traceback, so the raising line is lost"
        )

    def test_a_missing_request_does_not_break_the_logging(self):
        # the decorator also wraps plain functions, and a log call that raises
        # would turn a 400 into a 500 at the worst possible moment
        @api_exception
        def view():
            raise RuntimeError("boom")

        with self.assertLogs("oeplatform", level="ERROR") as captured:
            response = view()

        self.assertEqual(400, response.status_code)
        self.assertIn("<unknown path>", captured.records[0].getMessage())
