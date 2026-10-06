"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

Where the term search of the metadata editor and the oeo_ext unit picker goes
(#2292). Read by settings.py, so it imports nothing from the project.
"""  # noqa: 501

from typing import Mapping

PUBLIC_OEO_SEARCH = "https://openenergyplatform.org/api/oeo-search"
OWN_OEO_SEARCH = "/api/oeo-search"


def oeo_search_url(use_loep: bool, environ: Mapping[str, str]) -> str:
    """The search endpoint for this instance.

    `OEO_SEARCH_URL` in the environment wins. Otherwise an instance with its own
    lookup service (`use_loep`) searches itself, so a third-party instance needs
    no change, and one without it (a local dev setup) uses the public endpoint,
    whose index is seeded.
    """
    return environ.get("OEO_SEARCH_URL") or (
        OWN_OEO_SEARCH if use_loep else PUBLIC_OEO_SEARCH
    )
