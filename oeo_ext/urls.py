from django.conf.urls import url  # noqa:F401
from django.urls import path  # noqa:F401

from oeo_ext import views

app_name = "oeo_ext"

urlpatterns = [
    path(
        r"oeo-ext-plugin-ui/create",
        views.OeoExtPluginView.as_view(),
        name="oeo-ext-plugin-ui-create",
    )
]
