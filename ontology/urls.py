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
    OntologyViewClassesView,
    PartialOntologyAboutContentView,
    PartialOntologyAboutSidebarContentView,
)

app_name = "ontology"
urlpatterns = [
    # oeo-extended
    re_path(r"^$", OntologyAboutView.as_view()),
    path("oeox/", OeoExtendedFileServeView.as_view()),
    path("releases/oeox/", OeoExtendedFileServeView.as_view()),
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
    re_path(
        r"^(?P<ontology>[\w_-]+)?/(?P<module_or_id>[\w\d_-]+)?/$",
        OntologyViewClassesView.as_view(),
        name="oeo-classes",
    ),
]
