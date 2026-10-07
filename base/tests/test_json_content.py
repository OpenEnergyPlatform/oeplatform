"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

The project pages are read from JSON files in a static directory
(`get_json_content`). In the docker dev setup that directory is bind-mounted from
the host, so it can hold files that are not project pages, such as macOS'
`.DS_Store`; those must not take the about page down.
"""  # noqa: 501

import json
import tempfile
from pathlib import Path

from django.test import SimpleTestCase

from base.helper import get_json_content


class JsonContentTest(SimpleTestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        for project in ("alpha", "beta"):
            (self.root / f"{project}.json").write_text(json.dumps({"id": project}))

    def test_reads_every_project_page(self):
        ids = sorted(p["id"] for p in get_json_content(str(self.root)))
        self.assertEqual(ids, ["alpha", "beta"])

    def test_files_that_are_not_json_are_skipped(self):
        (self.root / ".DS_Store").write_bytes(b"\x00\x01binary")
        (self.root / "README.md").write_text("# not a project")
        ids = sorted(p["id"] for p in get_json_content(str(self.root)))
        self.assertEqual(ids, ["alpha", "beta"])

    def test_one_project_by_id(self):
        (self.root / ".DS_Store").write_bytes(b"\x00\x01binary")
        self.assertEqual(
            get_json_content(str(self.root), json_id="beta"), {"id": "beta"}
        )

    def test_an_unknown_id_is_none(self):
        self.assertIsNone(get_json_content(str(self.root), json_id="gamma"))
