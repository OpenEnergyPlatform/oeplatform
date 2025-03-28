from django.conf.urls import include
from django.urls import path, re_path

from base import views

urlpatterns = [
    re_path(r"^robots.txt$", views.robot),
    path("", views.Welcome.as_view(), name="home"),
    re_path(r"^about/$", views.AboutPage.as_view(), name="index"),
    re_path(
        r"^about/project-detail/(?P<project_id>[\w\-]+)/$",
        views.AboutProjectDetail.as_view(),
        name="project_detail",
    ),
    re_path(r"^faq/$", views.redir, {"target": "faq"}, name="index"),
    re_path(r"^discussion/$", views.redir, {"target": "discussion"}, name="index"),
    re_path(r"^contact/$", views.ContactView.as_view(), name="index"),
    re_path(
        r"^legal/privacy_policy/$",
        views.redir,
        {"target": "privacy_policy"},
        name="index",
    ),
    re_path(r"^legal/tou/$", views.redir, {"target": "terms_of_use"}, name="index"),
] + [path("captcha/", include("captcha.urls"))]
