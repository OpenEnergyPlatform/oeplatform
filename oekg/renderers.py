"""Serving a bundle as RDF, because that is the form the store actually holds.

Structured data is canonical here: the serializers are the validation layer, so
a **write** is JSON and nothing else. A **read** is different -- the subgraph
has already been constructed by the time a response is built, so the RDF form
is one `serialize()` away, and it is the lossless one. The serializer layer
expresses about 61% of the shape; the graph expresses all of it.

Two things these renderers do beyond calling `serialize`:

- **They fall back to JSON when the data is not a graph.** A `404`, a refusal
  or a throttle on a request that asked for turtle still has to say something,
  and an error body is a dict. It is rendered as JSON and the response's own
  content type is corrected to match, so nothing claims to be turtle and is
  not.
- **They are offered on safe methods only** (see `ScenarioBundleAPIView`), so a
  `PATCH` asking for turtle is a plain `406` rather than a write whose answer
  silently arrives in a different form than the read did.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from rdflib import Graph
from rest_framework.renderers import BaseRenderer, JSONRenderer


class GraphRenderer(BaseRenderer):
    """Serialise an `rdflib.Graph`, or hand anything else to JSON."""

    charset = "utf-8"
    rdflib_format = None

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if isinstance(data, Graph):
            return data.serialize(format=self.rdflib_format)
        # Not a graph, so this is an error body. Say JSON and mean it: the
        # response's content type is set before render() is called, which is
        # what makes correcting it here possible at all.
        response = (renderer_context or {}).get("response")
        if response is not None:
            response["Content-Type"] = "application/json"
        return JSONRenderer().render(data, "application/json", renderer_context)


class TurtleRenderer(GraphRenderer):
    media_type = "text/turtle"
    format = "turtle"
    rdflib_format = "turtle"


class JsonLdRenderer(GraphRenderer):
    media_type = "application/ld+json"
    format = "json-ld"
    rdflib_format = "json-ld"


# Both RDF forms the old whole-graph routes already offered, so a client that
# used those meets no new vocabulary here.
RDF_RENDERERS = (TurtleRenderer, JsonLdRenderer)
RDF_FORMATS = frozenset(renderer.format for renderer in RDF_RENDERERS)
