from allauth.socialaccount.signals import pre_social_login
from django.dispatch import receiver
from django.shortcuts import redirect
from django.views import View

from oeplatform import settings


class ImagesView(View):
    def get(self, request, f):
        return redirect("/static/" + f)


def redirect_tutorial(request):
    """all old links totutorials: redirect to new (external) page"""
    return redirect(settings.EXTERNAL_URLS["tutorials_index"])


@receiver(pre_social_login)
def populate_profile(request, sociallogin, **kwargs):
    social_account = sociallogin.account
    user = request.user
    user.name = social_account.name
    user.save()
