from django.shortcuts import render

from login.utilities import (
    get_review_badge_from_table_metadata,
    get_badge_icon_path,
)


def metadata_review_badge_indicator_icon_file(request):
    # Example usage in a Django view
    badge_name = "Gold"
    # is_badge : bool , msg : string -> either error msg or badge name
    is_badge, msg = get_review_badge_from_table_metadata(badge_name)

    icon_path = None
    err_msg = None
    if is_badge:
        icon_path = get_badge_icon_path(badge_name)
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

    return render(request, "my_template.html", context)
