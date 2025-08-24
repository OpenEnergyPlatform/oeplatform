from django.urls import path, re_path  # noqa:F401

from databus import views  # noqa:F401

app_name = "databus"

urlpatterns = [
    path(
        "distribution/table/<str:schema>/<str:table>/register/",
        views.DatabusRegister.as_view(),
        name="register",
    )
]
