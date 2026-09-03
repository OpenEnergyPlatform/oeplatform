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
import logging
import re

import urllib3
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseForbidden,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from django.views.generic import View

from dataedit.models import Tag
from modelview.helper import (
    getClasses,
    printable,
    processPost,
    view_props,
)
from modelview.list_payload import (
    build_list_payload,
    initial_fields,
    leaf_fields,
)
from modelview.models import BasicFactsheet

logger = logging.getLogger("oeplatform")


def log_factsheet_write(sheettype, pk, action, user, tags):
    """One logfmt line per factsheet write -- `add`, `update` or `delete`.

    This app keeps no history of any kind, so these lines are the only record
    that will ever exist of who changed what. They are deliberately one shape:
    a grep for `factsheet_write` has to find every write, not two thirds of
    them.

    What a log line cannot do is say what the write *replaced*, so there is
    still no undo -- and that is exactly the gap that made the tag corruption
    unrepairable, because the pre-corruption tag state was recorded nowhere.
    """
    logger.info(
        "factsheet_write sheettype=%s pk=%s action=%s user=%s tags=%s ok=1",
        sheettype,
        pk,
        action,
        user,
        tags,
    )


#: The prefix the old page put in front of every pk in its CSV link. It is a
#: DOM id and nothing else now, but links carrying it are in bookmarks and in
#: mails.
_LEGACY_TAG_PREFIX = "select_"


def tag_filter_pks(value):
    """The tag primary keys in a `?tags=<pk>,<pk>` value.

    One format, raw pks, shared by the list page's checkbox state and by the
    CSV download's filter. The two used to disagree: the page built its
    download link with `?tags=select_<pk>` where the CSV view filters on raw
    pks, so a filtered download matched nothing and returned a header row with
    no error -- which reads as "no matches" rather than as a bug (verified
    live: 0 rows where the correct value returns 59).
    """
    return [pk for pk in (part.strip() for part in (value or "").split(",")) if pk]


def resolve_legacy_tag_pks(pks):
    """Accept the prefixed values the old page's CSV link produced.

    Decided explicitly rather than by omission: refusing them would leave
    every link the old page emitted doing the very thing this fixes -- return
    an empty file with no error. It is applied *only* here, because only the
    CSV link ever carried the prefix; the list page had no `?tags=` at all
    before this.

    Not a bare prefix strip. A tag's primary key is its normalised name, so a
    real tag can legitimately begin with the prefix -- `Tag.get_name_normalized`
    maps "Select data" to `select_data` -- and blindly stripping would filter
    on `data` instead: a wrong answer, silently, which is the very class of
    failure this ticket exists to kill. The raw value therefore wins whenever
    it names a real tag, and only the leftovers are unprefixed. Costs one query,
    and only when a prefixed value actually arrives.
    """
    prefixed = [pk for pk in pks if pk.startswith(_LEGACY_TAG_PREFIX)]
    if not prefixed:
        return pks

    real = set(Tag.objects.filter(pk__in=prefixed).values_list("pk", flat=True))
    return [
        (
            pk
            if pk in real or not pk.startswith(_LEGACY_TAG_PREFIX)
            else pk[len(_LEGACY_TAG_PREFIX) :]
        )
        for pk in pks
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

    fields, defaults = view_props(sheettype)

    if sheettype == "framework":
        label = "Framework"
    else:
        label = "Model"

    # The prefetch is a precondition of the builder, not an optimisation:
    # without it the payload is one query per factsheet per view-property
    # group. Why the rows are built here rather than in the template is
    # `modelview/list_payload.py`'s docstring.
    #
    # `order_by` because the lazy payload replaces these rows wholesale, and
    # no factsheet model declares a `Meta.ordering` -- so today's agreement
    # between the two is a Postgres accident that an UPDATE can end.
    models = c.objects.all().order_by("pk").prefetch_related("tags")

    # Page-sized: the default columns for every row, and nothing else. The
    # other 165 come from `list_payload_view` on the first column toggle or
    # the first search keystroke. The page has to know which it already holds,
    # or every toggle would refetch.
    initial = initial_fields(fields, defaults)
    rows = build_list_payload(models, initial)

    # The tags actually in use by THIS sheet type, each once, by name.
    #
    # This replaces a loop that did `tags |= model.tags.all()` once per
    # factsheet. `QuerySet.__or__` OR-combines SQL rather than concatenating
    # results, so 305 iterations built one statement carrying ~305 joins and
    # returned a row per tag ATTACHMENT -- 12,156 checkboxes on production
    # where 825 distinct tags are in use, 6.04 MB and 30% of the page.
    #
    # Scoping matters most for frameworks: unscoped the page offered 290 tags
    # where 71 are in use, so 219 of its checkboxes returned nothing when
    # clicked.
    #
    # NOT ordered by `Tag.usage_count`: that field exists and looks apt, but
    # it is incremented only by table search in `dataedit` and never by
    # anything here, so it would rank an unrelated quantity.
    tags = Tag.objects.filter(factsheets__in=models).distinct().order_by("name")

    # A set of pks, not a queryset. The template tests each offered tag for
    # membership, and `in` against a QuerySet is what made this page
    # quadratic: Django defines no `QuerySet.__contains__`, so it falls back
    # to iterating the whole result cache once per checkbox.
    selected_tag_pks = set(tag_filter_pks(request.GET.get("tags")))

    return render(
        request,
        "modelview/modellist.html",
        {
            "rows": rows,
            "initial_columns": sorted(defaults),
            "label": label,
            "tags": tags,
            "selected_tag_pks": selected_tag_pks,
            "fields": fields,
            "default": defaults,
            "sheettype": sheettype,
        },
    )


@never_cache
def list_payload_view(request, sheettype):
    """Every column of every factsheet, for the list page's lazy fetch.

    The list ships the default columns only -- 1.32 MB at production's shape
    against 20.1 MB for the full record -- and DataTables searches hidden
    columns, so without this endpoint a search that used to find a model by
    its citation text would return nothing and say nothing. It is fetched
    once, on the first toggle or the first keystroke; a visitor who neither
    toggles nor searches never pays for it.

    Same builder, same queryset, same order as the list, because the table
    replaces its rows with these wholesale.

    A bare JSON array (`safe=False`), which is public data either way: these
    are the rows the CSV download already serves to anonymous callers.
    `never_cache` because a `fetch` GET is cacheable where the HTML page
    carrying the initial payload is not -- and a stale half of a row set is
    worse than either half being stale.
    """
    c, _ = getClasses(sheettype)
    if not c:
        raise Http404(
            "We dropped the scenario factsheets in favor of scenario bundles."
        )

    fields, _defaults = view_props(sheettype)
    models = c.objects.all().order_by("pk").prefetch_related("tags")

    return JsonResponse(build_list_payload(models, leaf_fields(fields)), safe=False)


@never_cache
def show_view(request, sheettype, pk):
    """
    Loads the requested factsheet
    """
    c, _ = getClasses(sheettype)

    if not c:
        raise Http404(
            "We dropped the scenario factsheets in favor of scenario bundles."
        )

    model: BasicFactsheet = get_object_or_404(c, pk=pk)

    user_agent = {"user-agent": "oeplatform"}
    urllib3.PoolManager(headers=user_agent)
    org = None
    repo = None

    if model.gitHub and model.link_to_source_code:
        match = re.match(
            r".*github\.com\/(?P<org>[^\/]+)\/(?P<repo>[^\/]+)(\/.)*",
            model.link_to_source_code,
        )
        if match:
            org = match.group("org")
            repo = match.group("repo")
        else:
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

    tag_ids = resolve_legacy_tag_pks(tag_filter_pks(request.GET.get("tags")))

    header = list(
        field.attname  # type: ignore because hasattr(field, "attname")
        for field in c._meta.get_fields()
        if hasattr(field, "attname")
    )

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="{filename}s.csv"'.format(
        filename=c.__name__
    )

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
def edit_model_view(request, pk, sheettype):
    """
    Constructs a form accoring to existing model
    """
    c, f = getClasses(sheettype)
    if not c or not f:
        raise Http404(
            "We dropped the scenario factsheets in favor of scenario bundles."
        )

    model: BasicFactsheet = get_object_or_404(c, pk=pk)

    form = f(instance=model)

    # No `tags` context variable: this view used to pass `Tag.objects.all()`
    # under that name, and `tag_selector.html` rendered every one of those
    # checkboxes `checked` -- so opening any factsheet for editing offered the
    # platform's whole vocabulary as already attached, and saving attached it
    # (#2385, #2381). The widget now reads its state off the bound form, which
    # can only ever carry this factsheet's own tags.
    return render(
        request,
        "modelview/edit{}.html".format(sheettype),
        {
            "form": form,
            "name": pk,
            "method": "update",
        },
    )


class FSAddView(LoginRequiredMixin, View):
    def get(self, request, sheettype, method="add"):
        # TODO: pk not used, but defined in urls.py
        # this should be POST,not GET?
        c, f = getClasses(sheettype)

        if method == "add" and f:
            form = f()

            return render(
                request,
                "modelview/edit{}.html".format(sheettype),
                {"form": form, "method": method},
            )
        else:
            raise NotImplementedError(method)  # FIXME: model_name not defined

    def post(self, request, sheettype, method="add", pk=None):
        c, f = getClasses(sheettype)
        form = processPost(request.POST, c, f, files=request.FILES, pk=pk)

        if form.is_valid():
            # `form.save()` writes the tags too, via `save_m2m()`. What stood
            # here instead was a `model.tags.clear()` followed by one
            # `Tag.objects.get()` per `tag_<pk>` field name in the POST: ~1,600
            # queries for a submit carrying the whole vocabulary (the "veeery
            # long on submit all" of #2385), and an unconditional wipe for any
            # submit that did not carry the widget at all.
            model = form.save()
            if hasattr(model, "license") and model.license:
                if model.license != "Other":
                    model.license_other_text = None

            model.save()

            log_factsheet_write(
                sheettype,
                model.pk,
                "update" if pk else "add",
                request.user.name,
                model.tags.count(),
            )

            return redirect(
                "modelview:show-factsheet",
                sheettype,
                model.pk,
                # "/factsheets/{sheettype}s/{model}".format(
                #    sheettype=sheettype, model=model.pk
                # )
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
    if not c:
        raise Http404(
            "We dropped the scenario factsheets in favor of scenario bundles."
        )

    # Checked here and not only in the template: `hx-delete` sends a real
    # DELETE request, and so does `curl -X DELETE`, so a hidden button is no
    # protection at all. Deleting is the one irreversible operation in this
    # app and it leaves no history, hence admins only -- editing stays open to
    # any account by policy.
    if not request.user.is_admin:
        return HttpResponseForbidden("Only administrators may delete a factsheet.")

    model = get_object_or_404(c, pk=pk)
    # Read before the delete: with no audit model, this line is the only
    # record that will ever exist of what went with it.
    tag_count = model.tags.count()
    model.delete()

    log_factsheet_write(sheettype, pk, "delete", request.user.name, tag_count)

    response_data = {"success": True, "message": "Entry deleted successfully."}

    response = HttpResponse(response_data)
    url = reverse("modelview:modellist", kwargs={"sheettype": sheettype})
    response["HX-Redirect"] = url
    return response
