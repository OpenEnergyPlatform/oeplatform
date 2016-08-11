from django.conf.urls import url

from literature import views

pgsql_qualifier = r"[\w\d_]+"

urlpatterns = [
    url(r'^$', views.list_references,),
    url(r'^entry/(?P<entries_id>\d+)/$', views.show_entry,),
    url(r'^entry/add$', views.LiteratureView.as_view(),),
    url(r'^entry/(?P<entries_id>\d+)/edit/$', views.LiteratureView.as_view(),),
]
