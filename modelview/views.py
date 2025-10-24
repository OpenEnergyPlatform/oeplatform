"""
SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Johann Wagner <https://github.com/johannwagner>  © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Tom Heimbrodt <https://github.com/tom-heimbrodt>
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 quentinpeyras <https://github.com/quentinpeyras>
SPDX-FileCopyrightText: 2025 Lara Christmann <https://github.com/solar-c> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import csv
import re

import urllib3
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from django.views.generic import View

from dataedit.models import Tag
from modelview.helper import (
    FRAMEWORK_DEFAULT_COLUMNS,
    FRAMEWORK_VIEW_PROPS,
    MODEL_DEFAULT_COLUMNS,
    MODEL_VIEW_PROPS,
    getClasses,
    printable,
    processPost,
)

__all__ = [
    "FSAddView",
    "edit_model_view",
    "fs_delete_view",
    "list_sheets_view",
    "model_to_csv_view",
    "show_view",
]


def list_sheets_view(request, sheettype):
    """
    Lists all available model, framework factsheet objects.
    """
    c, _ = getClasses(sheettype)
    if c is None:
        # Handle the case where getClasses returned None
        # You can return an error message or take appropriate action here.
        # For example, you can return an HttpResponse indicating that the
        # requested sheettype is not supported.
        sheettype_error_message = "Invalid sheettype"
        return render(
            request,
            "modelview/error_template.html",
            {"sheettype_error_message": sheettype_error_message},
        )

    fields = {}
    defaults = set()

    fields = (
        FRAMEWORK_VIEW_PROPS if sheettype == "framework" else MODEL_VIEW_PROPS
    )  # noqa
    defaults = (
        FRAMEWORK_DEFAULT_COLUMNS if sheettype == "framework" else MODEL_DEFAULT_COLUMNS
    )

    if sheettype == "framework":
        label = "Framework"
    else:
        label = "Model"

    models = c.objects.all()

    tags = Tag.objects.none()
    for model in models:
        tags |= model.tags.all()

    return render(
        request,
        "modelview/modellist.html",
        {
            "models": models,
            "label": label,
            "tags": tags,
            "fields": fields,
            "default": defaults,
        },
    )


@never_cache
def show_view(request, sheettype, model_name):
    """
    Loads the requested factsheet
    """
    c, _ = getClasses(sheettype)

    if not c:
        raise Http404(
            "We dropped the scenario factsheets in favor of scenario bundles."
        )

    model = get_object_or_404(c, pk=model_name)

    user_agent = {"user-agent": "oeplatform"}
    urllib3.PoolManager(headers=user_agent)
    org = None
    repo = None

    if model.gitHub and model.link_to_source_code:
        try:
            match = re.match(
                r".*github\.com\/(?P<org>[^\/]+)\/(?P<repo>[^\/]+)(\/.)*",
                model.link_to_source_code,
            )
            org = match.group("org")
            repo = match.group("repo")
            # _handle_github_contributions(org, repo)
        except Exception:
            org = None
            repo = None

    return render(
        request,
        ("modelview/{0}.html".format(sheettype)),
        {
            "model": model,
            "gh_org": org,
            "gh_repo": repo,
            "displaySheetType": sheettype.capitalize(),
        },
    )


def model_to_csv_view(request, sheettype):
    c, f = getClasses(sheettype)
    if not c:
        raise Http404(
            "We dropped the scenario factsheets in favor of scenario bundles."
        )

    tag_ids = request.GET.get("tags")
    if tag_ids:
        tag_ids = tag_ids.split(",")

    header = list(
        field.attname
        for field in c._meta.get_fields()
        if hasattr(field, "attname")  # noqa
    )

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="{filename}s.csv"'.format(
        filename=c.__name__
    )  # noqa

    writer = csv.writer(response, quoting=csv.QUOTE_ALL)
    writer.writerow(header)

    models = c.objects.all()
    # if tags are specified: filter models for ALL of the tags

    if tag_ids:
        for tag_id in tag_ids:
            models = models.filter(tags__pk=tag_id)

    for model in models.order_by("pk"):
        writer.writerow([printable(model, col) for col in header])

    return response


@login_required
@never_cache
def edit_model_view(request, model_name, sheettype):
    """
    Constructs a form accoring to existing model
    """
    c, f = getClasses(sheettype)

    model = get_object_or_404(c, pk=model_name)

    form = f(instance=model)

    tags = Tag.objects.all()

    return render(
        request,
        "modelview/edit{}.html".format(sheettype),
        {
            "form": form,
            "name": model_name,
            "method": "update",
            "tags": tags,
        },
    )


class FSAddView(LoginRequiredMixin, View):
    def get(self, request, sheettype, method="add"):
        c, f = getClasses(sheettype)
        if method == "add":
            form = f()

            return render(
                request,
                "modelview/edit{}.html".format(sheettype),
                {"form": form, "method": method},
            )
        else:
            raise NotImplementedError()  # FIXME: model_name not defined

    def post(self, request, sheettype, method="add", pk=None):
        c, f = getClasses(sheettype)
        form = processPost(request.POST, c, f, files=request.FILES, pk=pk)

        if form.is_valid():
            model = form.save()
            if hasattr(model, "license") and model.license:
                if model.license != "Other":
                    model.license_other_text = None
            ids = {
                field[len("tag_") :]
                for field in request.POST
                if field.startswith("tag_")
            }

            model.tags = sorted(list(ids))
            model.save()

            return redirect(
                "/factsheets/{sheettype}s/{model}".format(
                    sheettype=sheettype, model=model.pk
                )
            )
        else:
            errors = []
            for field in form.errors:
                e = form.errors[field]
                error = e[0]
                field = form.fields[field].label
                errors.append((field, str(error)))

            return render(
                request,
                "modelview/edit{}.html".format(sheettype),
                {
                    "form": form,
                    "name": pk,
                    "method": method,
                    "errors": errors,
                },
            )


@require_http_methods(["DELETE"])
@login_required
def fs_delete_view(request, sheettype, pk):
    c, _ = getClasses(sheettype)
    model = get_object_or_404(c, pk=pk)
    model.delete()

    response_data = {"success": True, "message": "Entry deleted successfully."}

    response = HttpResponse(response_data)
    url = reverse("modelview:modellist", kwargs={"sheettype": sheettype})
    response["HX-Redirect"] = url
    return response
