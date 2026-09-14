"""Scenario factsheets, as endpoints.

Everything these do is in `oekg.part_views`: a scenario is one of the two
things the shape gives its own has-uuid, and being addressable works the same
way for both. What is left here is what is particular to a scenario -- its
`BundlePart` and its serializer -- and two named classes, so a route and a
traceback say *scenario* rather than *part*.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from oekg.bundles import SCENARIO
from oekg.part_views import BundlePartAPIView, BundlePartCollectionAPIView
from oekg.serializers import ScenarioSerializer


class ScenarioCollectionAPIView(BundlePartCollectionAPIView):
    part = SCENARIO
    serializer_class = ScenarioSerializer


class ScenarioAPIView(BundlePartAPIView):
    part = SCENARIO
    serializer_class = ScenarioSerializer
