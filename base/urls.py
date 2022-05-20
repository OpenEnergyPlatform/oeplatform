from django.conf.urls import url, include
from django.urls import path
from base import views

urlpatterns = [
    url(r"^robots.txt$", views.robot),
    url(r"^$", views.Welcome.as_view(), name="index"),
    url(r"^about/$", views.AboutPage.as_view(), name="index"),
    url(r"^about/project-detail/(?P<project_id>[\w\-]+)/$", views.AboutProjectDetail.as_view(), name="project_detail"),
    url(r"^faq/$", views.redir, {"target": "faq"}, name="index"),
    url(r"^discussion/$", views.redir, {"target": "discussion"}, name="index"),
    url(r"^contact/$", views.ContactView.as_view(), name="index"),
    url(r"^legal/privacy_policy/$", views.redir, {"target": "privacy_policy"}, name="index"),
    url(r"^legal/tou/$", views.redir, {"target": "terms_of_use"}, name="index"),
] + [path('captcha/', include('captcha.urls'))]
