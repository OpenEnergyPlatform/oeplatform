from django.conf.urls import include, url

from login import views

urlpatterns = [
    url("^", include("django.contrib.auth.urls")),
    url(r"^profile/(?P<user_id>[\d]+)$", views.ProfileView.as_view(), name="input"),
    url(
        r"^profile/password_change$",
        views.OEPPasswordChangeView.as_view(),
        name="input",
    ),
    url(
        r"^profile/(?P<user_id>[\d]+)/edit$", views.EditUserView.as_view(), name="input"
    ),
    url(r"^groups/$", views.GroupManagement.as_view(), name="input"),
    url(
        r"^groups/new/$",
        views.GroupCreate.as_view(),
        name="input",
    ),
    url(
        r"^groups/(?P<group_id>[\w\d_\s]+)/edit$",
        views.GroupCreate.as_view(),
        name="input",
    ),
    url(
        r"^groups/(?P<group_id>[\w\d_\s]+)/$",
        views.GroupView.as_view(),
    ),
    url(
        r"^groups/(?P<group_id>[\w\d_\s]+)/members$",
        views.GroupEdit.as_view(),
        name="input",
    ),
    url(r"^groups/new/$", views.GroupCreate.as_view(), name="input"),
    url(r"^register$", views.CreateUserView.as_view()),
    url(r"^detach$", views.DetachView.as_view()),
    url(r"^activate/(?P<token>[\w\d\-\s]+)$", views.activate),
    url(r"^activate/$", views.ActivationNoteView.as_view(), name="activate"),
]
