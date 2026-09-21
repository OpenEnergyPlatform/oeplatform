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

import ast
import re
from pathlib import Path

from django.test import SimpleTestCase

import api.api_tags
from api.api_tags import (
    SCENARIO_BUNDLES,
    SCENARIO_BUNDLES_LEGACY,
    TABLES,
    TABLES_LEGACY,
    TAGS,
)
from api.tests.test_openapi_schema import (
    ARTIFACT,
    LEGACY_TABLE_PATH,
    REGENERATE,
    committed_document,
    operations,
)
from oeplatform.settings import BASE_DIR

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
#: section can be linked to, and carries the worked example other pages copy.
REFERENCE_PAGE = Path(ARTIFACT.parent, "api-reference.md")

#: Every page of the documentation, because a citation rots quietly wherever it
#: was written. Checking only the reference left the copies unwatched: the two
#: pages that cite the superseded group both cite it from somewhere else, so
#: renaming that group went red in one place and silently dead in two.
DOCUMENTATION = Path(BASE_DIR, "docs")

#: A citation of a section, as a page writes one. Parentheses are part of a
#: group's name, so they are matched only in balanced pairs -- a name followed
#: by the closing bracket of the Markdown link it sits in would otherwise be
#: read as ending in one, and no declared group ends in ")".
CITATION = re.compile(r"#/((?:[A-Za-z0-9\-]|%20|\((?:[A-Za-z0-9\-]|%20)*\))+)")


class TagSetTest(SimpleTestCase):
    """The groups a reader navigates by, and the order they are read in."""

    def setUp(self):
        self.document = committed_document()
        self.declared = self.document.get("tags", [])
        self.names = [tag["name"] for tag in self.declared]
        self.operations = list(operations(self.document))
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

    def citations(self):
        """Every (page, section) a documentation page links to."""
        return [
            (page, anchor.replace("%20", " "))
            for page in sorted(DOCUMENTATION.rglob("*.md"))
            for anchor in CITATION.findall(page.read_text(encoding="utf-8"))
        ]

    def test_the_reference_page_shows_how_to_link_into_a_group(self):
        """The page beside the document cites a section by name.

        In the form another page has to use: the reference is rendered inside
        a page, so a section is reached by opening that page at the section's
        address rather than by an anchor of the surrounding document. This is
        the worked example the other pages copy, so it has to stay on the page
        that explains the form.
        """
        page = REFERENCE_PAGE.read_text(encoding="utf-8")
        self.assertTrue(
            CITATION.findall(page),
            f"{REFERENCE_PAGE.name} links into no section, so the form it "
            "documents has no example on it",
        )

    def test_every_page_links_into_a_group_that_exists(self):
        """A citation names a group the description declares -- from any page.

        Documents: docs/oeplatform-code/web-api/api-reference.md
        """
        cited = self.citations()
        self.assertTrue(cited, "no page of the documentation links into a section")
        dead = sorted(
            f"{page.relative_to(DOCUMENTATION)} -> {anchor}"
            for page, anchor in cited
            if anchor not in self.names
        )
        self.assertEqual(
            [],
            dead,
            "These pages link to a section the description does not declare. "
            "A renamed group leaves the link pointing at nothing, and the page "
            "opens at the top with no sign anything is wrong:\n    "
            + "\n    ".join(dead),
        )

    def test_every_group_name_makes_a_stable_anchor(self):
        for name in self.names:
            self.assertRegex(
                name,
                STABLE_ANCHOR,
                f"the group {name!r} carries characters an anchor cannot be "
                "linked to predictably",
            )


class TagModuleTest(SimpleTestCase):
    """The one property of ``api.api_tags`` that something else depends on.

    ``oeplatform.settings`` reads the list from it, which happens before
    Django's app registry exists. A module that imports nothing survives that;
    one that imports anything touching Django does not, and the failure is the
    whole project refusing to start rather than a test going red. The docstring
    says so, and a docstring is not a mechanism.
    """

    def test_the_tag_module_imports_nothing(self):
        source = Path(api.api_tags.__file__).read_text(encoding="utf-8")
        imports = [
            node
            for node in ast.parse(source).body
            if isinstance(node, (ast.Import, ast.ImportFrom))
        ]
        self.assertEqual(
            imports,
            [],
            "api/api_tags.py has grown an import; oeplatform.settings reads it "
            "before the app registry exists, so it has to stay inert",
        )


class LegacyTableGroupTest(SimpleTestCase):
    """The older table addresses, which no annotation on a view can reach.

    One view serves both spellings, so *everything* that distinguishes them --
    the callable path, the deprecation, the group and the operation id -- is
    set by the postprocessing hook. These check its work where it lands.
    """

    def setUp(self):
        self.document = committed_document()
        self.legacy = [
            (path, method, operation)
            for path, method, operation in operations(self.document)
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
        for path, method, operation in operations(self.document):
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
        for path, method, operation in operations(self.document):
            operation_id = operation.get("operationId", "")
            self.assertRegex(
                operation_id,
                r"^[A-Za-z0-9_]+$",
                f"{method.upper()} {path} has the operation id {operation_id!r}",
            )
