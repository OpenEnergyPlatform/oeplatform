"""Repair what a machine can know about the OEKG's shape violations.

Measured against a real export (13,700 triples, 55 scenario bundles): **none of
them satisfies the canonical shape**. About half the violations a machine can
fix; the rest are missing *content* -- which sector a study covers, who wrote a
publication -- and nobody can infer those. So this repairs the first half and
says plainly how much is left.

Three repairs, and they are **not equally safe**, which is why each is named
separately and reported separately:

- ``types`` adds a missing ``rdf:type`` to a node that is already referenced as
  one. It asserts nothing that was not already implied by the reference.
- ``duplicate-references`` removes surplus references from a region, which the
  shape allows only one of. **This destroys data**: one of them was somebody's
  entry and the command keeps the lexically first, not the right one.
- ``year-dates`` rewrites ``"2020"^^xsd:dateTime`` -- which is not a valid
  dateTime -- as a full timestamp. **This invents precision.** Nobody said
  January the 1st at midnight; the shape demands ``xsd:dateTime`` for a value
  that is a year, which is arguably the shape's problem rather than the data's.
  Recorded on the shape's repository rather than silently normalised here.

**The dry run is the default** and the record is written *before* the graph is
touched, so a path the command cannot write to stops it rather than leaving a
change with no account of itself. The graph write is a single SPARQL request,
which is a single transaction: it all lands or none of it does.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import json
import re
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from rdflib import RDF, Graph, Literal, URIRef
from rdflib.namespace import XSD

from oekg.bundles import OEO
from oekg.graph_store import GraphStore, GraphStoreError

HAS_REFERENCE = OEO.OEO_00390078
REFERENCE_CLASS = OEO.OEO_00000353

TYPES = "types"
DUPLICATE_REFERENCES = "duplicate-references"
YEAR_DATES = "year-dates"
REPAIRS = (TYPES, DUPLICATE_REFERENCES, YEAR_DATES)

# The repairs that only ever add, and can be run without thinking twice.
SAFE = (TYPES,)

YEAR_ONLY = re.compile(r"^\d{4}$")


class Command(BaseCommand):
    help = (
        "Repair the OEKG shape violations a machine can fix. Prints what it "
        "would do unless --apply is given."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help=(
                "Actually write to the graph. Without it the command only "
                "reports, which is the default because two of the three "
                "repairs lose or invent information."
            ),
        )
        parser.add_argument(
            "--repair",
            action="append",
            choices=REPAIRS,
            help=(
                "Which repair to run; repeatable. Defaults to the ones that "
                f"only add: {', '.join(SAFE)}. The others have to be asked for "
                "by name."
            ),
        )
        parser.add_argument(
            "--record",
            default=None,
            help=(
                "Where to write the JSON record of every triple added and "
                "removed. Written before the graph is touched, by a real run "
                "only. Defaults to oekg-shape-repair-<timestamp>.json here."
            ),
        )

    def handle(self, *args, **options):
        chosen = tuple(options["repair"] or SAFE)
        store = GraphStore.from_settings()

        try:
            graph = store.construct("CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }")
        except GraphStoreError as error:
            raise CommandError(f"The OEKG graph store could not be read: {error}")

        added, removed, notes = Graph(), Graph(), []
        if TYPES in chosen:
            self._type_references(graph, added, notes)
        if DUPLICATE_REFERENCES in chosen:
            self._drop_surplus_references(graph, removed, notes)
        if YEAR_DATES in chosen:
            self._normalise_years(graph, added, removed, notes)

        self._report(chosen, added, removed, notes)
        if not (len(added) or len(removed)):
            self.stdout.write("Nothing to repair.")
            return

        if not options["apply"]:
            self.stdout.write(
                "\nThis was a dry run: the graph was not touched and no record "
                "was written. Re-run with --apply to repair."
            )
            return

        path = Path(
            options["record"]
            or f"oekg-shape-repair-{datetime.now():%Y%m%dT%H%M%S}.json"
        )
        # The record goes first: a repair whose account could not be written is
        # a change nobody can undo, and that is worse than not repairing.
        path.write_text(
            json.dumps(
                {
                    "repairs": list(chosen),
                    "added": _triples(added),
                    "removed": _triples(removed),
                    "notes": notes,
                },
                indent=2,
            )
        )

        operations = []
        if len(removed):
            operations.append(store.delete_data(removed))
        if len(added):
            operations.append(store.insert_data(added))
        try:
            # One request, so one transaction: all of it or none of it.
            store.update(*operations)
        except GraphStoreError as error:
            raise CommandError(
                f"Nothing was changed -- the graph store refused the write: "
                f"{error}. The record at {path} describes what was attempted."
            )
        self.stdout.write(f"\nRepaired. The record is at {path}.")

    # ------------------------------------------------------------- repairs

    def _type_references(self, graph, added, notes):
        """A node referenced as a reference is one; say so."""
        for _, obj in graph.subject_objects(HAS_REFERENCE):
            if (obj, RDF.type, REFERENCE_CLASS) not in graph:
                added.add((obj, RDF.type, REFERENCE_CLASS))

    def _drop_surplus_references(self, graph, removed, notes):
        """The shape allows one reference per region. Keep one, name the rest."""
        for region in set(graph.subjects(HAS_REFERENCE, None)):
            references = sorted(graph.objects(region, HAS_REFERENCE), key=str)
            for surplus in references[1:]:
                removed.add((region, HAS_REFERENCE, surplus))
                notes.append(
                    f"{region} kept {references[0]} and lost {surplus}; the "
                    "shape allows one reference and nothing says which."
                )

    def _normalise_years(self, graph, added, removed, notes):
        """`"2020"^^xsd:dateTime` is not a dateTime. Making it one invents a day."""
        for subject, predicate, obj in graph:
            if not isinstance(obj, Literal) or obj.datatype != XSD.dateTime:
                continue
            if not YEAR_ONLY.match(str(obj)):
                continue
            removed.add((subject, predicate, obj))
            added.add(
                (
                    subject,
                    predicate,
                    Literal(f"{obj}-01-01T00:00:00+00:00", datatype=XSD.dateTime),
                )
            )
            notes.append(
                f"{subject} had the year {obj} where the shape wants a "
                "dateTime; it now says the first of January at midnight, which "
                "nobody stated."
            )

    # -------------------------------------------------------------- report

    def _report(self, chosen, added, removed, notes):
        self.stdout.write(f"Repairs selected: {', '.join(chosen)}")
        self.stdout.write(f"  triples to add:    {len(added)}")
        self.stdout.write(f"  triples to remove: {len(removed)}")
        for note in notes:
            self.stdout.write(f"  ! {note}")
        skipped = [name for name in REPAIRS if name not in chosen]
        if skipped:
            self.stdout.write(
                f"\nNot selected: {', '.join(skipped)}. Ask for them by name "
                "with --repair if you want them."
            )


def _triples(graph: Graph) -> list:
    return [
        [str(s), str(p), _term(o)]
        for s, p, o in sorted(graph, key=lambda triple: tuple(str(t) for t in triple))
    ]


def _term(node) -> dict:
    if isinstance(node, URIRef):
        return {"iri": str(node)}
    return {
        "literal": str(node),
        "datatype": str(node.datatype) if node.datatype else None,
    }
