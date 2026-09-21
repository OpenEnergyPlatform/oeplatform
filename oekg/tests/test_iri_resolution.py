"""Following an OEKG IRI, and arriving somewhere.

Every bundle is named by an IRI under
`https://openenergyplatform.org/ontology/oekg/`, and until this slice none of
those IRIs answered anything useful: the address fell through to the ontology
catch-all and got a 200, a term page, for a term that does not exist.

Three properties are under test, and they are the three that make a dereference
worth building:

- **The address the graph names is the address that answers.** The tests derive
  the URL from `bundle_iri` and from the scenario's own mint segment rather
  than writing it out, so the routes cannot drift from the IRIs the API mints.
- **303, and where to.** The IRI names a scenario bundle; what it redirects to
  is a document *about* that bundle -- a page for a reader, the API's
  representation for a client asking for RDF. A 200 would say the bundle and
  the page are one object.
- **The scope is narrow on purpose.** A bundle and a scenario resolve. Every
  other node this API mints in that namespace is a 404, because there is
  nowhere honest to send anyone, and `version/` is 404 however that changes.

Rule: these run against a real Fuseki through the named URLs, the seam every
OEKG slice uses, and skip with a reason without one.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import os
import subprocess
import sys
import uuid
from unittest import mock
from urllib.parse import urlparse

from django.test import SimpleTestCase
from django.urls import reverse

from oekg.bundles import SCENARIO, bundle_iri, part_iri
from oekg.graph_store import GraphStoreUnavailable
from oekg.iri_views import RDF_MEDIA_TYPES
from oekg.renderers import RDF_RENDERERS
from oekg.serializers import READ_ONLY_CONTAINER
from oekg.tests.bundle_fixtures import VALID_PAYLOAD
from oekg.tests.test_scenario_api import VALID_SCENARIO, ScenarioTestCase
from oekg.tests.test_study_report_api import VALID_REPORT
from oekg.versioning import version_iri

BROWSER_ACCEPT = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"

# What `rdflib.Graph().parse(url, format=...)` actually sends, copied from
# `rdflib.parser.URLInputSource`. Every one of them carries `*/*;q=0.1`, which
# is the whole reason this endpoint has to read quality values rather than ask
# whether a client "accepts" a type: on membership alone all three of these
# accept HTML, and every RDF client went to the page.
RDFLIB_ACCEPT = {
    "turtle": "text/turtle, application/x-turtle, */*;q=0.1",
    "json-ld": "application/ld+json, application/json;q=0.9, */*;q=0.1",
}

# rdflib's XML request. This platform serves no rdf+xml, so it ties with HTML
# at the wildcard and gets the page -- better than a redirect to a 406.
RDFLIB_XML_ACCEPT = "application/rdf+xml, */*;q=0.1"

# Every segment this API mints a node under that is NOT addressable. Each is a
# real kind of node in the live graph; none of them has a page or an RDF
# representation of its own, so each is a 404 rather than a redirect to
# somewhere approximate.
UNADDRESSABLE_SEGMENTS = (
    "study-report",
    "dataset",
    "contact",
    "organisation",
    "funder",
    "framework",
    "model",
    "region",
    "author",
    "version",
)


class IriTestCase(ScenarioTestCase):
    def bundle_address(self, uid):
        """The path of the bundle's own IRI -- taken from the minted IRI.

        Written out, this test would go on passing after the routes and the
        namespace had parted company.
        """
        return urlparse(str(bundle_iri(uid))).path + "/"

    def scenario_address(self, sid):
        return urlparse(str(part_iri(SCENARIO, sid))).path + "/"

    def page_of(self, uid):
        return reverse("factsheet:bundle-id-page", args=[uid])

    def api_of(self, uid):
        return reverse("api:scenario-bundle", kwargs={"uid": uid})


class BundleAddressTest(IriTestCase):
    def test_a_reader_is_sent_to_the_bundle_page(self):
        uid, _ = self.created()

        response = self.client.get(self.bundle_address(uid), HTTP_ACCEPT="text/html")

        self.assertEqual(response.status_code, 303)
        self.assertEqual(response["Location"], self.page_of(uid))

    def test_a_client_asking_for_turtle_is_sent_to_the_api(self):
        uid, _ = self.created()

        response = self.client.get(self.bundle_address(uid), HTTP_ACCEPT="text/turtle")

        self.assertEqual(response.status_code, 303)
        self.assertEqual(response["Location"], self.api_of(uid))

    def test_a_client_asking_for_json_ld_is_sent_to_the_api(self):
        uid, _ = self.created()

        response = self.client.get(
            self.bundle_address(uid), HTTP_ACCEPT="application/ld+json"
        )

        self.assertEqual(response.status_code, 303)
        self.assertEqual(response["Location"], self.api_of(uid))

    def test_a_real_rdf_client_reaches_the_graph(self):
        # The case that was broken while every hand-written Accept header
        # passed: `rdflib` sends a wildcard beside the type it wants, so a
        # membership test says it accepts HTML and it never saw the graph.
        uid, _ = self.created()

        for form, accept in RDFLIB_ACCEPT.items():
            with self.subTest(form=form):
                response = self.client.get(self.bundle_address(uid), HTTP_ACCEPT=accept)

                self.assertEqual(response.status_code, 303)
                self.assertEqual(response["Location"], self.api_of(uid))

    def test_a_form_this_platform_does_not_serve_gets_the_page(self):
        # Redirecting to an endpoint that would answer 406 is worse than
        # answering with the page a person can read.
        uid, _ = self.created()

        response = self.client.get(
            self.bundle_address(uid), HTTP_ACCEPT=RDFLIB_XML_ACCEPT
        )

        self.assertEqual(response["Location"], self.page_of(uid))

    def test_the_forms_offered_are_the_ones_the_destination_serves(self):
        # A media type promised here and not rendered there would send a client
        # to a refusal; one rendered there and not promised here would leave a
        # client on the page. Read off the renderers so neither can drift.
        self.assertEqual(
            sorted(RDF_MEDIA_TYPES),
            sorted(renderer.media_type for renderer in RDF_RENDERERS),
        )

    def test_a_browser_gets_the_page_although_it_accepts_anything(self):
        # A browser's Accept ends in `*/*;q=0.8`, so "does it accept turtle" is
        # true of every browser alive. HTML has to win on being asked for, not
        # on being the only thing acceptable.
        uid, _ = self.created()

        response = self.client.get(self.bundle_address(uid), HTTP_ACCEPT=BROWSER_ACCEPT)

        self.assertEqual(response["Location"], self.page_of(uid))

    def test_a_client_asking_for_nothing_in_particular_gets_the_page(self):
        # curl sends `*/*`. Somebody following a link is the case that has to
        # work without being spelled out.
        uid, _ = self.created()

        response = self.client.get(self.bundle_address(uid), HTTP_ACCEPT="*/*")

        self.assertEqual(response["Location"], self.page_of(uid))

    def test_the_bare_iri_with_no_trailing_slash_resolves_in_one_hop(self):
        # This is the address people actually paste: the minted IRI has no
        # trailing slash. The routes accept both forms, so it arrives in one
        # hop. Left to `APPEND_SLASH` it would 301 first, and the address in
        # every citation would cost two requests and two chances to lose the
        # Accept header on the way.
        uid, _ = self.created()
        bare = self.bundle_address(uid).rstrip("/")

        response = self.client.get(bare, HTTP_ACCEPT="text/html", follow=True)

        self.assertEqual(response.redirect_chain, [(self.page_of(uid), 303)])

    def test_the_destination_of_a_reader_is_a_page_that_exists(self):
        # The redirect is only worth anything if what it names answers. Taken
        # from the router in the view for the same reason.
        uid, _ = self.created()

        response = self.client.get(self.page_of(uid))

        self.assertEqual(response.status_code, 200)

    def test_the_destination_of_a_client_serves_the_graph(self):
        uid, _ = self.created()

        response = self.client.get(self.api_of(uid), HTTP_ACCEPT="text/turtle")

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/turtle", response["Content-Type"])

    def test_an_unknown_identifier_is_404(self):
        response = self.client.get(f"/ontology/oekg/{uuid.uuid4()}/")

        self.assertEqual(response.status_code, 404)

    def test_an_unknown_identifier_is_not_the_ontology_shell(self):
        # The defect this closes: a bundle uuid rendered as an ontology TERM,
        # with a 200. A wrong uuid must not look like a working page either.
        response = self.client.get(f"/ontology/oekg/{uuid.uuid4()}/")

        self.assertNotContains(response, "OEKG Search", status_code=404)

    def test_an_identifier_this_api_could_not_have_minted_is_404(self):
        # Refused before it reaches a query: an IRI-unsafe value makes rdflib
        # raise, which would surface as a 500 rather than the 404 it is.
        response = self.client.get("/ontology/oekg/not-a-uuid/")

        self.assertEqual(response.status_code, 404)

    def test_a_deleted_bundle_stops_resolving(self):
        # The address survives in citations; what it reports has to follow the
        # graph rather than the URL pattern.
        uid, etag = self.created()
        self.client.force_login(self.user)
        deleted = self.client.delete(
            f"{self.detail_url(uid)}?confirm={VALID_PAYLOAD['acronym']}",
            HTTP_IF_MATCH=etag,
        )
        self.assertEqual(deleted.status_code, 200, deleted.data)

        response = self.client.get(self.bundle_address(uid), HTTP_ACCEPT="text/html")

        self.assertEqual(response.status_code, 404)


class ScenarioAddressTest(IriTestCase):
    def test_a_scenario_resolves_to_the_bundle_holding_it(self):
        # A scenario's IRI carries only its own identifier, so which bundle it
        # belongs to is a query. There is no scenario page to send anyone to,
        # and a scenario factsheet is read as part of its bundle everywhere
        # else in this API too.
        uid, sid, _ = self.with_one_scenario()

        response = self.client.get(self.scenario_address(sid), HTTP_ACCEPT="text/html")

        self.assertEqual(response.status_code, 303)
        self.assertEqual(response["Location"], self.page_of(uid))

    def test_a_scenario_asked_for_as_turtle_goes_to_the_bundle_api(self):
        uid, sid, _ = self.with_one_scenario()

        response = self.client.get(
            self.scenario_address(sid), HTTP_ACCEPT="text/turtle"
        )

        self.assertEqual(response.status_code, 303)
        self.assertEqual(response["Location"], self.api_of(uid))

    def test_a_scenario_asked_for_as_json_ld_goes_to_the_bundle_api(self):
        uid, sid, _ = self.with_one_scenario()

        response = self.client.get(
            self.scenario_address(sid), HTTP_ACCEPT="application/ld+json"
        )

        self.assertEqual(response.status_code, 303)
        self.assertEqual(response["Location"], self.api_of(uid))

    def test_a_scenario_reached_by_a_real_rdf_client_goes_to_the_api(self):
        uid, sid, _ = self.with_one_scenario()

        response = self.client.get(
            self.scenario_address(sid), HTTP_ACCEPT=RDFLIB_ACCEPT["turtle"]
        )

        self.assertEqual(response["Location"], self.api_of(uid))

    def test_the_right_bundle_is_found_when_there_are_several(self):
        # One query over has-part, so a second bundle is what would catch it
        # answering with whatever it found first.
        self.created(
            {
                **VALID_PAYLOAD,
                "acronym": "OTHER",
                "scenarios": [{**VALID_SCENARIO, "acronym": "OTHER-RE"}],
            }
        )
        uid, sid, _ = self.with_one_scenario()

        response = self.client.get(self.scenario_address(sid), HTTP_ACCEPT="text/html")

        self.assertEqual(response["Location"], self.page_of(uid))

    def test_a_bare_scenario_iri_resolves_in_one_hop_too(self):
        uid, sid, _ = self.with_one_scenario()
        bare = self.scenario_address(sid).rstrip("/")

        response = self.client.get(bare, HTTP_ACCEPT="text/html", follow=True)

        self.assertEqual(response.redirect_chain, [(self.page_of(uid), 303)])

    def test_an_unknown_scenario_is_404(self):
        response = self.client.get(f"/ontology/oekg/scenario/{uuid.uuid4()}/")

        self.assertEqual(response.status_code, 404)

    def test_a_bundle_identifier_under_the_scenario_segment_is_404(self):
        # The IRI is matched exactly rather than looked up by has-uuid, so the
        # answer is about the address given -- not about something that happens
        # to share an identifier with it.
        uid, _ = self.created()

        response = self.client.get(f"/ontology/oekg/scenario/{uid}/")

        self.assertEqual(response.status_code, 404)

    def test_a_scenario_identifier_at_the_bundle_address_is_404(self):
        uid, sid, _ = self.with_one_scenario()

        response = self.client.get(f"/ontology/oekg/{sid}/")

        self.assertEqual(response.status_code, 404)

    def test_a_scenario_of_a_deleted_bundle_stops_resolving(self):
        uid, sid, etag = self.with_one_scenario()
        self.client.force_login(self.user)
        self.client.delete(
            f"{self.detail_url(uid)}?confirm={VALID_PAYLOAD['acronym']}",
            HTTP_IF_MATCH=etag,
        )

        response = self.client.get(self.scenario_address(sid), HTTP_ACCEPT="text/html")

        self.assertEqual(response.status_code, 404)


class NothingElseResolvesTest(IriTestCase):
    """The scope is narrow, and the narrowness is the decision under test."""

    def test_every_other_minted_segment_is_404(self):
        for segment in UNADDRESSABLE_SEGMENTS:
            address = f"/ontology/oekg/{segment}/{uuid.uuid4()}/"
            with self.subTest(segment=segment):
                self.assertEqual(self.client.get(address).status_code, 404)

    def test_a_real_bundles_version_node_is_404(self):
        # `version/` must never resolve however the scope grows. It is
        # bookkeeping the read side hides on purpose, and an address for it
        # would publish a node no representation of a bundle contains. Asked of
        # a version node that genuinely exists, so this is the scope refusing
        # rather than the graph being empty.
        uid, _ = self.created()
        address = urlparse(str(version_iri(uid))).path + "/"

        self.assertEqual(self.client.get(address).status_code, 404)

    def test_a_real_study_report_is_404(self):
        # A study report IS addressable in the REST API and is deliberately not
        # addressable here: it has no page of its own, and only the bundle
        # endpoint serves RDF.
        uid, _ = self.created({**VALID_PAYLOAD, "study_reports": [VALID_REPORT]})
        read = self.client.get(self.detail_url(uid)).data
        pid = read["study_reports"][0][READ_ONLY_CONTAINER]["uid"]

        response = self.client.get(f"/ontology/oekg/study-report/{pid}/")

        self.assertEqual(response.status_code, 404)

    def test_the_namespace_root_is_404(self):
        self.assertEqual(self.client.get("/ontology/oekg/").status_code, 404)

    def test_a_deeper_address_is_404_rather_than_unrouted(self):
        # Answered by this module's own catch-all rather than by nothing
        # matching, so the answer stays here when a pattern above is widened.
        response = self.client.get("/ontology/oekg/scenario/x/y/z/")

        self.assertEqual(response.status_code, 404)


class StoreUnavailableTest(IriTestCase):
    """ "Not there" and "I could not find out" are different answers.

    A 404 from an unreachable store tells a client the bundle has been deleted,
    and a client that believes that stops asking.
    """

    def test_an_unreachable_store_is_503_not_404(self):
        uid, _ = self.created()
        with mock.patch(
            "oekg.iri_views.GraphStore.ask", side_effect=GraphStoreUnavailable("down")
        ):
            response = self.client.get(self.bundle_address(uid))

        self.assertEqual(response.status_code, 503)

    def test_an_unreachable_store_is_503_for_a_scenario_too(self):
        _, sid, _ = self.with_one_scenario()
        with mock.patch(
            "oekg.iri_views.GraphStore.select",
            side_effect=GraphStoreUnavailable("down"),
        ):
            response = self.client.get(self.scenario_address(sid))

        self.assertEqual(response.status_code, 503)


class LightImportTest(SimpleTestCase):
    """The resolver must not drag in the module that parses the ontology.

    `factsheet/oekg/connection.py` builds an rdflib graph over the whole OEO at
    import -- 1.3 GB resident, per process. `ontology/urls.py` imports this
    module at URLConf-import time, so an import added here is paid by every
    process that serves any URL at all.

    A subprocess, because the suite has almost certainly imported that module
    already for other reasons, and `sys.modules` in-process would say nothing.
    """

    def test_importing_the_resolver_does_not_import_the_ontology_connection(self):
        script = (
            "import django, sys; django.setup(); import oekg.iri_views; "
            "print('factsheet.oekg.connection' in sys.modules)"
        )
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
            env={**os.environ, "PYTHONPATH": os.getcwd()},
        )

        self.assertEqual(result.returncode, 0, result.stderr[-2000:])
        self.assertIn("False", result.stdout.splitlines()[-1])
