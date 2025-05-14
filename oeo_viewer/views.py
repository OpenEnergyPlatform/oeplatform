# SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani>
# SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani>
# SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr>
# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI>
#
# SPDX-License-Identifier: MIT

from django.shortcuts import render

from oeplatform.settings import EXTERNAL_URLS


def viewer_index(request, *args, **kwargs):
    return render(
        request, "index.html", context={"tib_ts_oeo_link": EXTERNAL_URLS["tib_ts_oeo"]}
    )
