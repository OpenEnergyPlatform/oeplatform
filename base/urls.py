from django.conf.urls import url

from base import views

urlpatterns = [
    url(r"^robots.txt$", views.robot),
    url(r"^$", views.Welcome.as_view(), name="index"),
    url(r"^about/$", views.redir, {"target": "about"}, name="index"),
    url(r"^faq/$", views.redir, {"target": "faq"}, name="index"),
    url(r"^discussion/$", views.redir, {"target": "discussion"}, name="index"),
    url(r"^contact/$", views.ContactView.as_view(), name="index"),
    url(r"^legal/impressum/$", views.redir, {"target": "impressum"}, name="index"),
    url(r"^legal/datasec/$", views.redir, {"target": "datasecurity"}, name="index"),
    url(r"^legal/tou/$", views.redir, {"target": "terms_of_use"}, name="index"),
]
