"""Build-time artifacts the OEKG REST API validates against.

Two files, one seam. The canonical SHACL shape for scenario bundles is fetched
from the ``oekg`` repository at a **pinned** revision, and the small
``rdfs:label`` subset that validation needs is generated from the OEO release
already on disk. ``manage.py fetch_oekg_shapes`` is the only caller; nothing
else in the platform obtains either file.

Why pinned, and why refused otherwise: an unpinned fetch would change the
*validator* without a deploy. The URL is assembled here from a repository, a
:class:`PinnedRef` and a path, so there is no way to pass a branch URL in.

Why the label subset rather than the ontology: ``ex:CommonShape`` requires
exactly one ``rdfs:label`` on every OEO term a bundle picks, so validation needs
labels -- but only labels. The ``rdfs:label``-only subset of ``oeo-full.owl`` is
~2,000 triples and under 200 KB, against 1.3 GB of resident memory and ~36 s to
parse the ontology itself.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

import requests
from rdflib import RDF, RDFS, Graph, URIRef
from rdflib.namespace import SH

RAW_GITHUB_HOST = "https://raw.githubusercontent.com"

FETCH_TIMEOUT_SECONDS = 30

# The shape is ~18 KB. A cap this generous still catches a redirect to a login
# page or an error document being written to disk as "the validator".
MAX_FETCH_BYTES = 5 * 1024 * 1024

COMMIT_SHA_PATTERN = re.compile(r"^[0-9a-f]{7,40}$")

# Names that move. A tag can be force-pushed too, which is why the error message
# says the source repo must treat tags as immutable -- but these names are
# mutable by convention and are the realistic mistake.
MOVING_REF_NAMES = frozenset(
    {
        "head",
        "latest",
        "main",
        "master",
        "develop",
        "development",
        "dev",
        "production",
        "prod",
        "staging",
        "release",
        "current",
        "stable",
    }
)


class ShapeArtifactError(Exception):
    """Base class for every way obtaining an artifact can fail."""


class UnpinnedSourceError(ShapeArtifactError, ValueError):
    """The requested revision is not, or cannot be shown to be, pinned."""


class NotAShapeError(ShapeArtifactError):
    """The fetched body is not a parseable SHACL shape graph."""


class MissingOntologyError(ShapeArtifactError):
    """The OEO release the label subset is generated from is not on disk."""


class EmptyLabelSubsetError(ShapeArtifactError):
    """The OEO release carries no labels, so the subset would be useless."""


@dataclass(frozen=True)
class PinnedRef:
    """A revision that cannot move under us: a commit sha, or a git tag.

    Constructed only through :meth:`commit` and :meth:`tag`, so the caller has
    to say which kind it means. A branch name is therefore not expressible --
    the point of the class.
    """

    kind: str
    value: str

    @classmethod
    def commit(cls, value: str) -> "PinnedRef":
        value = (value or "").strip()
        if not COMMIT_SHA_PATTERN.match(value):
            raise UnpinnedSourceError(
                f"{value!r} is not a commit sha, so the source is not pinned. "
                "Pass --commit with 7 to 40 lowercase hex characters, or "
                "--tag with a tag name."
            )
        return cls(kind="commit", value=value)

    @classmethod
    def tag(cls, value: str) -> "PinnedRef":
        value = (value or "").strip()
        if not value or "/" in value or ".." in value or value.startswith("-"):
            raise UnpinnedSourceError(
                f"{value!r} is not usable as a pinned tag name. Pass a plain "
                "tag, e.g. --tag v1.2.0."
            )
        lowered = value.lower()
        if lowered in MOVING_REF_NAMES or "latest" in lowered:
            raise UnpinnedSourceError(
                f"{value!r} names a moving revision, so the source would not "
                "be pinned and the validator could change without a deploy. "
                "Pass an immutable tag or --commit <sha>."
            )
        return cls(kind="tag", value=value)

    def __str__(self) -> str:
        return f"{self.kind} {self.value}"


@dataclass(frozen=True)
class ArtifactWrite:
    """What one artifact write did, so a deploy log can say whether it moved."""

    path: Path
    status: str  # "created" | "updated" | "unchanged"
    sha256: str
    size: int

    @property
    def changed(self) -> bool:
        return self.status != "unchanged"

    def __str__(self) -> str:
        return (
            f"{self.status} {self.path} "
            f"({self.size} bytes, sha256 {self.sha256[:12]})"
        )


def raw_github_url(repo: str, ref: PinnedRef, path_in_repo: str) -> str:
    """Build the raw URL for one file in ``repo`` at a pinned revision."""
    return f"{RAW_GITHUB_HOST}/{repo}/{ref.value}/{path_in_repo}"


def read_url_bytes(url: str) -> bytes:
    """Read a URL into memory. The one place this module touches the network."""
    response = requests.get(url, timeout=FETCH_TIMEOUT_SECONDS)
    response.raise_for_status()
    payload = response.content
    if len(payload) > MAX_FETCH_BYTES:
        raise NotAShapeError(
            f"{url} returned {len(payload)} bytes, more than the "
            f"{MAX_FETCH_BYTES} byte ceiling for a shape file."
        )
    return payload


def write_artifact(destination: Path, payload: bytes) -> ArtifactWrite:
    """Put ``payload`` at ``destination`` atomically, reporting what changed.

    Writes a sibling temporary file and renames it, so an interrupted run leaves
    the previously fetched artifact in place rather than a truncated one.
    """
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(payload).hexdigest()

    if destination.exists() and destination.read_bytes() == payload:
        return ArtifactWrite(destination, "unchanged", digest, len(payload))

    status = "updated" if destination.exists() else "created"
    temporary = destination.with_name(f"{destination.name}.tmp{os.getpid()}")
    try:
        temporary.write_bytes(payload)
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()

    return ArtifactWrite(destination, status, digest, len(payload))


def fetch_shape(
    url: str,
    destination: Path,
    *,
    read_url: Optional[Callable[[str], bytes]] = None,
) -> ArtifactWrite:
    """Fetch the SHACL shape from ``url`` and land it at ``destination``.

    The body is parsed and checked to be a shape graph *before* it is written,
    so an error document or a truncated response never replaces a usable shape.
    """
    reader = read_url or read_url_bytes
    payload = reader(url)
    _reject_if_not_a_shape_graph(payload, url)
    return write_artifact(destination, payload)


def extract_label_subset(oeo_full_owl: Path, destination: Path) -> ArtifactWrite:
    """Generate the ``rdfs:label``-only subset of an OEO release.

    Reads the ontology already on disk -- the full ontology is never fetched --
    and keeps only labels on IRI subjects. Turtle output was checked to be
    byte-stable across runs, which is what makes the "unchanged" report honest.
    """
    oeo_full_owl = Path(oeo_full_owl)
    if not oeo_full_owl.is_file():
        raise MissingOntologyError(
            f"The OEO release file {oeo_full_owl} is missing, so the label "
            "subset cannot be generated. Download the ontology release first."
        )

    ontology = Graph()
    ontology.parse(str(oeo_full_owl))

    subset = Graph()
    subset.bind("rdfs", RDFS)
    for subject, label in ontology.subject_objects(RDFS.label):
        if isinstance(subject, URIRef):
            subset.add((subject, RDFS.label, label))

    if not len(subset):
        raise EmptyLabelSubsetError(
            f"{oeo_full_owl} carries no rdfs:label triples, so the generated "
            "subset would validate nothing. Check the ontology release."
        )

    payload = subset.serialize(format="turtle").encode("utf-8")
    return write_artifact(destination, payload)


def _reject_if_not_a_shape_graph(payload: bytes, url: str) -> None:
    graph = Graph()
    try:
        graph.parse(data=payload, format="turtle")
    except Exception as error:
        raise NotAShapeError(
            f"{url} did not return parseable Turtle ({error}). The previously "
            "fetched shape is untouched."
        ) from error

    if (None, RDF.type, SH.NodeShape) not in graph:
        raise NotAShapeError(
            f"{url} returned Turtle with no sh:NodeShape in it, so it is not "
            "the shape. The previously fetched shape is untouched."
        )
