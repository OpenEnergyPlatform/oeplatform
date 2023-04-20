from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth.views import (
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.urls import path

from login import views

# from login.views import AccountDeleteView

urlpatterns = [
    path("admin/", admin.site.urls, name="admin"),
    path(
        "password_reset/",
        PasswordResetView.as_view(
            html_email_template_name="registration/password_reset_email.html",
            email_template_name="registration/password_reset_email.txt",
            template_name="registration/custom_password_reset_form.html",
        ),
        name="password_reset",
    ),
    path(
        "password_reset/done/",
        PasswordResetDoneView.as_view(
            template_name="registration/custom_password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        PasswordResetConfirmView.as_view(
            template_name="registration/custom_password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        PasswordResetCompleteView.as_view(
            template_name="registration/custom_password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    url("^", include("django.contrib.auth.urls")),
    url(
        r"^profile/(?P<user_id>[\d]+)$",
        views.TablesView.as_view(),
        name="profile",
    ),
    url(
        r"^profile/(?P<user_id>[\d]+)/tables$",
        views.TablesView.as_view(),
        name="tables",
    ),
    url(
        r"^profile/(?P<user_id>[\d]+)/review$",
        views.ReviewsView.as_view(),
        name="reviews",
    ),
    url(
        r"^profile/(?P<user_id>[\d]+)/settings$",
        views.SettingsView.as_view(),
        name="settings",
    ),
    url(
        r"^profile/(?P<user_id>[\d]+)/password_change$",
        views.OEPPasswordChangeView.as_view(),
        name="input",
    ),
    # TODO: implement tests before we allow user deletion
    # url(
    #    r"^profile/(?P<user_id>[\d]+)/delete_acc$",
    #    AccountDeleteView.as_view(),
    #    name="account-delete",
    # ),
    url(r"^groups/$", views.GroupManagement.as_view(), name="input"),
    url(
        r"^groups/new/$",
        views.GroupCreate.as_view(),
        name="input",
    ),
    url(
        r"^profile/(?P<user_id>[\d]+)/edit$", views.EditUserView.as_view(), name="edit"
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
