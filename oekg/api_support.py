"""What every endpoint of the OEKG API shares: its ceilings and its refusals.

Extracted when the second view module appeared and had to import five names
from the first. That import is the signal: helpers every endpoint needs are not
the bundle endpoint's property, and five more view modules are coming --
scenarios, study reports, dataset links, delete, replace. Left where they were,
`api_views` would become a utility module by accident, and would change
whenever any endpoint's conventions changed.

What belongs here: throttling, the refusals more than one endpoint gives, and
the existence check they all make first. What does not: anything specific to
one resource, which stays with that resource's view.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import logging
import uuid

from rest_framework import status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from oekg.bundles import BUNDLE_CLASS, bundle_iri
from oekg.graph_store import GraphStore

logger = logging.getLogger("oeplatform")


class Refused(Exception):
    """A refusal, raised where it is decided and returned as it stands.

    It carries a whole ``Response`` rather than a detail, and `OekgAPIView`
    hands that back untouched. Both halves of that are deliberate:

    - **Raised, not returned.** A helper that returned either a value or a
      refusal would make every call site test which it got, and one forgotten
      test is a refusal silently ignored.
    - **A Response, not an ``APIException``.** The obvious alternative is to
      subclass ``APIException`` and let the framework render it -- but the
      framework rewrites every scalar in an error body through
      ``ErrorDetail``, so ``None`` comes out as the string ``"None"`` and a
      count as a string. This API's refusals carry structured data with
      nullable fields, so that would corrupt them. Measured, not assumed.
    """

    def __init__(self, response: Response):
        super().__init__(getattr(response, "status_code", "refused"))
        self.response = response


class ScenarioBundleThrottle(AnonRateThrottle):
    """Reads are public, so the public endpoints need a ceiling of their own."""

    scope = "oekg_bundles_anon"


class ScenarioBundleUserThrottle(UserRateThrottle):
    scope = "oekg_bundles_user"


class OekgAPIView(APIView):
    """The base every OEKG endpoint shares: one ceiling, one way to refuse.

    Handling `Refused` here rather than in each view means a new endpoint
    cannot forget to, and a refusal decided three calls deep still reaches the
    client as the response it was written as.
    """

    throttle_classes = [ScenarioBundleThrottle, ScenarioBundleUserThrottle]

    def handle_exception(self, exc):
        if isinstance(exc, Refused):
            return exc.response
        return super().handle_exception(exc)


def is_minted_identifier(uid: str) -> bool:
    """Whether ``uid`` could have come from this API.

    Checked before a value reaches a query: an IRI-unsafe character makes
    rdflib refuse to build the IRI, which would surface as a 500 rather than
    the 404 it actually is. That refusal is also what keeps the query free of
    injection.
    """
    try:
        uuid.UUID(str(uid))
    except (ValueError, AttributeError, TypeError):
        return False
    return True


def bundle_exists(uid: str) -> bool:
    """Whether there is a bundle at ``uid``. Asked of the graph, not of a table.

    Raises ``GraphStoreError`` rather than answering ``False`` when the store
    cannot be reached: "there is no such bundle" and "I could not find out" are
    different answers, and a caller has to be able to say 503 instead of 404.

    An ASK rather than the read a GET does -- this asks whether the bundle is
    there, and pulling its whole subgraph across to answer that would make
    every caller pay for data it throws away.
    """
    if not is_minted_identifier(uid):
        return False
    return bundle_in(GraphStore.from_settings(), uid)


def bundle_in(store: GraphStore, uid: str) -> bool:
    """The same question, asked of a store the caller already has.

    Separate from `bundle_exists` because a delete has to ask it of **its own**
    store, inside its own request, and because the two must not drift: a write
    reads this back to find out whether its delete applied, and a query that
    had drifted would report a success that did not happen.
    """
    return store.ask("ASK { %s a %s }" % (bundle_iri(uid).n3(), BUNDLE_CLASS.n3()))


def no_such_bundle(uid: str) -> Response:
    return Response(
        {"detail": f"No scenario bundle {uid}."}, status=status.HTTP_404_NOT_FOUND
    )


def store_unavailable(error: Exception, action: str) -> Response:
    logger.error("OEKG API %s failed: %s", action, error)
    return Response(
        {"detail": f"The OEKG graph store could not be {action}."},
        status=status.HTTP_503_SERVICE_UNAVAILABLE,
    )


def shape_unavailable(error: Exception) -> Response:
    logger.error("OEKG API cannot validate: %s", error)
    return Response(
        {"detail": "The OEKG shape is not available on this server."},
        status=status.HTTP_503_SERVICE_UNAVAILABLE,
    )
