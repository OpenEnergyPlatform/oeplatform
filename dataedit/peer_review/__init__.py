"""
Open Peer Review (OPR) backend package.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

This package collects the OPR backend logic that previously lived inline in
``dataedit/views.py`` and ``dataedit/helper.py``. See the design notes
"08 / 09 / 10 - Phase ..." for the target architecture.

Phase 2, step S1 (this change): ``metadata_serializer`` — pure functions that
shape the oemetadata for the review templates, extracted verbatim out of
``TablePeerReviewView`` so they are unit-testable and the view shrinks.
"""  # noqa: E501
