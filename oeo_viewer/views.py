from django.shortcuts import render

from oeplatform.settings import EXTERNAL_URLS


def viewer_index(request, *args, **kwargs):
    return render(
        request, "index.html", context={"tib_ts_oeo_link": EXTERNAL_URLS["tib_ts_oeo"]}
    )
