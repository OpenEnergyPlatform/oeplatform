import os
import re

import markdown2
from django.core.mail import send_mail
from django.shortcuts import render
from django.views.generic import View

import oeplatform.securitysettings as sec
from base.forms import ContactForm

# Create your views here.

SITE_ROOT = os.path.dirname(os.path.realpath(__file__))


class Welcome(View):
    def get(self, request):
        os.path.dirname(os.path.realpath(__file__))
        version_expr = r"^(?P<major>\d+)\.(?P<minor>\d+)+\.(?P<patch>\d+)$"
        markdowner = markdown2.Markdown()
        with open(os.path.join(SITE_ROOT, "..", "VERSION")) as version_file:
            match = re.match(version_expr, version_file.read())
            major, minor, patch = match.groups()
        with open(
            os.path.join(
                SITE_ROOT,
                "..",
                "versions/changelogs/%s_%s_%s.md" % (major, minor, patch),
            )
        ) as change_file:
            changes = markdowner.convert(
                "\n".join(line for line in change_file.readlines())
            )
        return render(
            request,
            "base/index.html",
            {"version": "%s.%s.%s" % (major, minor, patch), "changes": changes, "disableSidebar": True},
        )


def get_logs(request):
    version_expr = r"^(?P<major>\d+)_(?P<major>\d+)+_(?P<major>\d+)\.md$"
    for file in os.listdir("../versions/changelogs"):
        match = re.match(version_expr, file)
        markdowner = markdown2.Markdown()
        if match:
            major, minor, patch = match.groups()
            with open("versions/changelogs" + file) as f:
                logs[(major, minor, patch)] = markdowner.convert(
                    "\n".join(line for line in f.readlines())
                )


def redir(request, target):
    return render(request, "base/{target}.html".format(target=target), {})


class ContactView(View):
    def post(self, request):
        form = ContactForm(data=request.POST)
        if form.is_valid():
            receps = sec.CONTACT_ADDRESSES[request.POST["contact"]]
            send_mail(
                request.POST.get("contact_topic"),
                request.POST.get("contact_name")
                + " wrote: \n"
                + request.POST.get("content"),
                request.POST.get("contact_email"),
                receps,
                fail_silently=False,
            )
            return render(
                request, "base/contact.html", {"form": ContactForm(), "success": True}
            )
        else:
            return render(
                request, "base/contact.html", {"form": form, "success": False}
            )

    def get(self, request):
        return render(
            request, "base/contact.html", {"form": ContactForm(), "success": False}
        )


def robot(request):
    return render(request, "base/robots.txt", {}, content_type="text/plain")


def handler500(request):
    response = render(request, "base/500.html", {})
    response.status_code = 500
    return response


def handler404(request):
    response = render(request, "base/404.html", {})
    response.status_code = 404
    return response
