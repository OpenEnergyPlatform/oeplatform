from django.conf.urls import include, url

from tutorials import views

urlpatterns = [
    url(r"^$", views.ListTutorials.as_view(), name="list_tutorials"),
    url(r"add/", views.CreateNewTutorial.as_view(), name="add_tutorial"),
    url(
        r"(?P<tutorial_id>[\w\-]+)/edit/",
        views.EditTutorials.as_view(),
        name="edit_tutorial",
    ),
    url(
        r"(?P<tutorial_id>[\w\-]+)/delete/",
        views.DeleteTutorial.as_view(),
        name="delete_tutorial",
    ),
    # This must be last, otherwise it will match anything
    url(
        r"jupyter/(?P<tutorial_id>[\w\-]+)/$",
        views.TutorialDetail.as_view(),
        name="detail_tutorial",
    ),
    url(
        r"^(?P<tutorial_id>[\w\-]+)/$",
        views.TutorialDetail.as_view(),
        name="detail_tutorial",
    ),
]
