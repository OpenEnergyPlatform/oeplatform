from django.shortcuts import render
from django.views import View

# Create your views here.



def _gatherTutorials(id = None):
    tutorials = [
        {
            "id": "b4031089-7765-47ad-927a-f1eb5fcf0641",
            "title": "Test-Tutorial",
            "html": "<span>Testeroni</span>"
        }
    ]

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




