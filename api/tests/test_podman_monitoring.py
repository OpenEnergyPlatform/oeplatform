"""The monitoring stack under podman/monitoring/ (#2412).

Two promises it makes are easy to break without noticing: the usage figures
count people, not the monitoring's own probes or crawlers, and the stack runs
pinned and reachable from the host only.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import pathlib
import re
import subprocess

from django.test import SimpleTestCase

MONITORING = pathlib.Path("podman/monitoring")
USAGE = MONITORING / "usage"


class UsageFiguresTest(SimpleTestCase):
    def test_the_test_log_gives_the_expected_figures(self):
        # The log holds a probe, a crawler, empty bodies ("-"), both table
        # routes, a failed download, a crafted format and an error-log line.
        counted = subprocess.run(
            ["bash", str(USAGE / "oep-usage.sh"), "count"],
            stdin=(USAGE / "testdata/access.log").open(),
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual((USAGE / "testdata/expected.prom").read_text(), counted.stdout)


class MonitoringUnitsTest(SimpleTestCase):
    def setUp(self):
        self.units = sorted((MONITORING / "quadlets").glob("*.container"))
        self.assertTrue(self.units, "no monitoring units found")

    def test_every_image_is_pinned(self):
        for unit in self.units:
            image = re.search(r"^Image=(\S+)$", unit.read_text(), re.M).group(1)
            with self.subTest(unit=unit.name):
                self.assertRegex(image, r":v?\d+\.\d+\.\d+$")

    def test_nothing_is_published_beyond_the_host(self):
        for unit in self.units:
            for port in re.findall(r"^PublishPort=(\S+)$", unit.read_text(), re.M):
                with self.subTest(unit=unit.name):
                    self.assertTrue(port.startswith("127.0.0.1:"), port)
