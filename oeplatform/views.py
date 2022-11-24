from django.shortcuts import redirect
from django.views import View


class ImagesView(View):
    def get(self, request, f):
        return redirect("/static/" + f)
