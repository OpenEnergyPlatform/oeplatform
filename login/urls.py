from django.conf.urls import include, url
from django.urls import path
from login import views
from django.contrib.auth.views import PasswordResetCompleteView, PasswordResetConfirmView, PasswordResetDoneView

urlpatterns = [
    path('password_reset/', views.PasswordResetView.as_view(
        html_email_template_name="registration/password_reset_email.html",
        email_template_name="registration/password_reset_email.txt",
        template_name='registration/custom_password_reset_form.html'), name='password_reset'),
    path('password_reset/done/', PasswordResetDoneView.as_view(template_name = 'registration/custom_password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(template_name = 'registration/custom_password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', PasswordResetCompleteView.as_view(template_name='registration/custom_password_reset_complete.html'), name='password_reset_complete'),

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
