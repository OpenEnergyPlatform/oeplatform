# SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani>
# SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani>
# SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani>
# SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr>
# SPDX-FileCopyrightText: 2025 Johann Wagner <https://github.com/johannwagner>
# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI>
# SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer>
# SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer>
# SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer>
# SPDX-FileCopyrightText: 2025 NB-KREDER\kreder <https://github.com/klarareder>
# SPDX-FileCopyrightText: 2025 Tu Phan Ngoc <RL-INSTITUT\tuphan.ngoc@rli-nb-65.rl-institut.local>
# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI>
#
# SPDX-License-Identifier: MIT

"""oeplatform URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns: re_path(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns: re_path(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns: re_path(r'^blog/', include(blog_urls))
"""

from django.conf.urls import include
from django.conf.urls.static import static
from django.urls import path, re_path

from oeplatform import settings

from .views import redirect_tutorial

handler500 = "base.views.handler500"
handler404 = "base.views.handler404"

urlpatterns = [
    re_path(r"^api/", include("api.urls")),
    path("", include("base.urls")),
    re_path(r"^user/", include("login.urls")),
    re_path(r"^oeo_ext/", include("oeo_ext.urls")),
    re_path(r"^factsheets/", include("modelview.urls")),
    re_path(r"^dataedit/", include("dataedit.urls")),
    re_path(r"^ontology/", include("ontology.urls")),
    re_path(r"^viewer/oeo/", include("oeo_viewer.urls")),
    re_path(r"^scenario-bundles/", include("factsheet.urls")),
    re_path(r"^tutorials/.*", redirect_tutorial),
    re_path(r"^oekg/", include("oekg.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
