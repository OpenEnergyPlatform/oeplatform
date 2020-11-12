from django.shortcuts import render, redirect
from django.views import View
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import exceptions, reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin

import os
import json

from copy import deepcopy

from django.conf import settings

from markdown2 import Markdown

from .forms import TutorialForm
from .models import Tutorial

import re
# Create your views here.

youtubeUrlRegex = re.compile('^.*youtube\.com\/watch\?v=(?P<id>[A-z0-9]+)$')

def _resolveStaticTutorial(tutorial):
    try:
        with open(os.path.join(settings.BASE_DIR, "examples", "build", tutorial["fileName"]), 'r') as buildFile:
                buildFileContent = buildFile.read()

        return {
            "html": buildFileContent
        }

    except:
        return {"html": "Tutorial is missing"}


def _resolveStaticTutorials():
    resolvedTutorials = []

    # Load list of static tutorials

    try:
        with open(os.path.join(os.getcwd(), "examples", "build", 'meta.json'), 'r') as metaFile:
            metaContent = json.load(metaFile)

            for tutorial in metaContent:
                rTut = _resolveStaticTutorial(tutorial)
                resolvedTutorials.append({
                    'id': tutorial['id'],
                    'fileName': tutorial['fileName'],
                    'title': tutorial['title'],
                    'html': rTut['html'],
                })

            return sorted(resolvedTutorials, key=lambda x: x.title)
    except Exception as e:
        print('Static tutorials could not be loaded, error=%s' % e)
        # If we do not have a generated meta.json or we cannot read them, we just do not return any static
        # tutorials. This is completly fine and dynamic tutorials can be used like normal.
        return []


def _resolveDynamicTutorial(evaluatedQs):
    """


    :param evaluatedQs: Evaluated queryset object
    :return:
    """

    # Initialize dict that stores a tutorial
    currentTutorial = {'id': '', 'title': '', 'html': '', 'markdown': '', 'category': '', 'media_src': '', 'level': ''}

    # populate dict
    currentTutorial.update(id=str(evaluatedQs.id),
                           title=evaluatedQs.title,
                           html=evaluatedQs.html,
                           markdown=evaluatedQs.markdown,
                           category= evaluatedQs.category,
                           media_src= evaluatedQs.media_src,
                           level=evaluatedQs.level)

    return currentTutorial


def _resolveDynamicTutorials(tutorials_qs):
    """
    Evaluates a QuerySet and passes each evaluated object to the next function which returns a python
    dictionary that contains all parameters from the object as dict. The dict is added to a list to
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
    Collects all existing tutorials (static/dynamic) and returns them as a list. If an id is
    specified as parameter a specific tutorial is returned filtered by id.

    :param id:
    :return:
    """

    # Retrieve allTutorials objects from db and cache
    dynamicTutorialsQs = Tutorial.objects.all()

    tutorials = _resolveStaticTutorials()
    tutorials.extend(_resolveDynamicTutorials(dynamicTutorialsQs))

    if id:
        filteredElement = list(filter(lambda tutorial: tutorial["id"] == id, tutorials))[0]
        return filteredElement

    return tutorials

def _processFormInput(form):
    tutorial = form.save(commit=False)
    # Add more information to the dataset like date, time, contributor ...

    if tutorial.media_src:
        matchResult = youtubeUrlRegex.match(tutorial.media_src)
        videoId = matchResult.group(1) if matchResult else None
        if videoId:
            tutorial.media_src = "https://www.youtube.com/embed/" + videoId

    return tutorial

def formattedMarkdown(markdown):
    """
    A parameter is used to enter a text formatted as markdown that is formatted
    to html and returned. This functionality is implemented using Markdown2.

    :param markdown:
    :return:
    """

    # escapes html but also escapes html code blocks lke "exampel code:
    #                                                    (1 tab)  code"
    # checkbox also not rendered as expected "- [ ]"
    markdowner = Markdown(safe_mode=True)
    markdowner.html_removed_text = ""

    return markdowner.convert(markdown)


class ListTutorials(View):
    def get(self, request):
        """
        Load and list the available tutorials.

        :param request: A HTTP-request object sent by the Django framework.
        :return: Tutorials renderer
        """

        # Gathering all tutorials

        tutorials = _gatherTutorials()

        return render(
            request, 'list.html', {"tutorials": tutorials}
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

        return render(
            request, 'detail.html', {"tutorial": tutorial}
        )


class CreateNewTutorial(LoginRequiredMixin, CreateView):
    template_name = 'add.html'
    redirect_url = 'detail_tutorial'
    form_class = TutorialForm
    login_url = '/user/login/'
    redirect_field_name = 'redirect_to'

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
    template_name = 'add.html'
    redirect_url = 'detail_tutorial'
    model = Tutorial
    form_class = TutorialForm
    pk_url_kwarg = 'tutorial_id'
    login_url = '/user/login/'
    redirect_field_name = 'redirect_to'

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
    template_name = 'tutorial_confirm_delete.html'
    model = Tutorial
    pk_url_kwarg = 'tutorial_id'
    success_url = reverse_lazy('list_tutorials')
    login_url = '/user/login/'
    redirect_field_name = 'redirect_to'








