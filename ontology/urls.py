from django.conf.urls import url
from django.views.generic import TemplateView

from ontology import views

urlpatterns = [
    url(r"^$", views.OntologyAbout.as_view()),
    url(
        "partial/page-content/",
        views.PartialOntologyAboutContent.as_view(),
        name="partial-page-content",
    ),
    url(
        "partial/page-sidebar-content/",
        views.PartialOntologyAboutSidebarContent.as_view(),
        name="partial-page-sidebar-content",
    ),
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
        r"^(?P<ontology>[\w_-]+)\/releases/latest?$",
        views.OntologyStatics.as_view(),
        {"full": True},
        name="oeo-latest-full-zip",
    ),
    url(
        r"^(?P<ontology>[\w_-]+)\/releases/latest/glossary?$",
        views.OntologyStatics.as_view(),
        {"glossary": True},
        name="oeo-latest-glossary",
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
        r"^(?P<ontology>[\w_-]+)?/$",
        views.OntologyStatics.as_view(),
        name="oeo-initializer",
    ),
    # url(
    #     r"^(?P<ontology>[\w_-]+)\/imports\/(?P<module_or_id>[\w\d_-]+)",
    #     views.OntologyOverview.as_view(),
    #     {"imports": True},
    # ),
    url(
        r"^(?P<ontology>[\w_-]+)?/(?P<module_or_id>[\w\d_-]+)?/$",
        views.OntologyViewClasses.as_view(),
        name="oeo-classes",
    ),
]
