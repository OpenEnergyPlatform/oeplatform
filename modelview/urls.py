from django.conf.urls import url

from . import views
from oeplatform import settings
from django.conf.urls.static import static

urlpatterns = [
    url(r'^(?P<model_name>.+)/$', views.ModelView.as_view(), name='index'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
