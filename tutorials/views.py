import json
import os
import re
from pathlib import Path

#import nbconvert
import nbformat
from bs4 import BeautifulSoup
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import Http404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from jinja2 import DictLoader
from markdown2 import Markdown

from .forms import TutorialForm
from .models import CATEGORY_OPTIONS, LEVEL_OPTIONS, Tutorial

youtubeUrlRegex = re.compile(r"^.*youtube\.com\/watch\?v=(?P<id>[A-z0-9]+)$")

template_cache = {}


def cache_templates(name):
    """read teamplates only once andcache in dict.

    Args:
        name: template file basename
              e.g. openenergyplatform for openenergyplatform.tpl

    Returns:
        str: template file content
    """
    if name not in template_cache:
        filepath = os.path.join(
            settings.BASE_DIR, "examples", "template", name + ".tpl"
        )
        with open(filepath) as file:
            template_cache[name] = file.read()
    return template_cache[name]


def _resolveStaticTutorial(path):
    try:
        with open(path, "r") as buildFile:
            build_file_content = buildFile.read()

            dl = DictLoader(
                {
                    "openenergyplatform": cache_templates("openenergyplatform"),
                }
            )

            jake_notebook = nbformat.reads(build_file_content, as_version=4)

            html_exporter = nbconvert.HTMLExporter(
                extra_loaders=[dl],
                template_file="openenergyplatform",
                anchor_link_text="Permalink",
            )
            (body, _resources) = html_exporter.from_notebook_node(jake_notebook)

            # Adding needed bootstrap styling to table.
            body = body.replace("<table", '<table class="table" ')

            return {"html": body}

    except Exception:
        return {"html": "Tutorial is missing"}


def _resolveStaticTutorials():
    resolvedTutorials = []

    # Load list of static tutorials

    jsonPaths = Path().rglob("*.json")

    def handleKeyNotInJson(json_dict, key_val, sub_key_val=None, merge_readable=False):
        if key_val in json_dict:

            if sub_key_val and sub_key_val in json_dict[key_val]:
                sub_val = json_dict[key_val][sub_key_val]

                if isinstance(sub_val, list) and merge_readable:
                    return ", ".join(sub_val)

                return sub_val

            return json_dict[key_val]
        else:
            return ""

    try:
        for jsonPath in jsonPaths:
            neededNotebookPath = os.path.splitext(jsonPath)[0] + ".ipynb"
            notebookPathExists = os.path.exists(neededNotebookPath)

            if not notebookPathExists:
                continue

            with open(jsonPath, "r") as jsonFile:
                jsonContent = json.load(jsonFile)

            rTut = _resolveStaticTutorial(neededNotebookPath)

            resolvedTutorials.append(
                {
                    "id": handleKeyNotInJson(jsonContent, "name"),
                    "title": handleKeyNotInJson(jsonContent, "displayName"),
                    "category": handleKeyNotInJson(
                        jsonContent, "category", "identifier"
                    ),
                    "level": handleKeyNotInJson(jsonContent, "level", "identifier"),
                    "language": handleKeyNotInJson(
                        jsonContent, "language", "identifier"
                    ),
                    "medium": handleKeyNotInJson(jsonContent, "medium"),
                    "license": handleKeyNotInJson(jsonContent, "license", "identifier"),
                    "creator": handleKeyNotInJson(jsonContent, "creator"),
                    "email_contact": handleKeyNotInJson(jsonContent, "email_contact"),
                    "github_contact": handleKeyNotInJson(jsonContent, "github_contact"),
                    "readable_github_contact": ", ".join(
                        handleKeyNotInJson(jsonContent, "github_contact")
                    ),
                    "readable_category": handleKeyNotInJson(
                        jsonContent, "category", "names", True
                    ),
                    "readable_level": handleKeyNotInJson(
                        jsonContent, "level", "names", True
                    ),
                    "readable_language": handleKeyNotInJson(
                        jsonContent, "language", "names", True
                    ),
                    "readable_license": handleKeyNotInJson(
                        jsonContent, "license", "names", True
                    ),
                    "html": rTut["html"],
                    "isStatic": True,
                }
            )

        return sorted(resolvedTutorials, key=lambda x: x["title"])
    except Exception as e:
        print("Static tutorials could not be loaded, error=%s" % e)
        # If we do not have a generated meta.json or we cannot read them,
        # we just do not return any static tutorials.
        # This is completly fine and dynamic tutorials can be used like normal.
        return []


staticTutorials = _resolveStaticTutorials()


def _resolveDynamicTutorial(evaluatedQs):
    """
    Get single tutorial as object (dict).

    :param evaluatedQs: Evaluated queryset object
    :return:
    """

    # Initialize dict that stores a tutorial
    currentTutorial = {
        "id": "",
        "title": "",
        "html": "",
        "markdown": "",
        "category": "",
        "media_src": "",
        "level": "",
        "language": "",
        "medium": "",
        "license": "",
        "creator": "",
        "email_contact": "",
        "github_contact": "",
        "readable_category": "",
        "readable_level": "",
    }

    readable_category = next(
        (x for x in CATEGORY_OPTIONS if x[0] == evaluatedQs.category),
        ("default", "Default"),
    )
    readable_level = next(
        (x for x in LEVEL_OPTIONS if x[0] == evaluatedQs.level), (0, "Default")
    )

    # populate dict
    currentTutorial.update(
        id=str(evaluatedQs.id),
        title=evaluatedQs.title,
        html=evaluatedQs.html,
        markdown=evaluatedQs.markdown,
        category=evaluatedQs.category,
        media_src=evaluatedQs.media_src,
        level=evaluatedQs.level,
        language=evaluatedQs.language,
        medium=evaluatedQs.medium,
        license=evaluatedQs.license,
        creator=evaluatedQs.creator,
        email_contact=evaluatedQs.email_contact,
        github_contact=evaluatedQs.github_contact,
        readable_category=readable_category[1],
        readable_level=readable_level[1],
    )

    return currentTutorial


def _resolveDynamicTutorials(tutorials_qs):
    """
    Get all tutorials(created via oep website) form django db.

    Evaluates a QuerySet and passes each evaluated object to the next function
    which returns a python dictionary that contains all parameters from the
    object as dict. The dict is added to a list to
    later merge the static and dynamic tutorials together.

    :param tutorials_qs:
    :return:
    """
    resolvedTutorials = []

    for tutorial in tutorials_qs:
        paramsToAdd = _resolveDynamicTutorial(tutorial)

        resolvedTutorials.append(paramsToAdd)

    return resolvedTutorials


def _gatherTutorials(id=None):
    """
    Collects all existing tutorials (static/dynamic) and returns them as a  single list.
    If id is set a single tutorial is returned (filter by id).

    :param id:
    :return:
    """

    # Retrieve allTutorials objects from db and cache
    dynamicTutorialsQs = Tutorial.objects.all()

    tutorials = staticTutorials.copy()
    tutorials.extend(_resolveDynamicTutorials(dynamicTutorialsQs))

    if id:
        filtered_elements = list(
            filter(lambda tutorial: tutorial["id"] == id, tutorials)
        )
        if filtered_elements:
            return filtered_elements[0]
        else:
            raise Http404

    return sorted(tutorials, key=lambda x: x["title"])


def _processFormInput(form):
    tutorial = form.save(commit=False)
    # Add more information to the dataset like date, time, contributor ...

    if tutorial.media_src:
        matchResult = youtubeUrlRegex.match(tutorial.media_src)
        videoId = matchResult.group(1) if matchResult else None
        if videoId:
            tutorial.media_src = "https://www.youtube.com/embed/" + videoId

    return tutorial


def cleanup_html(html):
    """

    Args:
        html (str): html code parsed from markdown
    Returns:
        str: cleaned html
    """
    html = BeautifulSoup(html, "html.parser")
    html = str(html)

    # remove iframes and script
    html = re.sub("<script[^>]*>.*</script>", "", html, re.IGNORECASE)
    html = re.sub("<iframe[^>]*>.*</iframe>", "", html, re.IGNORECASE)

    return html


def formattedMarkdown(markdown):
    """Markdown style text to html and return.
    This functionality is implemented using Markdown2 package.

    Args:
        markdown(str): markdown formatted text

    Returns:
        str: html
    """
    # TODO: Add syntax highliting,
    # add css files https://github.com/trentm/python-markdown2/wiki/fenced-code-blocks

    # list of extras: https://github.com/trentm/python-markdown2/wiki/Extras
    extras = {
        "break-on-newline": {},
        "fenced-code-blocks": {},
        "header-ids": {},  # Adds "id" attributes to headers. value is slug of header.
        "target-blank-links": {},  # Add target="_blank" to all <a> tags with an href.
        "task_list": {},  # Allows github-style task lists (i.e. check boxes),
        "html-classes": {
            "img": "img-fluid"  # add bootstrap class img-fluid to all images
        },
    }
    markdowner = Markdown(extras=extras)
    html = markdowner.convert(markdown)
    html = cleanup_html(html)

    return html


class ListTutorials(View):
    def get(self, request):
        """
        Load and list the available tutorials.

        :param request: A HTTP-request object sent by the Django framework.
        :return: Tutorials renderer
        """

        # Gathering all tutorials

        tutorials = _gatherTutorials()

        # special overview tutorials that are sticky
        tutorials_overview = [t for t in tutorials if t["category"] == "overview"]
        # sort them by title
        tutorials_overview = sorted(tutorials_overview, key=lambda t: t["title"])
        # change ids in collapsables (because we render multiple tutorials at once)
        # TODO: this is a quick and dirty solution.
        # it would be better (but slower) to use the parsed html and use bs4
        # to properly find tags
        for i, tut in enumerate(tutorials_overview):
            tut["html"] = tut["html"].replace(
                'data-target="#collapsable', 'data-target="#t%d-collapsable' % i
            )
            tut["html"] = tut["html"].replace(
                'id="collapsable', 'id="t%d-collapsable' % i
            )

        return render(
            request,
            "list.html",
            {"tutorials": tutorials, "tutorials_overview": tutorials_overview},
        )


class TutorialDetail(View):
    def get(self, request, tutorial_id):
        """
        Detail view for specific tutorial.

        :param request: A HTTP-request object sent by the Django framework.
        :return: Tutorials renderer
        """

        # Gathering all tutorials

        tutorial = _gatherTutorials(tutorial_id)

        return render(request, "detail.html", {"tutorial": tutorial})


class CreateNewTutorial(LoginRequiredMixin, CreateView):
    template_name = "add.html"
    redirect_url = "detail_tutorial"
    form_class = TutorialForm
    login_url = "/user/login/"
    redirect_field_name = "redirect_to"

    def form_valid(self, form):
        """
         validates a form and stores the values in the database and inserts a
         value for the tutorials field html.

        :param form:
        :return:
        """

        tutorial = _processFormInput(form)
        tutorial.save()

        # Convert markdown to HTML and save to db
        _html = formattedMarkdown(tutorial.markdown)
        addHtml = Tutorial.objects.get(pk=tutorial.id)
        addHtml.html = _html
        addHtml.save()

        return redirect(self.redirect_url, tutorial_id=tutorial.id)

    def addTutorialFromMarkdownFile(self):
        pass


class EditTutorials(LoginRequiredMixin, UpdateView):
    template_name = "add.html"
    redirect_url = "detail_tutorial"
    model = Tutorial
    form_class = TutorialForm
    pk_url_kwarg = "tutorial_id"
    login_url = "/user/login/"
    redirect_field_name = "redirect_to"

    def form_valid(self, form):
        """
        validates a form and stores the values in the database and inserts a
         value for the tutorials field html.

        :param form:
        :return:
        """
        tutorial = _processFormInput(form)
        tutorial.save()

        _html = formattedMarkdown(tutorial.markdown)
        addHtml = Tutorial.objects.get(pk=tutorial.id)
        addHtml.html = _html
        addHtml.save()

        return redirect(self.redirect_url, tutorial_id=tutorial.id)


class DeleteTutorial(LoginRequiredMixin, DeleteView):
    template_name = "tutorial_confirm_delete.html"
    model = Tutorial
    pk_url_kwarg = "tutorial_id"
    success_url = reverse_lazy("list_tutorials")
    login_url = "/user/login/"
    redirect_field_name = "redirect_to"
