from django.conf.urls import include, url
from markdownx import urls as markdownx

from tutorials import views

urlpatterns = [
    url(r'^$', views.ListTutorials.as_view()),
    url(r'^(?P<tutorial_id>[\w\-]+)/$', views.TutorialDetail.as_view()),
    # this not working correctly - some error in gatherTutorials
    url(r'/add/', views.NewTutorial.as_view(), name='add_tutorial'),
    url(r'^markdownx/', include(markdownx)),
]