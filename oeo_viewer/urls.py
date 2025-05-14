# SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani>
# SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr>
#
# SPDX-License-Identifier: MIT

from django.urls import path

from .views import viewer_index

urlpatterns = [path(r"", viewer_index)]
