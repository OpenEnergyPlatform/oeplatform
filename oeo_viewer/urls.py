from django.urls import path

from .views import viewer_index

urlpatterns = [path(r"", viewer_index)]
