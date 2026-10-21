"""The podman stack's Apache config must agree with the connection pool.

Two facts have to stay true together, and they live in different files that
nobody reads at the same time:

- every mod_wsgi process carries its own SQLAlchemy pool, whose ceiling is
  `OEDB_POOL_SIZE + OEDB_MAX_OVERFLOW` (oedb/connection.py), and
- the database's ceiling is per cluster, not per process.

Production reached its connection ceiling in September 2026 because a process
count was raised 4 -> 12 in an Apache config no repository contained, and
nothing recomputed the pool (issue #2495). The podman stack is where that
config becomes reviewable, so the arithmetic is checked here rather than
written in a comment somebody has to remember to re-do.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import pathlib
import re

from django.test import SimpleTestCase

from oedb.connection import OEDB_MAX_OVERFLOW, OEDB_POOL_SIZE

CONFIG = pathlib.Path("podman/apache2.conf")

# max_connections 255 minus superuser_reserved_connections 8, measured on the
# production OEDB 2026-09-21. A smaller database needs a smaller stack.
USABLE_CONNECTION_SLOTS = 247

STATEFUL_LOCATION = "/api/v0/advanced"


def daemon_groups(text):
    """{group name: process count} for every WSGIDaemonProcess, continuations
    included -- the directive is line-continued and `processes=` lives on the
    continuation, which is the whole point of reading it."""
    joined = re.sub(r"\\\s*\n\s*", " ", text)
    groups = {}
    for line in joined.splitlines():
        line = line.strip()
        if not line.startswith("WSGIDaemonProcess"):
            continue
        name = line.split()[1]
        match = re.search(r"\bprocesses=(\d+)", line)
        # mod_wsgi's default when processes= is absent is 1
        groups[name] = int(match.group(1)) if match else 1
    return groups


def directives(text):
    """The config with comment lines removed, for checks that must not match
    the prose explaining why something is absent."""
    return "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith("#")
    )


def location_groups(text):
    """{location path: process group} for every <Location> that names one."""
    found = {}
    for block in re.finditer(r"<Location\s+([^>]+)>(.*?)</Location>", text, re.DOTALL):
        path, body = block.group(1).strip(), block.group(2)
        match = re.search(r"WSGIProcessGroup\s+(\S+)", body)
        if match:
            found[path] = match.group(1)
    return found


class PodmanApacheConfigTest(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.text = CONFIG.read_text()

    def test_the_config_is_in_the_repository(self):
        # it was gitignored by an unanchored `apache*` and never committed,
        # while podman/Dockerfile went on COPYing it
        self.assertTrue(
            CONFIG.is_file(), f"{CONFIG} is missing; the image build COPYs it"
        )

    def test_the_processes_cannot_exhaust_the_database(self):
        per_process = OEDB_POOL_SIZE + OEDB_MAX_OVERFLOW
        total = sum(daemon_groups(self.text).values())
        worst_case = total * per_process

        self.assertLess(
            worst_case,
            USABLE_CONNECTION_SLOTS,
            f"{total} processes x {per_process} connections = {worst_case}, over the "
            f"{USABLE_CONNECTION_SLOTS} a client may hold. Raise the pool's ceiling "
            f"with the process count, or lower the process count.",
        )

    def test_the_stateful_api_has_its_own_single_process_group(self):
        # api/sessions.py keeps connections in a module-global dict and
        # mod_wsgi has no session affinity, so more than one process here
        # silently hands a client somebody else's interpreter
        group = location_groups(self.text).get(STATEFUL_LOCATION)
        self.assertIsNotNone(
            group, f"no <Location {STATEFUL_LOCATION}> naming a process group"
        )
        self.assertEqual(
            1,
            daemon_groups(self.text).get(group),
            f"the group serving {STATEFUL_LOCATION} must run processes=1",
        )

    def test_the_default_group_is_not_the_stateful_one(self):
        # the split is only a split if the two groups differ
        groups = location_groups(self.text)
        self.assertIn(
            STATEFUL_LOCATION, groups, f"no <Location {STATEFUL_LOCATION}> at all"
        )
        default = re.search(r"^\s*WSGIProcessGroup\s+(\S+)", self.text, re.M)
        self.assertNotEqual(default.group(1), groups[STATEFUL_LOCATION])

    def test_a_long_upload_is_not_cut_off_mid_request(self):
        # request-timeout restarts the daemon mid-request and Bulk Upload is
        # synchronous by design (ADR 0002). Checked against directives only:
        # the config explains in prose why it is absent, and a bare substring
        # search matches that explanation.
        self.assertNotIn("request-timeout=", directives(self.text))


# The access log's start is a contract with whatever reads it (the usage
# figures of #2412 parse it as Common Log Format), so new fields go at the end.
COMMON_LOG_FORMAT = r"%h %l %u %t \"%r\" %>s %b"


def access_log_format(text):
    """The format string the access log is written with, or None."""
    custom = re.search(r"^\s*CustomLog\s+(\S+)\s+(\S+)", directives(text), re.M)
    if not custom:
        return None
    nickname = custom.group(2)
    for match in re.finditer(
        r'^\s*LogFormat\s+"((?:[^"\\]|\\.)*)"\s+(\S+)', text, re.M
    ):
        if match.group(2) == nickname:
            return match.group(1)
    return None


class PodmanAccessLogTest(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.text = CONFIG.read_text()
        # "" rather than None, so a missing format fails each assertion
        # with its own message instead of an AttributeError
        cls.format = access_log_format(cls.text) or ""

    def test_the_access_log_goes_to_stdout_in_a_named_format(self):
        # TransferLog would fall back to plain CLF and silently drop the fields
        # below; stdout is what journald collects from the container
        self.assertNotIn("TransferLog", directives(self.text))
        self.assertRegex(directives(self.text), r"(?m)^\s*CustomLog\s+/dev/stdout\s")
        self.assertTrue(self.format, "CustomLog names no LogFormat defined here")

    def test_the_line_still_starts_as_common_log_format(self):
        self.assertTrue(
            self.format.startswith(COMMON_LOG_FORMAT),
            f"{self.format!r} must start with {COMMON_LOG_FORMAT!r}; "
            "parsers of the access log read it as CLF",
        )

    def test_duration_and_user_agent_are_recorded(self):
        # the duration is the last field, so a reader takes it as $NF
        self.assertTrue(self.format.endswith("%D"), self.format)
        self.assertIn(r"\"%{User-Agent}i\"", self.format)

    def test_no_credentials_or_cookies_are_logged(self):
        for header in ("Cookie", "Authorization", "Referer"):
            self.assertNotIn(f"%{{{header}}}i", self.format)
