from django.shortcuts import redirect
from django.views import View

from oeplatform import settings


class ImagesView(View):
    def get(self, request, f):
        return redirect("/static/" + f)


def redirect_tutorial(request):
    """all old links totutorials: redirect to new (external) page"""
    return redirect(settings.EXTERNAL_URLS["tutorials_index"])
