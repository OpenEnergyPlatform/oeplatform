"""The guard that keeps the committed description of ``api/v0`` true.

The description is generated from the code and committed to the repository, so
a reviewer sees in a pull request what the API's description became. That only
works while the committed copy is the one the code would produce, which is what
these checks are for. They name the command that regenerates it, because the
failure they report is nearly always somebody adding a route and not knowing
there was an artifact to update.

Two things about how they run are deliberate.

**Validation comes before the comparison.** A wrong annotation yields a stable
but invalid document, and a comparison alone would pass it forever. This was
observed on the branch that introduced the generator, where a dataset endpoint
acquired an empty Responses Object.

**The generation runs in a fresh process**, not through ``call_command``. The
artifact is defined as the output of the documented command, so that is what
runs. Generating it in-process would instead describe a Django that the rest of
the suite has already altered -- and it does alter it:
``Energyframework.__init__`` rewrites the ``help_text`` of the *shared* model
metadata (``modelview/models.py``), so merely having instantiated one framework,
which the ``modelview`` tests do, changes the described fields of the model
factsheet as well. In-process, the comparison below passed alone and failed
inside the suite.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: E501

import ast
import difflib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml
from django.apps import apps
from django.test import SimpleTestCase
from django.urls import URLPattern, URLResolver, get_resolver

from oeplatform.settings import BASE_DIR

#: The committed description of ``api/v0``, embedded by the reference page that
#: sits beside it. The path is part of the contract: the Swagger embed resolves
#: it relative to the page, so the artifact cannot move on its own.
ARTIFACT_PATH = "docs/oeplatform-code/web-api/openapi.yaml"
ARTIFACT = Path(BASE_DIR, ARTIFACT_PATH)

#: The command that writes the artifact, short of where to write it. It is run
#: as written, and the same list is printed whenever a check below fails, so
#: what is checked and what is advised cannot come apart. Deliberately without
#: ``--fail-on-warn``: the generator reports hundreds of pre-existing "unable to
#: guess serializer" findings on the plain views of the OEDB API, and failing on
#: those would leave the artifact unregenerable.
GENERATE = ["manage.py", "spectacular", "--validate", "--file"]
REGENERATE = " ".join(["python", *GENERATE, ARTIFACT_PATH])

#: Every endpoint below this prefix must reach the document. drf-spectacular
#: silently drops a view whose request or response it cannot resolve -- that is
#: what the bulk of the generator's errors on this project are -- and a route
#: falling out of the description that way disturbs none of the other checks.
COVERED_PREFIX = "api/v0/scenario-bundles/"


def _openapi_path(django_route):
    """Render a Django route the way OpenAPI spells the same path."""
    return "/" + re.sub(r"<(?:[^:<>]+:)?([^<>]+)>", r"{\1}", django_route)


def _routes(patterns, prefix=""):
    """Yield the full route string of every pattern reachable from here.

    Segments are joined as written. Several of this project's includes are
    ``re_path``s, so a segment can arrive carrying regular-expression anchors;
    those are dropped, because the interest here is which path was routed.
    """
    for entry in patterns:
        route = prefix + str(entry.pattern).lstrip("^").rstrip("$")
        if isinstance(entry, URLResolver):
            yield from _routes(entry.url_patterns, route)
        elif isinstance(entry, URLPattern):
            yield route


#: The legacy schema-qualified table addresses, after the postprocessing hook
#: has made them callable. Their canonical form is `/api/v0/tables/...`.
LEGACY_TABLE_PATH = "/api/v0/schema/{schema}/tables/"


def committed_document():
    """The artifact, parsed. The three guards that read it share this one."""
    return yaml.safe_load(ARTIFACT.read_text(encoding="utf-8"))


def operations(document, prefix=""):
    """Every operation in the document, as ``path, method, operation``.

    A path item holds more than operations -- shared ``parameters`` sit beside
    them -- so an entry is one when it declares the responses every operation
    has to declare.
    """
    for path, methods in document["paths"].items():
        if not path.startswith(prefix):
            continue
        for method, operation in methods.items():
            if isinstance(operation, dict) and "responses" in operation:
                yield path, method, operation


class OpenAPISchemaTest(SimpleTestCase):
    """The committed description, checked against a fresh generation.

    See the module docstring for why validation precedes the comparison and why
    the generation runs in its own process.
    """

    generated = None
    generation_error = None
    generation_output = ""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with tempfile.TemporaryDirectory() as directory:
            fresh = Path(directory, "openapi.yaml")
            result = subprocess.run(
                [sys.executable, *GENERATE, str(fresh)],
                cwd=BASE_DIR,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                cls.generation_error = result.stderr
                return
            cls.generation_output = result.stderr
            cls.generated = fresh.read_text(encoding="utf-8")

    def _require_a_generated_description(self):
        """Skip a check that has nothing to work with.

        A failed generation is reported once, by the check below whose subject
        it is. The two that read what it produced skip instead of failing, so
        one broken annotation reports as one failure rather than three -- and
        so that neither of them can report a drift or a missing endpoint that
        was never actually measured.
        """
        if self.generation_error is not None:
            self.skipTest(
                "the OpenAPI description could not be generated -- see "
                "test_the_generated_description_is_a_valid_openapi_document"
            )

    def test_the_generated_description_is_a_valid_openapi_document(self):
        if self.generation_error is not None:
            self.fail(
                "Generating the OpenAPI description failed. The generator "
                "names the annotation to fix; when it is fixed, regenerate "
                f"with:\n    {REGENERATE}\n\n{self.generation_error}"
            )

    def test_the_committed_artifact_matches_a_fresh_generation(self):
        self._require_a_generated_description()
        self.assertTrue(
            ARTIFACT.exists(),
            f"{ARTIFACT} is missing. Write it with:\n    {REGENERATE}",
        )
        committed = ARTIFACT.read_text(encoding="utf-8")
        if committed == self.generated:
            return
        # Not assertEqual: these are two ~2,000-line documents, and the useful
        # report is which lines moved, not either document.
        difference = list(
            difflib.unified_diff(
                committed.splitlines(),
                self.generated.splitlines(),
                fromfile=f"committed {ARTIFACT_PATH}",
                tofile="freshly generated",
                lineterm="",
                n=1,
            )
        )
        shown = difference[:80]
        if len(difference) > len(shown):
            shown.append(f"... and {len(difference) - len(shown)} more lines")
        self.fail(
            "The committed OpenAPI description no longer matches the API it "
            "describes. Regenerate it and commit the result:\n"
            f"    {REGENERATE}\n\n" + "\n".join(shown)
        )

    def test_the_description_is_generated_without_complaint(self):
        """No view left unannotated, anywhere in `api/v0`.

        The generator reports a view whose request or response it cannot
        resolve, and then **drops it** -- so an unannotated view is not a
        cosmetic complaint, it is an endpoint missing from the description. For
        most of this project's life there were hundreds of those, and the
        noise made the few that mattered unfindable.

        Asserted here rather than by passing `--fail-on-warn` to the command.
        The distinction is the one #2457 drew: the flag makes the artifact
        *unregenerable* while a complaint stands, which is a bad place to be
        mid-change. A failing test says the same thing without taking the
        command away.
        """
        self._require_a_generated_description()
        summary = [
            line
            for line in (self.generation_output or "").splitlines()
            if line.startswith(("Error", "Warning"))
        ]
        self.assertEqual(
            [],
            summary,
            "The generator is complaining about views it cannot describe. Each "
            "line names one; a view it cannot resolve is dropped from the "
            "description entirely. Annotate it -- `api/api_description.py` and "
            "`oekg/api_description.py` hold the vocabulary -- and regenerate:\n"
            f"    {REGENERATE}",
        )

    def test_the_legacy_table_addresses_are_callable_and_marked(self):
        """The schema-qualified spelling, as a client has to read it.

        Its schema segment is not captured by the route, so the generator
        renders the address with the raw character class in it -- something no
        client can call. `api.api_description.name_the_legacy_table_routes`
        repairs it, and this is what says the repair still runs: without the
        hook these paths come back as `/api/v0/schema/[\\w\\d_]/tables/...`
        and nothing else in the suite would notice.
        """
        self._require_a_generated_description()
        document = yaml.safe_load(self.generated)
        legacy = [p for p in document["paths"] if p.startswith(LEGACY_TABLE_PATH)]
        self.assertTrue(legacy, "no legacy schema-qualified table paths found")
        for path in document["paths"]:
            self.assertNotRegex(
                path,
                r"[\[\]\\^$*+]",
                f"{path} carries a regular expression where an address should "
                "be. A route whose parameter is not a named group renders this "
                "way; see name_the_legacy_table_routes.",
            )
        for path in legacy:
            for method, operation in document["paths"][path].items():
                self.assertTrue(
                    operation.get("deprecated"),
                    f"{method.upper()} {path} is the older spelling of an "
                    "endpoint and does not say so.",
                )
                self.assertIn(
                    "schema",
                    [p["name"] for p in operation.get("parameters", [])],
                    f"{method.upper()} {path} has a schema segment in its "
                    "address and does not describe it.",
                )

    def test_every_operation_says_what_it_does(self):
        """A route in the document with nothing written about it is half a fact."""
        self._require_a_generated_description()
        document = yaml.safe_load(self.generated)
        silent = [
            f"{method.upper()} {path}"
            for path, methods in document["paths"].items()
            for method, operation in methods.items()
            if isinstance(operation, dict) and not operation.get("description")
        ]
        self.assertEqual(
            [],
            silent,
            "These operations are described by their address alone. Give each "
            "an `extend_schema(description=...)` or a docstring, and "
            f"regenerate:\n    {REGENERATE}",
        )

    def test_every_scenario_bundle_endpoint_reaches_the_document(self):
        self._require_a_generated_description()
        described = set(yaml.safe_load(self.generated)["paths"])
        routed = {
            _openapi_path(route)
            for route in _routes(get_resolver().url_patterns)
            if route.startswith(COVERED_PREFIX)
        }
        self.assertTrue(routed, "no scenario-bundle routes found to check")
        self.assertEqual(
            set(),
            routed - described,
            "These scenario-bundle endpoints are routed but absent from the "
            "generated description. drf-spectacular drops a view whose request "
            "or response it cannot resolve; running the command below reports "
            f"which and why:\n    {REGENERATE}",
        )


#: How a test says which documentation page it pins. One line, in any docstring
#: of a test module, naming the page from the repository root::
#:
#:     Documents: docs/oeplatform-code/web-api/oekg-api/scenario-bundles.md
#:
#: The prose around it is for the reader; this line is the part a machine reads,
#: so the sentence a developer sees and the fact the check collects are one
#: thing rather than two that can drift apart.
POINTER = re.compile(r"^\s*Documents:\s*(\S+\.md)\s*$", re.MULTILINE)

#: What a test module is called, the way Django's own discovery spells it.
TEST_FILE = "test*.py"

#: The directory a checkout's dependencies land in, wherever it is put.
SITE_PACKAGES = "site-packages"


def project_packages():
    """The directories of this project's own apps.

    Deliberately not a walk of the whole tree from ``BASE_DIR``. A checkout
    routinely holds a virtual environment and a ``node_modules`` beneath it --
    this one carries 1,922 files matching ``test*.py`` inside ``.venv`` alone --
    so a plain walk would read thousands of third-party modules, and a
    ``Documents:`` line in any of their docstrings would be reported as this
    project's broken pointer. Asking the app registry also means a new app is
    covered the day it is added.

    Being under ``BASE_DIR`` is not enough on its own: a virtual environment
    inside the checkout puts the 27 installed apps under it too, so where a
    package sits is what separates this project's from everyone else's.
    """
    for config in apps.get_app_configs():
        path = Path(config.path)
        if path.is_relative_to(BASE_DIR) and SITE_PACKAGES not in path.parts:
            yield path


def declared_pointers():
    """Every code->doc pointer in the suite, as (file, named page) pairs.

    Read **statically**. Importing the modules instead would be much worse than
    slow: ``factsheet/tests/test_sector_dropdowns.py`` imports
    ``factsheet.oekg.connection``, which parses the whole OEO at module scope
    (``factsheet/oekg/connection.py:40``), so a collector that imported its way
    through the suite would pull a 1.3 GB ontology into memory to read a
    docstring.

    Every docstring is searched, not only the module's. The one pointer that
    predates this convention sits on a class, which is the natural place when a
    file pins more than one page.
    """
    found = {
        path for package in project_packages() for path in package.rglob(TEST_FILE)
    }
    for path in sorted(found):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(
                node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
            ):
                continue
            for named in POINTER.findall(ast.get_docstring(node) or ""):
                yield path, named


class DocumentationPointerTest(SimpleTestCase):
    """The pointers that run from a test to the page it keeps true.

    A documentation page describing behaviour goes stale silently: nothing
    fails at the moment the behaviour changes, which is the only moment the
    page is wrong. A citation in the prose does not help, because it rots on a
    rename with nobody watching. So the pointer runs the other way -- the test
    names the page -- and this is the check that the name still resolves.

    What it deliberately does **not** do is demand a pointer. A rule whose
    endpoint nobody has built yet has no test to carry one, and a check that
    insisted would be red until that work landed, which would teach the suite's
    readers to ignore it.

    This class carries no pointer of its own. It pins no documented behaviour,
    and a marker here would satisfy the emptiness check below out of its own
    docstring -- the check would then pass on a suite in which every real
    pointer had been deleted.
    """

    def setUp(self):
        self.pointers = list(declared_pointers())

    def test_the_suite_declares_at_least_one_pointer(self):
        """Without this the check below passes by finding nothing.

        The convention lives in docstrings, so a typo in the marker, a change
        of quoting style or a move of the test tree all end the same way: zero
        pointers collected, every assertion about them vacuously true.
        """
        self.assertTrue(
            self.pointers,
            "no test in the suite names a documentation page. Add a line "
            "'Documents: <path>' to the docstring of a test that pins what a "
            "page describes",
        )

    def test_every_named_page_exists(self):
        missing = sorted(
            f"{path.relative_to(BASE_DIR)} -> {named}"
            for path, named in self.pointers
            if not Path(BASE_DIR, named).is_file()
        )
        self.assertEqual(
            [],
            missing,
            "These tests name a documentation page that is not in the tree. "
            "The page was renamed, moved or deleted; point the test at where "
            "it went:\n    " + "\n    ".join(missing),
        )
