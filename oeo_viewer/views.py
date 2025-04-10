# SPDX-FileCopyrightText: 2025 Adel Memariani <memarian@haskell2go.iks.cs.ovgu.de>
# SPDX-FileCopyrightText: 2025 Adel Memariani <memarian@winadms-MacBook-Pro.local>
# SPDX-FileCopyrightText: 2025 Christian Winger <c@wingechr.de>
# SPDX-FileCopyrightText: 2025 Jonas Huber <jonas.huber@rl-institut.de>
#
# SPDX-License-Identifier: MIT

from django.shortcuts import render

from oeplatform.settings import EXTERNAL_URLS


def viewer_index(request, *args, **kwargs):
    return render(
        request, "index.html", context={"tib_ts_oeo_link": EXTERNAL_URLS["tib_ts_oeo"]}
    )
