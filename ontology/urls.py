# SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
# SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
# SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from django.urls import path, re_path
from django.views.generic import TemplateView

from ontology import views

urlpatterns = [
    # oeo-extended
    re_path(r"^$", views.OntologyAbout.as_view()),
    path("oeox/", views.OeoExtendedFileServe.as_view()),
    path("releases/oeox/", views.OeoExtendedFileServe.as_view()),
    path(
        "partial/page-content/",
        views.PartialOntologyAboutContent.as_view(),
        name="partial-page-content",
    ),
    path(
        "partial/page-sidebar-content/",
        views.PartialOntologyAboutSidebarContent.as_view(),
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
    ),
    re_path(
        r"^(?P<ontology>[\w_-]+)\/releases/latest$",
        views.OntologyStatics.as_view(),
        {"full": True},
        name="oeo-latest-full-zip",
    ),
    re_path(
        r"^(?P<ontology>[\w_-]+)\/releases/latest/glossary$",
        views.OntologyStatics.as_view(),
        {"glossary": True},
        name="oeo-latest-glossary",
    ),
    re_path(
        r"^(?P<ontology>[\w_-]+)\/releases(\/v?(?P<version>[\d\.]+))?\/imports\/(?P<file>[\w_-]+)(.(?P<extension>[\w_-]+))?$",  # noqa
        views.OntologyStatics.as_view(),
        {"imports": True},
    ),
    re_path(
        r"^(?P<ontology>[\w_-]+)\/releases(\/v?(?P<version>[\d\.]+))?\/(?P<file>[\w_-]+)(.(?P<extension>[\w_-]+))?$",  # noqa
        views.OntologyStatics.as_view(),
    ),
    re_path(
        r"^(?P<ontology>[\w_-]+)\/dev\/(?P<file>[\w_-]+)(.(?P<extension>[\w_-]+))?$",
        views.OntologyStatics.as_view(),
    ),
    re_path(
        r"^(?P<ontology>[\w_-]+)?/$",
        views.OntologyStatics.as_view(),
        name="oeo-initializer",
    ),
    # re_path(
    #     r"^(?P<ontology>[\w_-]+)\/imports\/(?P<module_or_id>[\w\d_-]+)",
    #     views.OntologyOverview.as_view(),
    #     {"imports": True},
    # ),
    re_path(
        r"^(?P<ontology>[\w_-]+)?/(?P<module_or_id>[\w\d_-]+)?/$",
        views.OntologyViewClasses.as_view(),
        name="oeo-classes",
    ),
]
