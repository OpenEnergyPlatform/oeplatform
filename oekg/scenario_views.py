"""Scenario factsheets, as endpoints.

Everything these do is in `oekg.part_views`: a scenario is one of the two
things the shape gives its own has-uuid, and being addressable works the same
way for both. What is left here is what is particular to a scenario -- its
`BundlePart` and its serializer -- and two named classes, so a route and a
traceback say *scenario* rather than *part*.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from drf_spectacular.utils import extend_schema_view

from oekg.bundles import SCENARIO
from oekg.part_views import (
    BundlePartAPIView,
    BundlePartCollectionAPIView,
    part_detail_operations,
    part_operations,
)
from oekg.read_serializers import ScenarioReadSerializer
from oekg.serializers import ScenarioSerializer

# What the shared handlers cannot say: which serializer their answer has, and
# what to call the thing. Per subclass because it *is* per subclass -- unlike
# the operation ids, which are a rule and live in `CollectionSchema`.


@extend_schema_view(
    **part_operations(
        ScenarioReadSerializer, "scenario factsheet", "scenario factsheets"
    )
)
class ScenarioCollectionAPIView(BundlePartCollectionAPIView):
    part = SCENARIO
    serializer_class = ScenarioSerializer


@extend_schema_view(
    **part_detail_operations(ScenarioReadSerializer, "scenario factsheet")
)
class ScenarioAPIView(BundlePartAPIView):
    part = SCENARIO
    serializer_class = ScenarioSerializer
