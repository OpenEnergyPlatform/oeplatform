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
"""  # noqa: 501

import difflib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml
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


class OpenAPISchemaTest(SimpleTestCase):
    """The committed description, checked against a fresh generation.

    See the module docstring for why validation precedes the comparison and why
    the generation runs in its own process.
    """

    generated = None
    generation_error = None

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
            cls.generated = fresh.read_text(encoding="utf-8")

    def test_the_generated_description_is_a_valid_openapi_document(self):
        if self.generation_error is not None:
            self.fail(
                "Generating the OpenAPI description failed. The generator "
                "names the annotation to fix; when it is fixed, regenerate "
                f"with:\n    {REGENERATE}\n\n{self.generation_error}"
            )

    def test_the_committed_artifact_matches_a_fresh_generation(self):
        if self.generation_error is not None:
            self.fail(
                "The OpenAPI description could not be generated, so it could "
                "not be compared against the committed artifact. Fix that "
                "first -- see "
                "test_the_generated_description_is_a_valid_openapi_document."
            )
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

    def test_every_scenario_bundle_endpoint_reaches_the_document(self):
        if self.generation_error is not None:
            self.skipTest("the OpenAPI description could not be generated")
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
