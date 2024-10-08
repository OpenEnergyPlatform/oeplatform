from django.shortcuts import get_object_or_404, render

from dataedit.models import Table
from login.utils import get_badge_icon_path, get_review_badge_from_table_metadata


def metadata_review_badge_indicator_icon_file(request, user_id, table_name):
    # is_badge : bool , msg : string -> either error msg or badge name
    schema = "model_draft"  # set fixed for now
    table = get_object_or_404(Table, schema__name=schema, name=table_name)
    is_badge, msg = get_review_badge_from_table_metadata(table)

    icon_path = None
    err_msg = None
    if is_badge:
        icon_path = get_badge_icon_path(msg)
        badge_name = msg
    else:
        badge_name = None
        err_msg = msg

    context = {
        "is_badge": is_badge,
        "err_msg": err_msg,
        "badge_name": badge_name,
        "icon_path": icon_path,
    }

    return render(request, "login/partials/badge_icon.html", context)
