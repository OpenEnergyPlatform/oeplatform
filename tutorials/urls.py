from django.conf.urls import include, url

from tutorials import views

urlpatterns = [
    url(r'^$', views.ListTutorials.as_view()),
    url(r'^(?P<tutorial_id>[\w\-]+)/$', views.TutorialDetail.as_view()),
]