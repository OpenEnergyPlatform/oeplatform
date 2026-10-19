"""Only models and frameworks are factsheet types; any other is not found.

`/factsheets/<anything>s/` used to answer 200 with an empty list, so a
mistyped address looked like a real page with nothing on it. The addresses are
written out rather than reversed: an unknown type is exactly what a reverse
lookup may refuse to build.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from base.tests import TestViewsTestCase
from modelview.tests.corpus import seed_corpus

SHEETTYPES = ("model", "framework")


class SheetTypeTest(TestViewsTestCase):
    def setUp(self):
        self.client.force_login(self.user)
        self.pk = {
            t: seed_corpus(sheettype=t, factsheets=1, corrupted=0).factsheets[0].pk
            for t in SHEETTYPES
        }

    def addresses(self, sheettype, pk):
        base = f"/factsheets/{sheettype}s/"
        return {
            "list": base,
            "download": base + "download/",
            "payload": base + "payload/",
            "detail": f"{base}{pk}/",
            "edit": f"{base}{pk}/edit/",
            "add": base + "add/",
        }

    def test_models_and_frameworks_answer(self):
        for sheettype in SHEETTYPES:
            for route, url in self.addresses(sheettype, self.pk[sheettype]).items():
                with self.subTest(sheettype=sheettype, route=route):
                    self.assertEqual(self.client.get(url).status_code, 200)

    def test_an_unknown_type_is_not_found_on_every_route(self):
        # The pk of a factsheet that exists, so a 404 can only come from the
        # type and not from the record.
        pk = self.pk["model"]
        for sheettype in ("xyz", "scenario", "Model"):
            for route, url in self.addresses(sheettype, pk).items():
                with self.subTest(sheettype=sheettype, route=route):
                    self.assertEqual(self.client.get(url).status_code, 404)
