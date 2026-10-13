"""A research project page that does not exist is a 404, not a 500.

The project pages are JSON files read by id; an id no file carries used to
index an empty list and take the request down with an `IndexError`.

Its partners are rendered one way (#2652): a partner with a logo used to be an
image 200 pixels wide and one without a loose line of text, each in a list of
its own. Now every partner is one tile of one grid, the about page's: its logo
where it has one, its name where it has none (open_MODEX has both kinds).

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from base.helper import get_json_content
from base.tests import TestViewsTestCase
from base.tests.html_tree import parse
from base.views import AboutPageView


class ProjectDetailTest(TestViewsTestCase):
    def test_a_known_project_answers(self):
        self.get("base:project_detail", kwargs={"project_id": "sirop"})

    def test_an_unknown_project_is_not_found(self):
        self.get(
            "base:project_detail",
            kwargs={"project_id": "no-such-project"},
            expect_status=404,
        )

    def test_every_partner_is_one_tile_of_one_grid(self):
        project = get_json_content(
            path=AboutPageView.projects_content_path, json_id="open_modex"
        )
        html = self.get(
            "base:project_detail", kwargs={"project_id": "open_modex"}
        ).content.decode()

        [grid] = parse(html).find("main").find_all("ul", "logo-grid")
        self.assertEqual(len(grid.elements), len(project["partners"]))
        for item, partner in zip(grid.elements, project["partners"]):
            with self.subTest(partner=partner["name"]):
                [tile] = item.elements
                self.assertTrue(tile.has_class("logo-tile"))
                if "logo" in partner:
                    self.assertEqual(tile.find("img").attrs["alt"], partner["name"])
                else:
                    self.assertEqual(tile.text(), partner["name"])
