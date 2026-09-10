"""The canonical SHACL shape, read as data.

The shape is the contract for what a scenario bundle is, and it is still
moving in its own repository. So nothing here is copied into Python: the
enumerations a payload may pick from and the messages a rejection carries are
both read from the artifact ``manage.py fetch_oekg_shapes`` puts on disk.

That artifact is the cache key. A redeploy with a new pin changes the file, and
the file's identity changes with it, so the cache invalidates itself and no
process serves yesterday's enumerations.

Two things this module does NOT do:

- **It does not fall back.** A missing artifact raises rather than validating
  against nothing, because a validator that silently disappears is worse than
  one that is absent loudly.
- **It does not translate.** ``message_for`` returns the shape's own wording,
  so the API and the shape can never disagree about the same rule. The
  validator in use does not honour ``sh:resultMessage`` itself, and relying on
  an engine's leniency for the API's error text would be fragile anyway.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from functools import lru_cache
from pathlib import Path
from typing import Optional

from django.conf import settings
from rdflib import Graph, URIRef
from rdflib.collection import Collection
from rdflib.namespace import SH


class ShapeUnavailable(Exception):
    """The shape artifacts are not on disk, so nothing can be validated."""


def shape_graph() -> Graph:
    """The SHACL shape itself."""
    return _parsed(_fingerprint(Path(settings.OEKG_SHAPES_PATH)))


def label_graph() -> Graph:
    """The rdfs:label subset the shape's targets need to satisfy it."""
    return _parsed(_fingerprint(Path(settings.OEKG_SHAPE_LABELS_PATH)))


def enumeration(property_iri: str) -> frozenset:
    """The IRIs a payload may pick for ``property_iri``, per the shape's sh:in.

    Empty for a property the shape does not constrain by enumeration -- which
    a caller must treat as "not enumerated", never as "nothing is allowed".
    """
    return _shape_enumerations()[0].get(property_iri, frozenset())


def constraint_message(property_iri: str) -> Optional[str]:
    """The shape's own wording for the property shape constraining ``property_iri``.

    Used so a rejected pick is explained in the shape's words rather than in a
    second set written here, which could then disagree with it.
    """
    return _shape_enumerations()[1].get(property_iri)


def message_for(source_shape) -> Optional[str]:
    """The shape's own wording for a violation raised by ``source_shape``."""
    if source_shape is None:
        return None
    message = shape_graph().value(source_shape, SH.resultMessage)
    return str(message) if message is not None else None


def _shape_enumerations() -> tuple:
    return _enumerations(_fingerprint(Path(settings.OEKG_SHAPES_PATH)))


def _fingerprint(path: Path) -> tuple:
    """Identity of an artifact: its path and what a redeploy would change."""
    try:
        stat = path.stat()
    except OSError as error:
        raise ShapeUnavailable(
            f"The OEKG shape artifact {path} is missing. Run "
            "'python manage.py fetch_oekg_shapes' to obtain it; the API "
            "refuses to validate against a shape it does not have."
        ) from error
    return (str(path), stat.st_mtime_ns, stat.st_size)


@lru_cache(maxsize=4)
def _parsed(fingerprint: tuple) -> Graph:
    graph = Graph()
    graph.parse(fingerprint[0], format="turtle")
    return graph


@lru_cache(maxsize=2)
def _enumerations(fingerprint: tuple) -> tuple:
    """Every sh:in list in the shape, and the message beside it.

    Keyed by the property path each constrains, so a caller asks in the
    vocabulary it already has.
    """
    graph = _parsed(fingerprint)
    allowed_by_path = {}
    message_by_path = {}
    for constraint, members in graph.subject_objects(SH["in"]):
        path = graph.value(constraint, SH.path)
        if path is None:
            continue
        allowed = frozenset(
            str(member)
            for member in Collection(graph, members)
            if isinstance(member, URIRef)
        )
        allowed_by_path[str(path)] = (
            allowed_by_path.get(str(path), frozenset()) | allowed
        )
        message = graph.value(constraint, SH.resultMessage)
        if message is not None:
            message_by_path.setdefault(str(path), str(message))
    return allowed_by_path, message_by_path
