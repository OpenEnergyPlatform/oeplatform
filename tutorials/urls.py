from django.conf.urls import include, url

from tutorials import views

urlpatterns = [
    url(r'^$', views.ListTutorials.as_view()),
    url(r'add/', views.NewTutorial.as_view(), name='add_tutorial'),

    # This must be last, otherwise it will match anything
    url(r'^(?P<tutorial_id>[\w\-]+)/$', views.TutorialDetail.as_view(), name='detail_tutorial'),
]