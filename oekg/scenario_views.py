"""Scenario factsheets, as endpoints.

Everything these do is in `oekg.part_views`: a scenario is one of the two
things the shape gives its own has-uuid, and being addressable works the same
way for both. What is left here is what is particular to a scenario -- its
`BundlePart` and its serializer -- and two named classes, so a route and a
traceback say *scenario* rather than *part*.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from drf_spectacular.utils import extend_schema, extend_schema_view

from oekg.bundles import SCENARIO
from oekg.part_views import BundlePartAPIView, BundlePartCollectionAPIView
from oekg.serializers import ScenarioSerializer

# A collection read and a detail read of the same resource would otherwise both
# be called `..._retrieve`, and the generator would resolve the collision with
# a numeral -- a name no reader can map back to an endpoint. Named on the
# subclasses because the handlers themselves are shared: one implementation
# serves scenarios and study reports both, and only the subclass knows which.


@extend_schema_view(
    get=extend_schema(operation_id="scenario_bundles_scenarios_list"),
)
class ScenarioCollectionAPIView(BundlePartCollectionAPIView):
    part = SCENARIO
    serializer_class = ScenarioSerializer


@extend_schema_view(
    get=extend_schema(operation_id="scenario_bundles_scenarios_retrieve"),
)
class ScenarioAPIView(BundlePartAPIView):
    part = SCENARIO
    serializer_class = ScenarioSerializer
