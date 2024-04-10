from django.conf.urls import url
from django.views.generic import TemplateView

from ontology import views

urlpatterns = [
    url(r"^$", views.OntologyVersion.as_view()),
    url(
        "partial/page-content/",
        views.PartialOntologyOverviewContent.as_view(),
        name="partial-page-content",
    ),
    url(
        "partial/page-sidebar-content/",
        views.PartialOntologyOverviewSidebarContent.as_view(),
        name="partial-page-sidebar-content",
    ),
    url(r"^ontology/$", views.OntologyVersion.as_view()),
    url(
        r"^oeo-steering-committee/$",
        TemplateView.as_view(template_name="ontology/oeo-steering-committee.html"),
        name="oeo-s-c",
    ),
    url(
        r"^ontology/oeo-steering-committee/$",
        TemplateView.as_view(template_name="ontology/oeo-steering-committee.html"),
    ),
    url(
        r"^(?P<ontology>[\w_-]+)\/releases(\/v?(?P<version>[\d\.]+))?\/imports\/(?P<file>[\w_-]+)(.(?P<extension>[\w_-]+))?$",  # noqa
        views.OntologyStatics.as_view(),
        {"imports": True},
    ),
    url(
        r"^(?P<ontology>[\w_-]+)\/releases(\/v?(?P<version>[\d\.]+))?\/(?P<file>[\w_-]+)(.(?P<extension>[\w_-]+))?$",  # noqa
        views.OntologyStatics.as_view(),
    ),
    url(
        r"^(?P<ontology>[\w_-]+)\/dev\/(?P<file>[\w_-]+)(.(?P<extension>[\w_-]+))?$",
        views.OntologyStatics.as_view(),
    ),
    url(
        r"^(?P<ontology>[\w_-]+)\/imports\/(?P<module_or_id>[\w\d_-]+)",
        views.OntologyOverview.as_view(),
        {"imports": True},
    ),
    url(
        r"^(?P<ontology>[\w_-]+)?/(?P<module_or_id>[\w\d_-]+)?/$",
        views.OntologyViewClasses.as_view(),
        name="oeo-classes",
    ),
    url(
        r"^(?P<ontology>[\w_-]+)?/$",
        views.OntologyOverview.as_view(),
    ),
]
