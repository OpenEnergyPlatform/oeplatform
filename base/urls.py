"""
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Christian Hofmann <https://github.com/christian-rli> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.urls import path, re_path

from base.views import (
    AboutPageView,
    AboutProjectDetailView,
    ContactView,
    WelcomeView,
    redir_view,
    redirect_tutorial_view,
    reverse_url_view,
    robot_view,
)

app_name = "base"
urlpatterns = [
    path("", WelcomeView.as_view(), name="home"),
    re_path(r"^robots.txt$", robot_view, name="robots"),
    re_path(r"^about/$", AboutPageView.as_view(), name="about"),
    re_path(
        r"^about/project-detail/(?P<project_id>[\w\-]+)/$",
        AboutProjectDetailView.as_view(),
        name="project_detail",
    ),
    re_path(r"^contact/$", ContactView.as_view(), name="contact"),
    re_path(r"^faq/$", redir_view, {"target": "faq"}, name="faq"),
    re_path(r"^discussion/$", redir_view, {"target": "discussion"}, name="discussion"),
    re_path(
        r"^legal/privacy_policy/$",
        redir_view,
        {"target": "privacy_policy"},
        name="legal-privacy-policy",
    ),
    re_path(r"^legal/tou/$", redir_view, {"target": "terms_of_use"}, name="legal-tou"),
    re_path(r"^reverse-url/(?P<name>.*)", reverse_url_view, name="reverse-url"),
    re_path(r"^tutorials/.*", redirect_tutorial_view, name="tutorials"),
]
