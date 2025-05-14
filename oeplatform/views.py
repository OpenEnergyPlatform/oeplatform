# SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr>
# SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer>
#
# SPDX-License-Identifier: MIT

from django.shortcuts import redirect
from django.views import View

from oeplatform import settings


class ImagesView(View):
    def get(self, request, f):
        return redirect("/static/" + f)


def redirect_tutorial(request):
    """all old links totutorials: redirect to new (external) page"""
    return redirect(settings.EXTERNAL_URLS["tutorials_index"])
