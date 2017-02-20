from django.shortcuts import render
from api import actions
from django.http import HttpResponse
import json
from django.views.decorators.csrf import csrf_exempt
from django_ajax.decorators import ajax
import json
import time

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from django.http import JsonResponse

from django.views.generic import View

class Table(View):
    """
    Handels the creation of tables and serves information on existing tables
    """
    def get(self, request, schema, table):
        """
        Returns a dictionary that describes the DDL-make-up of this table.
        Fields are:

        * name : Name of the table,
        * schema: Name of the schema,
        * columns : as specified in :meth:`api.actions.describe_columns`
        * indexes : as specified in :meth:`api.actions.describe_indexes`
        * constraints: as specified in
                    :meth:`api.actions.describe_constraints`

        :param request:
        :return:
        """
        return {
            'schema': schema,
            'name': table,
            'columns': actions.describe_columns(schema,table),
            'indexed': actions.describe_indexes(schema, table),
            'constraints': actions.describe_constraints(schema, table)
        }




    def post(self, request):
        pass

    def put(self, request):
        pass


class Index(View):

    def get(self, request):
        pass

    def post(self, request):
        pass

    def put(self, request):
        pass

class Rows(View):

    def get(self, request):
        pass

    def post(self, request):
        pass

    def put(self, request):
        pass

class Session(View):
    def get(self, request, length=1):
        return request.session['resonse']


def date_handler(obj):
    """
    Implements a handler to serialize dates in JSON-strings
    :param obj: An object
    :return: The str method is called (which is the default serializer for JSON) unless the object has an attribute  *isoformat*
    """
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    else:
        return str(obj)


# Create your views here.


def create_ajax_handler(func):
    """
    Implements a mapper from api pages to the corresponding functions in
    api/actions.py
    :param func: The name of the callable function
    :return: A JSON-Response that contains a dictionary with the corresponding response stored in *content*
    """
    @csrf_exempt
    def execute(request):
        content = request.POST if request.POST else request.GET
        data = func(json.loads(content['query']), {'user': request.user})

        # This must be done in order to clean the structure of non-serializable
        # objects (e.g. datetime)
        response_data = json.loads(json.dumps(data, default=date_handler))
        return JsonResponse({'content':response_data}, safe=False)
    return execute


def stream(data):
    """
    TODO: Implement streaming of large datasets
    :param data:
    :return:
    """
    size = len(data)
    chunck = 100

    for i in range(size):
        yield json.loads(json.dumps(data[i], default=date_handler))
        time.sleep(1)