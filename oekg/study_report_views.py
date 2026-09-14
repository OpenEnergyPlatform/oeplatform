"""Study reports, as endpoints.

A study report is the publication a bundle is written up in. It is a
sub-resource for the same reason a scenario factsheet is -- the shape gives it
its own has-uuid -- so it gets the same endpoints from `oekg.part_views`, and
what is particular to it is a `BundlePart` and a serializer.

Two things about a study report are worth knowing before changing this:

- **Its authors are shared nodes.** Two bundles citing the same paper reference
  one author node, so a write may point at an existing one but may never rename
  it; `refuse_renames` in the shared write path is what enforces that.
- **Its reference is the URL itself.** The shape allows at most one, and the
  cited document's URL *is* the node's IRI, typed as a reference. There is no
  second node holding a label, because nothing asks a reference for one.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from oekg.bundles import STUDY_REPORT
from oekg.part_views import BundlePartAPIView, BundlePartCollectionAPIView
from oekg.serializers import StudyReportSerializer


class StudyReportCollectionAPIView(BundlePartCollectionAPIView):
    part = STUDY_REPORT
    serializer_class = StudyReportSerializer


class StudyReportAPIView(BundlePartAPIView):
    part = STUDY_REPORT
    serializer_class = StudyReportSerializer
