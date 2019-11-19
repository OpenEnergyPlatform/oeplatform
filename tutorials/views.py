from django.shortcuts import render
from django.views import View

from os.path import join

from uuid import uuid4

from copy import deepcopy

from django.conf import settings

# Create your views here.


staticTutorials = [
    {
        "id": "e59819c7-46fd-4528-b2bd-f37e8866d1df",
        "title": "appBBB-UML.html",
        "fileName": "appBBB-UML.html"
    },
    {
        "id": "5064610a-596a-4911-8862-e9d815d872d4",
        "title": "df_normalize_denormalize.html",
        "fileName": "df_normalize_denormalize.html"
    },
    {
        "id": "56c675ea-93ae-43cf-886c-01f4fc98711f",
        "title": "germany-UML.html",
        "fileName": "germany-UML.html"
    },
    {
        "id": "7e51c992-5a8a-419f-b778-31a1dd32db4a",
        "title": "OEP-api_template.html",
        "fileName": "OEP-api_template.html"
    },
    {
        "id": "61201725-493f-4dd0-b9aa-6e0f6d6aa550",
        "title": "OEP_API_tutorial_part1.html",
        "fileName": "OEP_API_tutorial_part1.html"
    },
    {
        "id": "c4e48c2d-626a-45ad-aa68-a6711c7af85c",
        "title": "OEP_API_tutorial_part2.html",
        "fileName": "OEP_API_tutorial_part2.html"
    },
    {
        "id": "eab6aece-cff8-4265-989f-3dd9d7d03026",
        "title": "OEP_API_tutorial_part3.html",
        "fileName": "OEP_API_tutorial_part3.html"
    },
    {
        "id": "a1d6fc71-6694-4704-8ab4-950be4de9561",
        "title": "OEP_API_tutorial_part4.html",
        "fileName": "OEP_API_tutorial_part4.html"
    },
    {
        "id": "ea5e68ef-bcfb-47a1-9768-b5184797bcab",
        "title": "OEP-oedialect_eGoDP.html",
        "fileName": "OEP-oedialect_eGoDP.html"
    },
    {
        "id": "44634b85-389f-4c26-988f-217ee9c6f768",
        "title": "OEP-oedialect-geoquery.html",
        "fileName": "OEP-oedialect-geoquery.html"
    },
    {
        "id": "cc9e9a5e-826b-4296-a544-e057003dd22c",
        "title": "OEP-oedialect.html",
        "fileName": "OEP-oedialect.html"
    },
    {
        "id": "99f35e78-49ca-47f4-9926-d5197c0e3ffe",
        "title": "OEP-oedialect_template.html",
        "fileName": "OEP-oedialect_template.html"
    },
    {
        "id": "c254d5e4-479b-423f-92fb-c10411abab66",
        "title": "OEP-oedialect_upload_from_csv.html",
        "fileName": "OEP-oedialect_upload_from_csv.html"
    },
    {
        "id": "bc6ad0f4-d9ed-4f00-84e4-f3b62f3eafca",
        "title": "rli_tool_validate-metadata-datapackage.html",
        "fileName": "rli_tool_validate-metadata-datapackage.html"
    },
    {
        "id": "43d4da3a-4fef-4524-8c17-7214637e44ad",
        "title": "UML Tutorial.html",
        "fileName": "UML Tutorial.html"
    },
]

def _resolveStaticTutorial(tutorial):
    with open(join(settings.BASE_DIR, "examples", "build", tutorial["fileName"]), 'r') as buildFile:
            buildFileContent = buildFile.read()


    return {
        "html": buildFileContent
    }

def _resolveStaticTutorials(tutorials):

    resolvedTutorials = []

    # I was not able to solve this problem without an object spread operator due to my JS history.
    # The copy does not have a specific reason but not iterating over the array which is modified in interation.

    for tutorial in tutorials:
        paramsToAdd = _resolveStaticTutorial(tutorial)
        copiedTutorial = deepcopy(tutorial)
        copiedTutorial.update(paramsToAdd)

        resolvedTutorials.append(copiedTutorial)


    return resolvedTutorials


staticTutorialsResolved = _resolveStaticTutorials(staticTutorials)

def _gatherTutorials(id = None):


    # TODO: Add dynamic tutorials
    tutorials = staticTutorialsResolved

    if id:
        filteredElement = list(filter(lambda tutorial: tutorial["id"] == id, tutorials))[0]
        return filteredElement

    return tutorials

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
        Load and list the available tutorials.
        :param request: A HTTP-request object sent by the Django framework.
        :return: Tutorials renderer
        """

        # Gathering all tutorials

        tutorial = _gatherTutorials(tutorial_id)


        return render(
            request, 'detail.html', {"tutorial": tutorial}
        )




