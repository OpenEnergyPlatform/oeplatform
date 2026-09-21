"""What `/ontology/<name>/...` answers, now that something checks the name.

Measured before this changed, on localhost and on production (2026-09-21):

    /ontology/nonsense/nonsense/        200   the React shell, for nothing
    /ontology/nonsense/entities/        200   a search page for nothing
    /ontology/nonsense/releases/latest  500   FileNotFoundError out of os.listdir
    /ontology/oekg/<bundle-uuid>/       200   an ontology TERM page for a bundle

Three different answers to "this does not exist", none of them a 404, and a
scenario bundle rendering as an ontology term. Every one of those is a route
that took a name and never asked whether it was a name we serve.

The two real ontologies are pinned FIRST in this module, because they are the
reason the catch-all exists and the thing a name check is most likely to break.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import tempfile
import uuid
from unittest import mock

from django.test import TestCase
from django.urls import resolve

from ontology import urls as ontology_urls
from ontology.views import get_OEO_MODULES_MAIN
from ontology.vocabularies import KNOWLEDGE_GRAPH, names_of_kind

# A name of every shape a vocabulary name can be given, so an unknown one is
# asked the same question at each. The statics view answers four of these and
# the React view two; before this slice they disagreed about what "unknown"
# means.
ADDRESS_SHAPES = (
    "/ontology/{name}/",
    "/ontology/{name}/entities/",
    "/ontology/{name}/OEO_00000040/",
    "/ontology/{name}/releases/latest",
    "/ontology/{name}/releases/latest/glossary",
    "/ontology/{name}/releases/v1.0.0/oeo-full.owl",
    "/ontology/{name}/dev/oeo-full.owl",
)


class RealOntologiesStillResolveTest(TestCase):
    """The addresses that worked before this slice and must go on working."""

    def test_an_oeo_term_page_is_served(self):
        response = self.client.get("/ontology/oeo/OEO_00000040/")

        self.assertEqual(response.status_code, 200)

    def test_the_oeo_entity_search_is_served(self):
        response = self.client.get("/ontology/oeo/entities/")

        self.assertEqual(response.status_code, 200)

    def test_an_oeo_ext_term_page_is_served(self):
        # The extension's name carries an underscore, which the two route
        # regexes spell differently. Pinned so a tightened pattern cannot drop
        # it quietly.
        response = self.client.get("/ontology/oeo_ext/OEO_00000040/")

        self.assertEqual(response.status_code, 200)

    def test_the_oeo_ext_entity_search_is_served(self):
        response = self.client.get("/ontology/oeo_ext/entities/")

        self.assertEqual(response.status_code, 200)

    def test_the_file_backed_releases_are_still_served(self):
        if "oeo" not in get_OEO_MODULES_MAIN():
            self.skipTest("The local ontology files are not present.")

        response = self.client.get("/ontology/oeo/releases/latest/glossary")

        self.assertEqual(response.status_code, 200)


class UnknownVocabularyTest(TestCase):
    def test_an_unknown_name_is_404_at_every_route_that_takes_one(self):
        for shape in ADDRESS_SHAPES:
            address = shape.format(name="nonsense")
            with self.subTest(address=address):
                self.assertEqual(self.client.get(address).status_code, 404)

    def test_an_unknown_name_does_not_render_the_ontology_shell(self):
        # The failure this replaces was not an error page: it was a working
        # page about nothing, which a reader has no way to tell from a real
        # one. The shell put the name in its own breadcrumb -- "NONSENSE
        # Search" -- so the name's absence from the body is the evidence that
        # no page about it was built. Asserting on the 404 template instead
        # would pass just as well against a shell that had stopped echoing it.
        response = self.client.get("/ontology/nonsense/nonsense/")

        self.assertEqual(response.status_code, 404)
        self.assertNotContains(response, "NONSENSE", status_code=404)


class MissingOntologyDirectoryTest(TestCase):
    """A registered name whose files are not there.

    The two cases mean different things and the tests keep them apart:
    **unknown** is "we do not serve this at all" and is a permanent answer,
    while **missing directory** is "we do serve this, and this deployment has
    not got the files" -- a deployment fault. Both are 404 to a client, because
    there is nothing at the address either way; the distinction lives in the
    logs and in this test, not in the status code. What neither may be is the
    500 that `os.listdir` raised.
    """

    def test_a_known_ontology_with_no_directory_is_404_and_not_500(self):
        with tempfile.TemporaryDirectory() as empty:
            with mock.patch("ontology.views.ONTOLOGY_ROOT", empty):
                response = self.client.get("/ontology/oeo/releases/latest")

        self.assertEqual(response.status_code, 404)

    def test_the_glossary_of_a_missing_directory_is_404_and_not_500(self):
        with tempfile.TemporaryDirectory() as empty:
            with mock.patch("ontology.views.ONTOLOGY_ROOT", empty):
                response = self.client.get("/ontology/oeo/releases/latest/glossary")

        self.assertEqual(response.status_code, 404)


class KnowledgeGraphRoutingTest(TestCase):
    """A store-backed name must never reach the file-backed views."""

    def test_every_knowledge_graph_has_routes_of_its_own(self):
        # The coverage test the registry is worth having: a name whose kind
        # nothing routes would fall through to the ontology views, and a
        # knowledge graph resolving to nothing looks exactly like a graph whose
        # contents have been deleted.
        self.assertEqual(
            sorted(ontology_urls.KNOWLEDGE_GRAPH_ROUTES),
            sorted(names_of_kind(KNOWLEDGE_GRAPH)),
        )

    def test_a_bundle_address_is_not_served_by_the_ontology_view(self):
        match = resolve(f"/ontology/oekg/{uuid.uuid4()}/")

        self.assertNotEqual(match.func, resolve("/ontology/oeo/OEO_1/").func)

    def test_the_knowledge_graph_routes_precede_the_ontology_catch_all(self):
        # Exactly what a later route addition would silently undo: the
        # catch-all matches `oekg/<anything>/` perfectly well, so it wins if it
        # is reached first, and the knowledge graph becomes an ontology again.
        names = [pattern.name for pattern in ontology_urls.urlpatterns]

        self.assertLess(names.index("oekg-bundle-iri"), names.index("oeo-class-detail"))
        self.assertLess(
            names.index("oekg-scenario-iri"), names.index("ontology-entity-search")
        )

    def test_the_knowledge_graph_name_reaches_no_file_backed_view(self):
        # `oekg` is registered, so the name check alone would let it through;
        # what keeps it out of `os.listdir` is that its own routes own the
        # whole namespace.
        for shape in ADDRESS_SHAPES:
            address = shape.format(name="oekg")
            with self.subTest(address=address):
                self.assertEqual(self.client.get(address).status_code, 404)
