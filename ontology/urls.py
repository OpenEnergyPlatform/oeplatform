"""
SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.urls import path, re_path
from django.views.generic import TemplateView

from ontology.views import (
    OeoExtendedFileServeView,
    OntologyAboutView,
    OntologyStaticsView,
    PartialOntologyAboutContentView,
    PartialOntologyAboutSidebarContentView,
    ontology_react_view,
)

app_name = "ontology"
urlpatterns = [
    # oeo-extended
    re_path(r"^$", OntologyAboutView.as_view(), name="index"),
    path("oeox/", OeoExtendedFileServeView.as_view(), name="oeox"),
    path("releases/oeox/", OeoExtendedFileServeView.as_view(), name="releases"),
    path(
        "partial/page-content/",
        PartialOntologyAboutContentView.as_view(),
        name="partial-page-content",
    ),
    path(
        "partial/page-sidebar-content/",
        PartialOntologyAboutSidebarContentView.as_view(),
        name="partial-page-sidebar-content",
    ),
    re_path(
        r"^oeo-steering-committee/$",
        TemplateView.as_view(template_name="ontology/oeo-steering-committee.html"),
        name="oeo-s-c",
    ),
    re_path(
        r"^ontology/oeo-steering-committee/$",
        TemplateView.as_view(template_name="ontology/oeo-steering-committee.html"),
        name="oeo-steering-committee",
    ),
    re_path(
        r"^(?P<ontology>[\w_-]+)\/releases/latest$",
        OntologyStaticsView.as_view(),
        {"full": True},
        name="oeo-latest-full-zip",
    ),
    re_path(
        r"^(?P<ontology>[\w_-]+)\/releases/latest/glossary$",
        OntologyStaticsView.as_view(),
        {"glossary": True},
        name="oeo-latest-glossary",
    ),
    re_path(
        r"^(?P<ontology>[\w_-]+)\/releases(\/v?(?P<version>[\d\.]+))?\/imports\/(?P<file>[\w_-]+)(.(?P<extension>[\w_-]+))?$",  # noqa
        OntologyStaticsView.as_view(),
        {"imports": True},
        name="oeo-static",
    ),
    re_path(
        r"^(?P<ontology>[\w_-]+)\/releases(\/v?(?P<version>[\d\.]+))?\/(?P<file>[\w_-]+)(.(?P<extension>[\w_-]+))?$",  # noqa
        OntologyStaticsView.as_view(),
        name="oeo-static",
    ),
    re_path(
        r"^(?P<ontology>[\w_-]+)\/dev\/(?P<file>[\w_-]+)(.(?P<extension>[\w_-]+))?$",
        OntologyStaticsView.as_view(),
        name="oeo-static",
    ),
    re_path(
        r"^(?P<ontology>[\w_-]+)?/$",
        OntologyStaticsView.as_view(),
        name="oeo-initializer",
    ),
    # ------------------------------------------------------------------
    # 1. Search Page Listing
    # Pattern: /ontology/<ontology_name>/entities/
    # Matches: /ontology/oeo/entities/ OR /ontology/xyz/entities/
    # ------------------------------------------------------------------
    re_path(
        r"^(?P<ontology>[\w-]+)/entities/$",
        ontology_react_view,
        name="ontology-entity-search",
    ),
    # ------------------------------------------------------------------
    # 2. Specific Entity Page (The Catch-All)
    # Pattern: /ontology/<ontology_name>/<short_form>/
    # Matches: /ontology/oeo/OEO_00000040/
    # NOTE: This must come AFTER 'entities' so 'entities' isn't mistaken for an ID.
    # ------------------------------------------------------------------
    re_path(
        r"^(?P<ontology>[\w-]+)/(?P<term_id>[\w\d:_-]+)/$",
        ontology_react_view,
        name="oeo-class-detail",
    ),
]
