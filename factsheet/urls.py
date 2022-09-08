from django.urls import path
from .views import factsheets_index

urlpatterns = [
    path(r"", factsheets_index)
]
