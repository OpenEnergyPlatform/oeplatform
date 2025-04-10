# SPDX-FileCopyrightText: 2025 Adel Memariani <memarian@winadms-MacBook-Pro.local>
# SPDX-FileCopyrightText: 2025 Christian Winger <c@wingechr.de>
#
# SPDX-License-Identifier: MIT

from django.urls import path

from .views import viewer_index

urlpatterns = [path(r"", viewer_index)]
