"""The OEKG REST API's own transport to the graph store.

Deliberately **not** `factsheet/oekg/connection.py`. That module exposes the
graph as an rdflib ``Graph`` over a ``SPARQLUpdateStore`` with
``autocommit=True``, so every ``add()`` is its own committed transaction: a
~200-triple bundle costs ~200 requests and 30 s, and an abort halfway leaves
half a bundle behind. It also parses the full ontology at import -- 1.3 GB
resident and ~36 s, per process -- which no request path should pay for.

So the boundary is drawn one step earlier: **keep rdflib for building a graph
in memory, drop it as transport.** Callers assemble triples in an
``rdflib.Graph`` (which is also what the validator will read), and this module
ships them as *one* SPARQL request.

That one request is also one transaction, across ``;``-separated operations --
established by experiment against Fuseki 5.1.0 on TDB2, and re-proved by this
app's own tests rather than taken on trust. It is why an update-in-place is
expressible at all: a delete and an insert in one request either both apply or
neither does.

Two safety properties are built in rather than left to callers:

- **The store's own error bodies never escape.** Fuseki answers a bad query
  with a parser dump that echoes the generated query back. It is logged, never
  raised.
- **`clear()` refuses to touch the default graph.** It exists for tests, and a
  helper that could `DROP DEFAULT` is one misconfigured endpoint away from
  erasing the production knowledge graph.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import logging
from dataclasses import dataclass, field
from typing import Optional

import requests
from django.conf import settings
from rdflib import Graph

logger = logging.getLogger("oeplatform")

DEFAULT_TIMEOUT_SECONDS = 60

SELECT_RESULTS = "application/sparql-results+json"
CONSTRUCT_RESULTS = "text/turtle"

# An availability probe should answer fast or not at all: it runs before a test
# class and decides whether to skip, so it must not stall a suite.
AVAILABILITY_TIMEOUT_SECONDS = 5

# DROP SILENT on a graph nothing uses: a write that changes nothing whatever
# the store's state, so the probe is safe against any endpoint.
AVAILABILITY_PROBE_GRAPH = "urn:oep:graph-store-availability-probe"

# Distinguishes "use whatever is configured" from an explicit "the default
# graph". Without it, asking for the default graph would silently pick up a
# test's override instead.
USE_CONFIGURED_GRAPH = object()


class GraphStoreError(Exception):
    """Base class for every way talking to the graph store can fail.

    ``action`` names what was refused and ``detail`` what the caller may assume
    about the graph's state afterwards. Both live on the class so the message
    is built from the failure itself rather than from an argument that has to
    agree with it.
    """

    action = "request"
    detail = ""


class GraphStoreUnavailable(GraphStoreError):
    """The store could not be reached at all -- DNS, refused, or timed out."""


class GraphQueryRejected(GraphStoreError):
    """The store refused a read. Its response body is logged, never carried."""

    action = "query"


class GraphUpdateRejected(GraphStoreError):
    """The store refused a write. Its response body is logged, never carried."""

    action = "update"
    detail = "Nothing was changed: one request is one transaction."


class UnsafeClearError(GraphStoreError):
    """Refused to empty the default graph."""


class NothingToModifyError(GraphStoreError):
    """A guarded modification was asked for with no triples to change."""


@dataclass(frozen=True)
class GraphStore:
    """A query client and an update client, and no pretence of being a graph.

    ``graph`` names the target: ``None`` is the default graph, which is what
    the platform reads and writes in production. Tests point it at a named
    graph of their own instead.
    """

    query_url: str
    update_url: str
    graph: Optional[str] = None
    auth: Optional[tuple] = None
    timeout: float = DEFAULT_TIMEOUT_SECONDS
    session: requests.Session = field(
        default_factory=requests.Session, repr=False, compare=False
    )

    @classmethod
    def from_settings(cls, *, graph=USE_CONFIGURED_GRAPH) -> "GraphStore":
        """Build the store the platform is configured to talk to.

        ``graph`` defaults to ``settings.OEKG_GRAPH``, which is ``None`` -- the
        default graph, where the platform's bundles live. A test overrides that
        setting to work in a graph of its own without reaching into the views.
        Passing ``graph=None`` explicitly means the default graph and ignores
        the setting.
        """
        rdf = settings.RDF_DATABASES["knowledge"]
        if graph is USE_CONFIGURED_GRAPH:
            graph = getattr(settings, "OEKG_GRAPH", None)
        base = "http://{host}:{port}/{name}".format(
            host=rdf["host"], port=rdf["port"], name=rdf["name"]
        )
        # Credentials are sent whenever they are configured. The existing
        # connection module gates this on USE_DOCKER, which makes the transport
        # behave differently between environments for no stated reason.
        user, password = rdf.get("user"), rdf.get("password")
        return cls(
            query_url=f"{base}/query",
            update_url=f"{base}/update",
            graph=graph,
            auth=(user, password) if user and password else None,
        )

    # ------------------------------------------------------------------ reads

    def select(self, query: str) -> list:
        """Run a SELECT and return its bindings as plain dicts of strings."""
        payload = self._query(query, SELECT_RESULTS).json()
        return [
            {name: binding[name]["value"] for name in binding}
            for binding in payload["results"]["bindings"]
        ]

    def ask(self, query: str) -> bool:
        """Run an ASK."""
        return bool(self._query(query, SELECT_RESULTS).json()["boolean"])

    def construct(self, query: str) -> Graph:
        """Run a CONSTRUCT or DESCRIBE and return the triples as a graph."""
        response = self._query(query, CONSTRUCT_RESULTS)
        graph = Graph()
        graph.parse(data=response.text, format="turtle")
        return graph

    # ----------------------------------------------------------------- writes

    def update(self, *operations: str) -> None:
        """Send SPARQL update operations as **one** request, so one transaction.

        The operations are the caller's own SPARQL and are sent as written --
        **this method does not scope them to the target graph.** Use
        ``insert_data``, ``delete_data`` and ``guarded_modification`` to build
        scoped operations; reach for a hand-written one only where no builder
        exists yet, and scope it yourself. An unscoped ``INSERT DATA`` writes
        the default graph whatever this store targets.
        """
        if not operations:
            return
        self._post(
            self.update_url, {"update": " ;\n".join(operations)}, GraphUpdateRejected
        )

    def insert(self, triples: Graph) -> None:
        """Write every triple in ``triples`` in one request."""
        self.update(self.insert_data(triples))

    def insert_data(self, triples: Graph) -> str:
        """The INSERT DATA operation for ``triples``, scoped to the target graph.

        Returned rather than sent, so several operations can be combined into
        the single request that makes them atomic.
        """
        return f"INSERT DATA {{ {self._in_target_graph(triples)} }}"

    def delete_data(self, triples: Graph) -> str:
        """The DELETE DATA operation for ``triples``, scoped to the target graph."""
        return f"DELETE DATA {{ {self._in_target_graph(triples)} }}"

    def guarded_modification(
        self,
        where: str,
        delete: Optional[Graph] = None,
        insert: Optional[Graph] = None,
    ) -> str:
        """A DELETE/INSERT/WHERE operation, scoped to the target graph.

        ``where`` is the guard, and it is part of the write rather than a check
        in front of it: SPARQL applies the templates only if the pattern
        matches, so a compare-and-set cannot be overtaken between the test and
        the change. The price is that a guard that does not match is
        indistinguishable from one that does -- the store answers ``200`` and
        changes nothing either way -- so the caller has to read back for the
        signal. That is not a shortcoming of this method; it is what SPARQL
        update offers.

        Scoping is by ``WITH``, which makes the target graph the default for
        every unqualified pattern in all three clauses at once. Writing
        ``GRAPH`` blocks instead would put the same decision in three places,
        and forgetting one of them writes the default graph -- in production,
        the graph the platform serves.
        """
        clauses = []
        if delete is not None and len(delete):
            clauses.append(f"DELETE {{ {delete.serialize(format='nt')} }}")
        if insert is not None and len(insert):
            clauses.append(f"INSERT {{ {insert.serialize(format='nt')} }}")
        if not clauses:
            # A guard with nothing behind it would still be a valid request the
            # store answers 200 to, which is the one answer a caller must never
            # read as "the guard held".
            raise NothingToModifyError(
                "A guarded modification needs triples to delete or to insert."
            )
        prefix = f"WITH <{self.graph}>\n" if self.graph else ""
        return f"{prefix}{' '.join(clauses)} WHERE {{ {where} }}"

    def clear(self) -> None:
        """Remove this store's named graph. Refuses on the default graph.

        DROP rather than CLEAR: CLEAR empties a graph but leaves it in the
        store, so a persistent dataset would accumulate one empty graph per
        test per run.
        """
        if not self.graph:
            raise UnsafeClearError(
                "Refusing to clear the default graph: this store targets the "
                "graph the platform itself uses. Build a GraphStore with a "
                "named graph to clear it."
            )
        self.update(f"DROP SILENT GRAPH <{self.graph}>")

    # ---------------------------------------------------------------- probing

    def is_available(self) -> bool:
        """Whether this store can actually be read from and written to.

        Probed with a harmless no-op update rather than a read, because the two
        are not the same permission: Fuseki serves queries to anyone and answers
        updates with 401 unless credentials are valid. A read-only probe would
        report a store as usable and leave the write tests failing instead of
        skipping.

        Never raises -- the caller is deciding whether to skip.
        """
        try:
            self.session.post(
                self.update_url,
                data={"update": f"DROP SILENT GRAPH <{AVAILABILITY_PROBE_GRAPH}>"},
                auth=self.auth,
                timeout=AVAILABILITY_TIMEOUT_SECONDS,
            ).raise_for_status()
        except requests.RequestException:
            return False
        return True

    # --------------------------------------------------------------- internal

    def _in_target_graph(self, triples: Graph) -> str:
        body = triples.serialize(format="nt")
        if self.graph:
            return f"GRAPH <{self.graph}> {{ {body} }}"
        return body

    def _query(self, query: str, accept: str) -> requests.Response:
        parameters = {"query": query}
        if self.graph:
            # Scoping by protocol parameter rather than by rewriting the query,
            # so callers write plain SPARQL and the store decides where it runs.
            parameters["default-graph-uri"] = self.graph
        return self._post(self.query_url, parameters, GraphQueryRejected, accept=accept)

    def _post(
        self,
        url: str,
        data: dict,
        rejection: type,
        accept: Optional[str] = None,
    ) -> requests.Response:
        headers = {"Accept": accept} if accept else {}
        try:
            response = self.session.post(
                url, data=data, headers=headers, auth=self.auth, timeout=self.timeout
            )
        except requests.RequestException as error:
            raise GraphStoreUnavailable(
                f"The OEKG graph store at {url} could not be reached."
            ) from error

        if response.status_code >= 400:
            # The body is the store's, not ours: Fuseki's parser dump echoes the
            # generated query back, which would leak it to whoever sees the
            # error. Log it where operators can read it and raise without it.
            logger.error(
                "OEKG graph store refused a %s: HTTP %s from %s -- %s",
                rejection.action,
                response.status_code,
                url,
                response.text[:2000],
            )
            raise rejection(
                f"The OEKG graph store refused this {rejection.action} "
                f"(HTTP {response.status_code}). {rejection.detail}".strip()
            )
        return response
