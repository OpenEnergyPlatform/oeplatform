from django.views import View
from django.shortcuts import redirect


class ImagesView(View):
    def get(self, request, f):
        return redirect("/static/"+f)
