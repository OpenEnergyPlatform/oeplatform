import json
import time

from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from api import actions


class ModHttpResponse(HttpResponse):
    def __init__(self, dictonary):
        if dictonary['success']:
            HttpResponse.__init__(self, status=200)

        # TODO: Find smarter way to just define a parameter, if an expression is true.
        if dictonary['error'] is not None:
            HttpResponse.__init__(self, status=dictonary['http_status'], reason = dictonary['error'])
        else:
            HttpResponse.__init__(self, status=dictonary['http_status'])


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

            # Migrate Postgres to Python Structures
            data_type = json_data.get('data_type')

            size = json_data.get('character_maximum_length')
            if size is not None and data_type is not None:
                data_type += "(" + str(size) + ")"


            notnull = None
            is_nullable = json_data.get('is_nullable')
            if is_nullable is not None:
                notnull = 'NO' in is_nullable

            column_definition = {'name': json_data['name'],
                                 'notnull': notnull,
                                 'data_type': data_type,
                                 'new_name': json_data.get('newname')
                                 }

            result = actions.table_change_column(schema, table, column_definition)
            return ModHttpResponse(result)

        elif 'constraint' in json_data['type']:

            # Input has nothing to do with DDL from Postgres.
            # Input is completely different.
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

            result = actions.table_change_constraint(schema, table, constraint_definition)
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

        # There must be a better way to do this.
        json_data = json.loads(request.body.decode("utf-8"))

        constraints = []
        columns = []

        for key in json_data['constraints']:
            value = json_data['constraints'][key]['definition']

            # "PRIMARY KEY (groups_id)"
            # "FOREIGN KEY (database_id) REFERENCES reference.jabref_database(database_id)"

            # Creating dicts with one entry is inefficient.
            # Passing more parameters is easy later which is needed
            if 'PRIMARY KEY' or 'FOREIGN KEY' in value:
                insert_val = {'definition': value}

                constraints.append(insert_val)

        for c in json_data['columns']:

            # Parse Datatype
            data_type = json_data['columns'][c]['data_type']

            # Check for size
            size = json_data['columns'][c]['character_maximum_length']
            if isinstance(size, int):
                data_type += "(" + str(size) + ")"

            # Check for null

            not_null = 'NO' in json_data['columns'][c]['is_nullable']

            x = {'datatype': data_type,
                 'notnull': not_null,
                 'name': str(c),
                 }

            columns.append(x)

        result = actions.table_create(schema, table, columns, constraints)

        return ModHttpResponse(result)


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
        return JsonResponse({'content': response_data}, safe=False)

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
