from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render  # noqa:F401
from django.views.generic import View


# Suggested views maybe you will use other ones @adel
class OeoExtPluginView(View, LoginRequiredMixin):
    def get(self, request):
        return render(request, "oeo_ext/partials/oeo-ext-plugin-ui.html")

    def post(self, request):
        return render(request, "oeo_ext/partials/oeo-ext-plugin-ui.html")
