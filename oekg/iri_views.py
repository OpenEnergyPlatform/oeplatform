"""Making the OEKG's own IRIs dereference.

Every bundle this platform holds is named by an IRI under
`https://openenergyplatform.org/ontology/oekg/`, and until this module existed
none of those IRIs answered anything. Following one reached the ontology
catch-all and got a term page for a term that does not exist -- a 200, for a
scenario bundle, rendered as a piece of an ontology.

**What resolves, deliberately narrow:**

- a bundle,   ``.../oekg/<uuid>``
- a scenario, ``.../oekg/scenario/<pid>``

**What does not, equally deliberately:** everything else minted in that
namespace -- ``study-report/``, ``dataset/``, ``contact/``, ``organisation/``,
``funder/``, ``framework/``, ``model/``, ``region/``, ``author/``. They are
404, because there is nothing to send a reader to: the user interface has no
page for any of them and only `ScenarioBundleAPIView` serves RDF, so a redirect
would have to invent a destination. ``version/`` must **never** resolve however
that changes: it is bookkeeping the read side hides on purpose
(`oekg/versioning.py`), and an address for it would publish a node no
representation of a bundle contains.

**303, not 302 and not 200.** The IRI names a scenario bundle -- a thing in the
world -- and what it redirects to is a document *about* that thing. A 200 here
would say the bundle and the web page are the same object, which is the exact
confusion this module exists to remove. Both kinds resolve to the same pair of
destinations, differing only in which bundle:

    Accept: text/html                          -> /scenario-bundles/id/<uid>
    Accept: text/turtle | application/ld+json  -> /api/v0/scenario-bundles/<uid>/

Anything else -- `*/*` from curl, a browser's long Accept list, a client asking
for something nobody serves -- gets the HTML page, because a person following a
link is the case that has to work without being spelled.

**Both forms of the address answer.** The minted IRI has no trailing slash and
that is the form people paste; the routes accept it directly rather than
leaving it to `APPEND_SLASH`, which would 301 it first. Every citation in the
wild would otherwise cost two requests, with two chances for a client to drop
the `Accept` header that decides where it lands.

**A scenario's IRI carries only its own identifier**, not its bundle's, so
resolving one is a query: which bundle has this scenario as a part. The IRI is
matched exactly rather than looked up by has-uuid, so the answer is about the
address given and not about something that happens to share an identifier.

**Only IRIs this API minted resolve.** A scenario written through the browser
lives at an address this API did not mint and under a different shape, so
``.../oekg/scenario/<pid>`` names API-minted scenarios alone. That is a 404
reporting an identity problem that predates this module, not a bug in it.

**This module stays light on purpose.** It must not reach
`factsheet/oekg/connection.py`, which parses the full ontology at import --
1.3 GB resident per process -- and a test pins that it does not.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import logging

from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.urls import re_path, reverse

from oekg.api_support import bundle_exists, is_minted_identifier
from oekg.bundles import BUNDLE_CLASS, SCENARIO, bundle_uid, part_iri
from oekg.fields import HAS_PART
from oekg.graph_store import GraphStore, GraphStoreError

logger = logging.getLogger("oeplatform")

#: The representations that mean "send me the graph, not the page". Both are
#: served by `ScenarioBundleAPIView`, which slice 10 taught to render RDF.
RDF_MEDIA_TYPES = ("text/turtle", "application/ld+json")

#: What a minted identifier looks like in a URL. Narrow enough that nothing
#: reaches a query which could not have been minted; the value is checked
#: against `is_minted_identifier` as well, which is what actually keeps the
#: query free of injection.
IDENTIFIER = r"[\w-]+"


class HttpResponseSeeOther(HttpResponseRedirect):
    """A 303. Django ships 301 and 302 and not this one.

    The distinction is the point of the module rather than pedantry: 302 would
    say the bundle has temporarily moved to a web page, and the bundle is not a
    web page at all.
    """

    status_code = 303


def _bundle_of_scenario(store: GraphStore, scenario) -> str:
    """The uid of the bundle this scenario belongs to, or ``None``.

    Both types are asserted, not just the has-part edge: an edge alone would
    resolve any node some bundle happens to point at, and this address promises
    a scenario.

    ``LIMIT 1`` because a scenario factsheet belongs to one bundle. The graph
    does not enforce that, so the limit states the assumption instead of
    letting an unexpected second row decide the answer by ordering.

    ``None`` also when the bundle found lives at an IRI outside the namespace
    -- the user interface concatenates a uid of its client's choosing. Such a
    bundle has no URL of its own either, so there is nowhere to send anyone and
    a 404 reports an identity problem that predates this module.
    """
    query = """
        SELECT ?bundle WHERE {
          ?bundle a %(bundle_class)s ;
                  %(has_part)s %(scenario)s .
          %(scenario)s a %(scenario_class)s .
        }
        LIMIT 1
    """ % {
        "bundle_class": BUNDLE_CLASS.n3(),
        "has_part": HAS_PART.n3(),
        "scenario": scenario.n3(),
        "scenario_class": SCENARIO.node_class.n3(),
    }
    rows = store.select(query)
    return bundle_uid(rows[0]["bundle"]) if rows else None


def _destination(request, uid: str) -> str:
    """Where a reader asking like this should be sent for bundle ``uid``.

    HTML is the default rather than one branch of three: a client that asks for
    nothing in particular is a person following a link.
    """
    if not request.accepts("text/html") and any(
        request.accepts(media_type) for media_type in RDF_MEDIA_TYPES
    ):
        return reverse("api:scenario-bundle", kwargs={"uid": uid})
    return reverse("factsheet:bundle-id-page", args=[uid])


def _see_other(request, uid: str) -> HttpResponse:
    return HttpResponseSeeOther(_destination(request, uid))


def _unavailable(error: Exception) -> HttpResponse:
    """The store could not be asked -- which is not the same as "not there".

    A 404 here would tell a client the bundle has been deleted, and a client
    that believes that stops asking.
    """
    logger.error("An OEKG address could not be resolved: %s", error)
    return HttpResponse(
        "The OEKG graph store could not be reached.",
        content_type="text/plain; charset=utf-8",
        status=503,
    )


def bundle_address(request, uid: str) -> HttpResponse:
    """Dereference a bundle's own IRI.

    Asked through `bundle_exists` rather than with an ASK of its own, because
    that is where the one spelling of this question lives and two spellings of
    it would be free to drift.
    """
    try:
        found = bundle_exists(uid)
    except GraphStoreError as error:
        return _unavailable(error)

    if not found:
        raise Http404(f"No scenario bundle {uid}.")
    return _see_other(request, uid)


def scenario_address(request, pid: str) -> HttpResponse:
    """Dereference a scenario's IRI, by way of the bundle holding it.

    There is no scenario page to send anyone to, so both representations are
    the bundle's. That is not a shortcut: a scenario factsheet is read as part
    of its bundle everywhere else in this API too.

    The identifier is checked here rather than inside a shared helper the way
    the bundle's is, because there is no `scenario_exists`: this is the only
    place that asks. An IRI-unsafe value makes rdflib refuse to build the IRI,
    which would surface as a 500 rather than the 404 it is.
    """
    if not is_minted_identifier(pid):
        raise Http404(f"{pid!r} is not an identifier this platform mints.")

    store = GraphStore.from_settings()
    scenario = part_iri(SCENARIO, pid)
    try:
        uid = _bundle_of_scenario(store, scenario)
    except GraphStoreError as error:
        return _unavailable(error)

    if uid is None:
        raise Http404(f"No scenario {pid} in any bundle.")
    return _see_other(request, uid)


def unresolvable_address(request, *args, **kwargs) -> HttpResponse:
    """Everything else in the OEKG namespace.

    A route rather than a fall-through, so the answer is this module's and
    stays this module's: without it these addresses would reach the ontology
    catch-all again the moment a pattern there is widened.
    """
    raise Http404(
        "Only a scenario bundle and a scenario factsheet have an address in "
        "the OEKG namespace."
    )


#: Registered ahead of the ontology routes, so the whole `oekg/` namespace is
#: answered here and no part of it can fall into a view that lists a directory.
urlpatterns = [
    re_path(
        r"^oekg/%s/(?P<pid>%s)/?$" % (SCENARIO.mint_segment, IDENTIFIER),
        scenario_address,
        name="oekg-scenario-iri",
    ),
    re_path(
        r"^oekg/(?P<uid>%s)/?$" % IDENTIFIER,
        bundle_address,
        name="oekg-bundle-iri",
    ),
    re_path(r"^oekg/", unresolvable_address, name="oekg-address"),
]
