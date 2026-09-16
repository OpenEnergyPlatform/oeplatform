"""The names the reference's groups carry, checked in the committed document.

``test_openapi_schema`` keeps the artifact equal to what the code produces and
``test_scenario_bundle_description`` asserts what one half of it says. These
are about how the whole of it is *navigated*: Swagger draws one accordion per
tag and orders them by the document's own tag list, so a tag is both what a
reader scans and what a prose page links to.

Left alone the generator derives a tag from the first path segment, which is
how the document came to carry thirteen groups nobody chose -- among them
``scenario-bundle`` and ``scenario-bundles``, a single legacy route beside the
entire REST API replacing it, rendered as adjacent accordions one letter apart.
The rules below are what stops that returning, and every one of them reads the
**committed** document rather than the annotations: an assertion about
``extend_schema`` would pass while the generator quietly dropped the operation
it decorated.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: E501

import re
from pathlib import Path

import yaml
from django.test import SimpleTestCase

from api.api_tags import (
    SCENARIO_BUNDLES,
    SCENARIO_BUNDLES_LEGACY,
    TABLES,
    TABLES_LEGACY,
    TAGS,
)
from api.tests.test_openapi_schema import ARTIFACT, LEGACY_TABLE_PATH, REGENERATE

#: The superseded groups, each with the group that replaced it. A description
#: here has to say *superseded* and name that replacement, because the document
#: is where a client author is standing when the question occurs to them.
SUPERSEDED = {SCENARIO_BUNDLES_LEGACY: SCENARIO_BUNDLES, TABLES_LEGACY: TABLES}

#: What a tag name may be made of. Swagger's anchor for a group is built from
#: its name, so a page linking to `#/Tables` needs the name to survive being
#: put in a URL predictably. Letters, digits, spaces and the three punctuation
#: marks the convention uses are enough for that.
STABLE_ANCHOR = re.compile(r"^[A-Za-z0-9 :()\-]+$")


#: The page that renders the document. It cites a group by name to show that a
#: section can be linked to, and a name it cites has to be one that exists --
#: the failure a prose citation has is that it rots quietly.
REFERENCE_PAGE = Path(ARTIFACT.parent, "api-reference.md")


def _document():
    return yaml.safe_load(ARTIFACT.read_text(encoding="utf-8"))


def _operations(document):
    for path, methods in document["paths"].items():
        for method, operation in methods.items():
            if isinstance(operation, dict) and "responses" in operation:
                yield path, method, operation


class TagSetTest(SimpleTestCase):
    """The groups a reader navigates by, and the order they are read in."""

    def setUp(self):
        self.document = _document()
        self.declared = self.document.get("tags", [])
        self.names = [tag["name"] for tag in self.declared]
        self.operations = list(_operations(self.document))
        self.assertTrue(self.operations, "no operations described")

    def advice(self, complaint):
        return f"{complaint}\n    {REGENERATE}"

    def test_the_document_lists_the_groups_this_project_named(self):
        """The list in the document is the list in ``api.api_tags``.

        Not a restatement of it: the setting is read at settings-import time
        and the artifact is generated from a separate process, so this is the
        step where a tag added to the module but never regenerated shows up.
        """
        self.assertEqual(
            self.declared,
            TAGS,
            self.advice("the document's tag list is not the one api.api_tags declares"),
        )

    def test_no_operation_takes_a_group_nobody_named(self):
        """A tag outside the list is one the generator derived from a path.

        It is the failure this whole module exists for, and it arrives by
        omission: a view added without a tag is described perfectly well and
        lands in an accordion named after its first path segment.
        """
        for path, method, operation in self.operations:
            for tag in operation.get("tags", []):
                self.assertIn(
                    tag,
                    self.names,
                    self.advice(
                        f"{method.upper()} {path} is in the group {tag!r}, which "
                        "is not declared -- annotate the view with a tag from "
                        "api.api_tags"
                    ),
                )

    def test_every_operation_is_in_exactly_one_group(self):
        """Two groups would put one operation in two accordions."""
        for path, method, operation in self.operations:
            self.assertEqual(
                len(operation.get("tags", [])),
                1,
                self.advice(f"{method.upper()} {path} does not name one group"),
            )

    def test_no_group_is_empty(self):
        """A named group with no operations is an accordion that opens onto
        nothing -- which is what a group renamed in one place looks like."""
        used = {tag for _, _, op in self.operations for tag in op.get("tags", [])}
        for name in self.names:
            self.assertIn(name, used, f"the group {name!r} describes no operation")

    def test_every_group_says_what_it_holds(self):
        for tag in self.declared:
            self.assertTrue(
                tag.get("description", "").strip(),
                f"the group {tag['name']!r} carries no description",
            )

    def test_every_superseded_group_names_what_replaced_it(self):
        """Saying *superseded* without naming the replacement leaves a reader
        knowing not to use this and not knowing what to use."""
        for name, replacement in SUPERSEDED.items():
            description = next(
                t["description"] for t in self.declared if t["name"] == name
            )
            self.assertIn(
                "uperseded", description, f"{name!r} does not say it is superseded"
            )
            self.assertIn(
                replacement,
                description,
                f"{name!r} does not name {replacement!r} as its replacement",
            )

    def test_the_superseded_groups_are_read_last(self):
        """Order is the other half of saying it: a superseded group sitting
        above the one that replaced it is an invitation to build against it."""
        positions = [self.names.index(name) for name in SUPERSEDED]
        self.assertEqual(
            sorted(positions),
            list(range(len(self.names) - len(SUPERSEDED), len(self.names))),
            "the superseded groups are not the last entries in the tag list",
        )

    def test_the_reference_page_links_into_a_group_that_exists(self):
        """The page beside the document cites a section by name.

        Swagger builds a section's anchor from its name, so the citation is
        also the demonstration that one can be linked to. If a group is
        renamed, this is what notices that the page still points at the old
        name.
        """
        page = REFERENCE_PAGE.read_text(encoding="utf-8")
        cited = re.findall(r"\]\(#/([^)]+)\)", page)
        self.assertTrue(cited, f"{REFERENCE_PAGE.name} links into no section")
        for anchor in cited:
            self.assertIn(
                anchor.replace("%20", " "),
                self.names,
                f"{REFERENCE_PAGE.name} links to the section {anchor!r}, which "
                "the description does not declare",
            )

    def test_every_group_name_makes_a_stable_anchor(self):
        for name in self.names:
            self.assertRegex(
                name,
                STABLE_ANCHOR,
                f"the group {name!r} carries characters an anchor cannot be "
                "linked to predictably",
            )


class LegacyTableGroupTest(SimpleTestCase):
    """The older table addresses, which no annotation on a view can reach.

    One view serves both spellings, so *everything* that distinguishes them --
    the callable path, the deprecation, the group and the operation id -- is
    set by the postprocessing hook. These check its work where it lands.
    """

    def setUp(self):
        self.document = _document()
        self.legacy = [
            (path, method, operation)
            for path, method, operation in _operations(self.document)
            if path.startswith(LEGACY_TABLE_PATH)
        ]
        self.assertTrue(self.legacy, "no legacy table addresses in the description")

    def test_every_legacy_address_is_in_the_legacy_group(self):
        for path, method, operation in self.legacy:
            self.assertEqual(
                operation.get("tags"),
                [TABLES_LEGACY],
                f"{method.upper()} {path} is not grouped as a legacy address",
            )

    def test_no_canonical_address_is_in_the_legacy_group(self):
        """The group is the older spelling, not the endpoints themselves."""
        for path, method, operation in _operations(self.document):
            if path.startswith(LEGACY_TABLE_PATH):
                continue
            self.assertNotIn(
                TABLES_LEGACY,
                operation.get("tags", []),
                f"{method.upper()} {path} is not a legacy address",
            )

    def test_no_operation_id_carries_the_route_pattern(self):
        """An id is what a generated client turns into a method name.

        These were generated from the uncaptured group in the route, so they
        arrived as `schema_[\\w\\d_]_tables_retrieve` -- a name no language
        accepts. The check is over the whole document rather than the legacy
        paths alone, because the cause is a kind of route rather than these
        routes.
        """
        for path, method, operation in _operations(self.document):
            operation_id = operation.get("operationId", "")
            self.assertRegex(
                operation_id,
                r"^[A-Za-z0-9_]+$",
                f"{method.upper()} {path} has the operation id {operation_id!r}",
            )
