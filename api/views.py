import json
import time
from decimal import Decimal

from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

import api.parser
from api import actions
from api import parser
from api.helpers.http import ModHttpResponse
from rest_framework.views import APIView
import geoalchemy2  # Although this import seems unused is has to be here

class Table(APIView):
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
        return JsonResponse({
            'schema': schema,
            'name': table,
            'columns': actions.describe_columns(schema, table),
            'indexed': actions.describe_indexes(schema, table),
            'constraints': actions.describe_constraints(schema, table)
        })

    def post(self, request, schema, table):
        """
        Changes properties of tables and table columns
        :param request:
        :param schema:
        :param table:
        :return:
        """

        json_data = json.loads(request.body.decode("utf-8"))

        if 'column' in json_data['type']:

            column_definition = api.parser.parse_scolumnd_from_columnd(schema, table, json_data['name'], json_data)
            result = actions.queue_column_change(schema, table, column_definition)
            return ModHttpResponse(result)

        elif 'constraint' in json_data['type']:

            # Input has nothing to do with DDL from Postgres.
            # Input is completely different.
            # Using actions.parse_sconstd_from_constd is not applicable
            # dict.get() returns None, if key does not exist
            constraint_definition = {
                'action': json_data['action'],  # {ADD, DROP}
                'constraint_type': json_data.get('constraint_type'),  # {FOREIGN KEY, PRIMARY KEY, UNIQUE, CHECK}
                'constraint_name': json_data.get('constraint_name'),  # {myForeignKey, myUniqueConstraint}
                'constraint_parameter': json_data.get('constraint_parameter'),
                # Things in Brackets, e.g. name of column
                'reference_table': json_data.get('reference_table'),
                'reference_column': json_data.get('reference_column')
            }

            result = actions.queue_constraint_change(schema, table, constraint_definition)
            return ModHttpResponse(result)
        else:
            return ModHttpResponse(actions.get_response_dict(False, 400, 'type not recognised'))

    def put(self, request, schema, table):
        """
        Every request to unsave http methods have to contain a "csrftoken".
        This token is used to deny cross site reference forwarding.
        In every request the header had to contain "X-CSRFToken" with the actual csrftoken.
        The token can be requested at / and will be returned as cookie.

        :param request:
        :return:
        """
        json_data = request.data['query']

        constraint_definitions = []
        column_definitions = []

        for constraint_definiton in json_data.get('constraints',[]):
            constraint_definiton.update({"action": "ADD",
                                         "c_table": table,
                                         "c_schema": schema})
            constraint_definitions.append(constraint_definiton)

        if 'columns' not in json_data:
            return
        for column_definition in json_data['columns']:
            column_definition.update({"c_table": table,
                                      "c_schema": schema})
            column_definitions.append(column_definition)

        result = actions.table_create(schema, table, column_definitions, constraint_definitions)

        return ModHttpResponse(result)


class Index(APIView):
    def get(self, request):
        pass

    def post(self, request):
        pass

    def put(self, request):
        pass


class Fields(APIView):
    def get(self, request, schema, table, id, column):

        if not parser.is_pg_qual(table) or not  parser.is_pg_qual(schema) or not parser.is_pg_qual(id) or not parser.is_pg_qual(column):
            return ModHttpResponse({"error": "Bad Request", "http_status": 400})

        returnValue = actions.getValue(schema, table, column, id);

        return HttpResponse(returnValue if returnValue is not None else "", status= (404 if returnValue is None else 200))

    def post(self, request):
        pass

    def put(self, request):
        pass


class Rows(APIView):
    def get(self, request, schema, table):
        columns = request.GET.get('columns')
        where = request.GET.get('where')
        orderby = request.GET.get('orderby')
        limit = request.GET.get('limit')
        offset = request.GET.get('offset')

        # OPERATORS could be EQUAL, GREATER, LOWER, NOTEQUAL, NOTGREATER, NOTLOWER
        # CONNECTORS could be AND, OR
        # If you connect two values with an +, it will convert the + to a space. Whatever.

        where_clauses = None
        if where:
            where_splitted = where.split(' ')
            where_clauses = [{'first': where_splitted[4 * i],
                              'operator': where_splitted[4 * i + 1],
                              'second': where_splitted[4 * i + 2],
                              'connector': where_splitted[4 * i + 3] if len(where_splitted) > 4 * i + 3 else None} for i
                             in range(int(len(where_splitted) / 4) + 1)]

        # TODO: Validate where_clauses. Should not be vulnerable
        data = {'schema': schema,
                'table': table,
                'columns': parser.split(columns, ','),
                'where': where_clauses,
                'orderby': parser.split(orderby, ','),
                'limit': limit,
                'offset': offset
                }

        return_obj = actions.get_rows(request, data)

        # TODO: Figure out what JsonResponse does different.
        response = json.dumps(return_obj, default=date_handler)
        return HttpResponse(response, content_type='application/json')

    def post(self, request):
        pass

    def put(self, request, schema, table):

        data = json.loads(request.body.decode("utf-8"))

        column_data = data['columnData']

        for key, value in column_data.items():

            if not parser.is_pg_qual(key):  # or ((not str(value).isdigit()) and not parser.is_pg_qual(value)):
                return JsonResponse(actions.get_response_dict(success=False, http_status_code=400,
                                                              reason="Your request was malformed."), 400)

        result = actions.put_rows(schema, table, column_data)

        return ModHttpResponse(result)


class Session(APIView):
    def get(self, request, length=1):
        return request.session['resonse']


def date_handler(obj):
    """
    Implements a handler to serialize dates in JSON-strings
    :param obj: An object
    :return: The str method is called (which is the default serializer for JSON) unless the object has an attribute  *isoformat*
    """
    if isinstance(obj, Decimal):
        return float(obj)
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    else:
        return str(obj)


# Create your views here.


def create_ajax_handler(func, create_cursor=True):
    """
    Implements a mapper from api pages to the corresponding functions in
    api/actions.py
    :param func: The name of the callable function
    :return: A JSON-Response that contains a dictionary with the corresponding response stored in *content*
    """

    @csrf_exempt
    def execute(request):
        content = request.POST if request.POST else request.GET
        context = {'user': request.user}
        if 'cursor_id' in content:
            context['cursor_id'] = int(content['cursor_id'])
        else:
            if create_cursor:
                context.update(actions.open_raw_connection(request, context))
                context.update(actions.open_cursor(request, context))
        data = func(json.loads(content.get('query', '{}')), context)

        # This must be done in order to clean the structure of non-serializable
        # objects (e.g. datetime)
        response_data = json.loads(json.dumps(data, default=date_handler))
        return JsonResponse({'content': response_data,
                             'cursor_id': context['cursor_id']}, safe=False)

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
