"""
SPDX-FileCopyrightText: 2025 Pierre Francois <https://github.com/Bachibouzouk> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Johann Wagner <https://github.com/johannwagner>  © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Johann Wagner <https://github.com/johannwagner>  © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 NB-KREDER\\kreder <https://github.com/klarareder> © Fraunhofer IEE
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import logging
import os

from django.core.mail import send_mail
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic import View

from base.forms import ContactForm
from base.helper import get_json_content, read_version_changes
from oeplatform.settings import (
    CONTACT_ADDRESSES,
    DEFAULT_FROM_EMAIL,
    EXTERNAL_URLS,
    STATIC_ROOT,
)

logger = logging.getLogger("oeplatform")


class WelcomeView(View):
    def get(self, request):
        context = read_version_changes()
        return render(request, "base/index.html", context)


def redir_view(request, target):
    return render(request, "base/{target}.html".format(target=target), {})


class ContactView(View):
    error_css_class = "error"
    required_css_class = "required"

    def post(self, request):
        form = ContactForm(data=request.POST)
        if form.is_valid():
            contact_category = request.POST.get("contact_category", "technical")
            receps = CONTACT_ADDRESSES[contact_category]
            send_mail(
                request.POST.get("contact_topic"),
                f"{request.POST.get('contact_name')} "
                + f"({request.POST.get('contact_email')}) wrote: \n"
                + request.POST.get("content"),
                DEFAULT_FROM_EMAIL,
                receps,
                fail_silently=False,
            )
            return render(
                request, "base/contact.html", {"form": ContactForm(), "success": True}
            )
        else:
            return render(
                request, "base/contact.html", {"form": form, "success": False}
            )

    def get(self, request):
        return render(
            request, "base/contact.html", {"form": ContactForm(), "success": False}
        )


def robot_view(request):
    return render(request, "base/robots.txt", {}, content_type="text/plain")


def handler500(request):
    response = render(request, "base/500.html", {})
    response.status_code = 500
    return response


def handler404(request, exception):
    response = render(request, "base/404.html", {})
    response.status_code = 404
    return response


class AboutPageView(View):

    projects_content_static = "project_detail_pages_content"
    projects_content_path = os.path.join(STATIC_ROOT, projects_content_static)

    def get(self, request, projects_content_path=projects_content_path):
        projects = get_json_content(path=projects_content_path)

        return render(request, "base/about.html", {"projects": projects})


class AboutProjectDetailView(AboutPageView):

    def get(self, request, project_id):
        project = get_json_content(path=self.projects_content_path, json_id=project_id)

        return render(request, "base/project-detail.html", {"project": project})


def redirect_tutorial_view(request: HttpRequest) -> HttpResponse:
    """all old links totutorials: redirect to new (external) page"""
    return redirect(EXTERNAL_URLS["tutorials_index"])


def reverse_url_view(request: HttpRequest, name: str) -> JsonResponse:
    """for pure javascript, we need to resolve urls dynamically"""

    def to_str(x: list | str) -> str:
        if isinstance(x, list):
            return x[0]
        return x

    try:
        # convert GET into dict[str,str]
        kwargs = {k: to_str(v) for k, v in request.GET.items()}
        url = reverse(name, kwargs=kwargs)
        return JsonResponse({"url": url})
    except Exception as exc:
        logger.error(f"reverse url failed for {name},{request.GET}: {exc}")
        return JsonResponse({"message": "invalid reverse request"}, status=400)
