"""The bundle collection: summaries, filtered and paged in the store.

A listing is not a bundle read repeated. **Each entry carries an identifier, an
acronym, a label, a version and counts** -- enough to find a bundle and decide
which one, and nothing else. The full bundle is fetched at its own URL.

Three properties follow from that and are the point of the module:

- **No per-item follow-up.** One query answers a whole page, counts included.
  The user interface's own listing asks one further question per bundle for its
  scenarios, which is the pattern this replaces rather than reuses.
- **No relational lookups at all.** A summary carries no dataset links, so the
  resolution a bundle read does against Postgres never runs on a listing.
- **No unbounded mode.** This is a public, unauthenticated endpoint: it is
  paged by default and the page size has a ceiling. Counting and paging both
  happen in the store, so the cost of a listing does not grow with the corpus.

Two queries, not one: the page and the total. That is the deliberate reading of
"one query" -- what the listing must never become is *one query per item*, and
a total is O(1) queries however large the corpus grows. The alternative, a
`LIMIT n+1` probe, would leave every client unable to say how many bundles
matched.

**The filter set is the user interface's, in this API's vocabulary.** Same
filters -- organisation, funder, author, descriptor, scenario year, publication
year -- named as the payload names those fields, because a client reading a
bundle should not meet a second set of words for the same things. Each
predicate is taken from the field tables rather than retyped, so a filter
cannot come to mean something the write path does not.

`?acronym=` is the one filter the contract depends on: a stateless pipeline
re-identifies its bundle through it, and the `_meta` it gets back carries the
version its next write has to send.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from dataclasses import dataclass
from typing import Optional

from drf_spectacular.utils import OpenApiParameter
from rdflib import RDFS, Literal, URIRef
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from oekg.acronyms import ACRONYM
from oekg.api_support import Refused
from oekg.bundles import (
    BUNDLE_CLASS,
    BUNDLE_FIELDS,
    SCENARIO,
    SCENARIO_FIELDS,
    STUDY_REPORT,
    STUDY_REPORT_FIELDS,
    bundle_uid,
)
from oekg.fields import HAS_PART, field_named
from oekg.graph_store import GraphStore
from oekg.serializers import READ_ONLY_CONTAINER
from oekg.versioning import UNVERSIONED, VERSION, VERSION_OF

# Which predicate each filter asks about, read from the field tables so a
# filter cannot come to mean something a write does not.
ORGANISATION = field_named(BUNDLE_FIELDS, "organisations").predicate
FUNDER = field_named(BUNDLE_FIELDS, "funders").predicate
DESCRIPTOR = field_named(BUNDLE_FIELDS, "descriptors").predicate
AUTHOR = field_named(STUDY_REPORT_FIELDS, "authors").predicate
SCENARIO_YEAR = field_named(SCENARIO_FIELDS, "years").predicate
PUBLICATION_DATE = field_named(STUDY_REPORT_FIELDS, "publication_date").predicate


class ScenarioBundlePagination(PageNumberPagination):
    """A ceiling, not a default. The public endpoint has no unbounded mode.

    `page` and `page_size`, like every other collection in this API, rather
    than the user interface's `resultsPerPage`: meeting two conventions inside
    one API is worse for a client than meeting one that differs from a legacy
    view it does not call.
    """

    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 100


@dataclass(frozen=True)
class SummaryFilters:
    """What a listing was asked to narrow itself to.

    Repeating a parameter widens that filter; different parameters narrow each
    other. So `?organisation=A&organisation=B&funder=C` means *(A or B) and C*,
    which is what a faceted interface means by ticking two boxes in one facet.
    """

    acronym: Optional[str] = None
    organisations: tuple = ()
    funders: tuple = ()
    authors: tuple = ()
    descriptors: tuple = ()
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    published_from: Optional[int] = None
    published_to: Optional[int] = None

    @classmethod
    def from_query(cls, params) -> "SummaryFilters":
        """Read them off the query string, refusing what cannot be one.

        Raises ``Refused`` with a `400` rather than ignoring a value it cannot
        use: a filter silently dropped answers with more bundles than were
        asked for, which a client cannot tell from there being more.
        """
        return cls(
            acronym=params.get("acronym") or None,
            organisations=_iris(params, "organisation"),
            funders=_iris(params, "funder"),
            authors=_iris(params, "author"),
            descriptors=_iris(params, "descriptor"),
            year_from=_year(params, "year_from"),
            year_to=_year(params, "year_to"),
            published_from=_year(params, "published_from"),
            published_to=_year(params, "published_to"),
        )


def _filter(name, description, many=True):
    return OpenApiParameter(
        name=name,
        location=OpenApiParameter.QUERY,
        required=False,
        type=str,
        description=description
        + (
            " Repeating this parameter widens it; different parameters narrow "
            "each other, which is what a faceted interface means by ticking "
            "two boxes in one facet."
            if many
            else ""
        ),
    )


def _year_filter(name, description):
    return OpenApiParameter(
        name=name,
        location=OpenApiParameter.QUERY,
        required=False,
        type=int,
        description=description + " Either end of the range may be given alone.",
    )


#: Declared beside the parser that reads them, so a filter cannot appear in the
#: description under a name `from_query` does not answer to. Each takes IRIs
#: rather than labels wherever the payload does, so a filter can be built out
#: of a bundle a client just read.
LISTING_FILTERS = [
    _filter(
        "acronym",
        "Only the bundle carrying exactly this acronym. **The filter the "
        "contract depends on**: it is how a pipeline holding no state between "
        "runs finds its own bundle again, and the `_meta` it gets back carries "
        "the version its next write has to send.",
        many=False,
    ),
    _filter("organisation", "The IRI of an organisation a bundle names."),
    _filter("funder", "The IRI of a funder a bundle names."),
    _filter("author", "The IRI of an author of one of a bundle's study reports."),
    _filter("descriptor", "The IRI of a descriptor a bundle is tagged with."),
    _year_filter("year_from", "Bundles with a scenario year at or after this."),
    _year_filter("year_to", "Bundles with a scenario year at or before this."),
    _year_filter(
        "published_from", "Bundles with a study report published in this year or later."
    ),
    _year_filter(
        "published_to", "Bundles with a study report published in this year or earlier."
    ),
]


class BundleSummaries:
    """Every bundle matching these filters -- counted and sliced in the store.

    A sequence in the two ways a paginator uses one, and in no other: it
    answers how many there are and hands back one window. Django's paginator
    then does the arithmetic and this API's clients get the same paged shape
    they get everywhere else, without a page ever being cut out of a list that
    was fetched whole.
    """

    def __init__(self, store: GraphStore, filters: SummaryFilters):
        self.store = store
        self.filters = filters

    def count(self) -> int:
        rows = self.store.select(
            "SELECT (COUNT(DISTINCT ?bundle) AS ?total) WHERE { %s }"
            % _where(self.filters)
        )
        return int(rows[0]["total"]) if rows else 0

    def __getitem__(self, window: slice) -> list:
        offset = window.start or 0
        return [
            _summary(row)
            for row in self.store.select(
                _page_query(self.filters, offset, window.stop - offset)
            )
        ]


def _summary(row: dict) -> dict:
    """One row of the page query, as the body a client reads.

    The two fields a human recognises a bundle by stay at the top level, where
    a bundle read also has them; everything a client cannot write -- the
    identifier, the version, the counts -- is in the read-only container, which
    is where this API puts read-only data everywhere else.
    """
    iri = row["bundle"]
    return {
        "label": row.get("label"),
        "acronym": row.get("acronym"),
        READ_ONLY_CONTAINER: {
            "uid": bundle_uid(iri),
            "iri": iri,
            "version": int(row.get("version") or UNVERSIONED),
            "counts": {
                SCENARIO.payload_key: int(row.get("scenarios") or 0),
                STUDY_REPORT.payload_key: int(row.get("study_reports") or 0),
            },
        },
    }


def _page_query(filters: SummaryFilters, offset: int, limit: int) -> str:
    """One page of summaries, counts included, in one query.

    **Grouped by the bundle alone, and everything else sampled.** Grouping by
    the label and the acronym as well would be one row per *combination*, so a
    bundle carrying two acronyms -- which the shape forbids and the live graph
    nonetheless contains, none of its bundles conforming -- would take two rows
    out of a page while the total counted it once. The page would then be
    longer than the total claims and the window would shift under the next
    page. Sampling picks one and the page stays one row per bundle.

    The counts are `COUNT(DISTINCT ...)` for the sibling reason: the filters
    join, so a bundle matching two of the organisations asked for appears twice
    before grouping, and a count that did not say DISTINCT would report twice
    as many scenarios for it as it has.
    """
    return """
        SELECT ?bundle
               (SAMPLE(?acronymValue) AS ?acronym)
               (SAMPLE(?labelValue) AS ?label)
               (SAMPLE(?versionValue) AS ?version)
               (COUNT(DISTINCT ?scenarioPart) AS ?scenarios)
               (COUNT(DISTINCT ?reportPart) AS ?study_reports)
        WHERE {
          %(where)s
          OPTIONAL { ?bundle %(acronym)s ?acronymValue }
          OPTIONAL { ?bundle %(label)s ?labelValue }
          OPTIONAL {
            ?versionNode %(versionOf)s ?bundle ; %(version)s ?versionValue
          }
          OPTIONAL { ?bundle %(hasPart)s ?scenarioPart . ?scenarioPart a %(scenario)s }
          OPTIONAL { ?bundle %(hasPart)s ?reportPart . ?reportPart a %(report)s }
        }
        GROUP BY ?bundle
        ORDER BY ?acronym ?bundle
        LIMIT %(limit)d OFFSET %(offset)d
    """ % {
        "where": _where(filters),
        "acronym": ACRONYM.n3(),
        "label": RDFS.label.n3(),
        "versionOf": VERSION_OF.n3(),
        "version": VERSION.n3(),
        "hasPart": HAS_PART.n3(),
        "scenario": SCENARIO.node_class.n3(),
        "report": STUDY_REPORT.node_class.n3(),
        "limit": limit,
        "offset": offset,
    }


def _where(filters: SummaryFilters) -> str:
    """The patterns a bundle has to match. Shared by the count and the page.

    One function for both, so a total can never describe a different set of
    bundles than the page it is counting.
    """
    clauses = ["?bundle a %s ." % BUNDLE_CLASS.n3()]
    if filters.acronym is not None:
        clauses.append(
            "?bundle %s %s ." % (ACRONYM.n3(), Literal(filters.acronym).n3())
        )
    clauses.append(_any_of("?organisation", ORGANISATION, filters.organisations))
    clauses.append(_any_of("?funder", FUNDER, filters.funders))
    clauses.append(_any_of("?descriptor", DESCRIPTOR, filters.descriptors))
    if filters.authors:
        clauses.append(
            "?bundle %s ?authorReport . ?authorReport a %s ."
            % (HAS_PART.n3(), STUDY_REPORT.node_class.n3())
        )
        clauses.append(_any_of("?author", AUTHOR, filters.authors, "?authorReport"))
    clauses.append(
        _within_years(
            SCENARIO.node_class,
            SCENARIO_YEAR,
            "scenarioYear",
            filters.year_from,
            filters.year_to,
        )
    )
    clauses.append(
        _within_years(
            STUDY_REPORT.node_class,
            PUBLICATION_DATE,
            "publication",
            filters.published_from,
            filters.published_to,
        )
    )
    return " ".join(clause for clause in clauses if clause)


def _any_of(variable: str, predicate, iris: tuple, subject: str = "?bundle") -> str:
    """``subject`` points at one of ``iris`` -- or no constraint at all."""
    if not iris:
        return ""
    return "VALUES %s { %s } %s %s %s ." % (
        variable,
        " ".join(URIRef(iri).n3() for iri in iris),
        subject,
        predicate.n3(),
        variable,
    )


def _within_years(node_class, predicate, name: str, first, last) -> str:
    """A bundle holding a part whose date falls in this range.

    Either end alone is a range: the user interface's own blocks need both and
    silently drop the filter given one, which then answers with every bundle
    rather than with the half that was asked for.

    ``name`` distinguishes this filter's variables from every other filter's in
    the same query -- two filters sharing a variable would silently require one
    node to satisfy both.
    """
    if first is None and last is None:
        return ""
    node, date, year = f"?{name}Part", f"?{name}Date", f"?{name}Year"
    bounds = []
    if first is not None:
        bounds.append(f"{year} >= {first:d}")
    if last is not None:
        bounds.append(f"{year} <= {last:d}")
    return "?bundle %s %s . %s a %s ; %s %s . BIND(YEAR(%s) AS %s) FILTER(%s)" % (
        HAS_PART.n3(),
        node,
        node,
        node_class.n3(),
        predicate.n3(),
        date,
        date,
        year,
        " && ".join(bounds),
    )


def _iris(params, name: str) -> tuple:
    """Repeated IRI values for one filter, refusing anything that is not one.

    rdflib refuses to serialise an IRI carrying a space, a quote or an angle
    bracket, which is both the validation and the reason nothing here can be
    talked into ending a pattern early.
    """
    values = params.getlist(name)
    for value in values:
        try:
            URIRef(value).n3()
        except Exception:
            raise Refused(
                Response(
                    {
                        "detail": (
                            f"{value!r} is not an IRI, so it cannot be a "
                            f"{name} to filter by."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            )
    return tuple(values)


def _year(params, name: str) -> Optional[int]:
    value = params.get(name)
    if value in (None, ""):
        return None
    try:
        return int(value)
    except ValueError:
        raise Refused(
            Response(
                {"detail": f"{value!r} is not a year, so it cannot be {name}."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        )
