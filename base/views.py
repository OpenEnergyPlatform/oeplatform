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

import json
import os
import re
from functools import lru_cache

import markdown2
from django.core.mail import send_mail
from django.shortcuts import render
from django.views.generic import View

import oeplatform.securitysettings as sec
from base.forms import ContactForm

# Create your views here.

SITE_ROOT = os.path.dirname(os.path.realpath(__file__))


@lru_cache(maxsize=None)
def read_version_changes():
    """read version and changes from changelog markdown

    We use cache so it can stay in process memory and we dont have to read files
    in every request. this only changes on a new release anyway, in which case
    the process is restarted.

    Returns:
       dict: {"version": (major, minor, patch), "changes": changes}
    """
    os.path.dirname(os.path.realpath(__file__))
    version_expr = r"^(?P<major>\d+)\.(?P<minor>\d+)+\.(?P<patch>\d+)$"
    markdowner = markdown2.Markdown()
    import logging

    logging.info("READING VERSION file.")
    try:
        with open(
            os.path.join(SITE_ROOT, "..", "VERSION"), encoding="utf-8"
        ) as version_file:
            match = re.match(version_expr, version_file.read())
            major, minor, patch = match.groups()
        with open(
            os.path.join(
                SITE_ROOT,
                "..",
                "versions/changelogs/%s_%s_%s.md" % (major, minor, patch),
            ),
            encoding="utf-8",
        ) as change_file:
            changes = markdowner.convert(
                "\n".join(line for line in change_file.readlines())
            )
    except Exception:
        logging.error("READING VERSION file.")
        # probably because change_file is missing
        major, minor, patch, changes = "", "", "", ""
    return {"version": (major, minor, patch), "changes": changes}


class Welcome(View):
    def get(self, request):
        context = read_version_changes()
        return render(request, "base/index.html", context)


def get_logs(request):
    version_expr = r"^(?P<major>\d+)_(?P<major>\d+)+_(?P<major>\d+)\.md$"
    logs = {}
    for file in os.listdir("../versions/changelogs"):
        match = re.match(version_expr, file)
        markdowner = markdown2.Markdown()
        if match:
            major, minor, patch = match.groups()
            with open("versions/changelogs" + file, encoding="utf-8") as f:
                logs[(major, minor, patch)] = markdowner.convert(
                    "\n".join(line for line in f.readlines())
                )
    return logs


def redir(request, target):
    return render(request, "base/{target}.html".format(target=target), {})


class ContactView(View):
    error_css_class = "error"
    required_css_class = "required"

    def post(self, request):
        form = ContactForm(data=request.POST)
        if form.is_valid():
            receps = sec.CONTACT_ADDRESSES.get(
                request.POST["contact_category"], "technical"
            )
            send_mail(
                request.POST.get("contact_topic"),
                f"{request.POST.get('contact_name')} "
                + f"({request.POST.get('contact_email')}) wrote: \n"
                + request.POST.get("content"),
                sec.DEFAULT_FROM_EMAIL,
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


def robot(request):
    return render(request, "base/robots.txt", {}, content_type="text/plain")


def handler500(request):
    response = render(request, "base/500.html", {})
    response.status_code = 500
    return response


def handler404(request, exception):
    response = render(request, "base/404.html", {})
    response.status_code = 404
    return response


def get_json_content(path, json_id=None):
    """Parse all jsons from given path and return as
        list or return a single parsed json by id ->
        The json must have a field called id.

    Args:
        path (string): path to directory like 'static/project_pages_content/'
        json_id (string, optional): ID value that must match the value of json[id].
            Defaults to None.

    Returns:
        list[object]: List of all deserialized json files in path
        or
        object: single json python object
    """

    if path is not None:
        all_jsons = []
        for _json in os.listdir(path=path):
            with open(os.path.join(path, _json), "r", encoding="utf-8") as json_content:
                content = json.load(json_content)
                all_jsons.append(content)

        if json_id is None:
            return all_jsons
        else:
            content_by_id = [
                i for i in all_jsons if json_id == i["id"] and "template" != i["id"]
            ]
            return content_by_id[0]
    # TODO: catch the exception if path is none
    else:
        return {
            "error": "Path cant be None. Please provide the path to '/static/project_detail_pages_content/' . You can create a new Project by adding an JSON file like the '/static/project_detail_pages_content/PROJECT_TEMPLATE.json'."  # noqa
        }


class AboutPage(View):
    # docstring
    projects_content_static = "project_detail_pages_content"
    projects_content_path = os.path.join(sec.STATIC_ROOT, projects_content_static)

    def get(self, request, projects_content_path=projects_content_path):
        projects = get_json_content(path=projects_content_path)

        return render(request, "base/about.html", {"projects": projects})


class AboutProjectDetail(AboutPage):
    # docstring

    def get(self, request, project_id):
        project = get_json_content(path=self.projects_content_path, json_id=project_id)

        return render(request, "base/project-detail.html", {"project": project})
