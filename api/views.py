import json
import re
import time
from decimal import Decimal

from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

import login.models as login_models
import api.parser
from api import actions
from api import parser
from api.helpers.http import ModHttpResponse
from rest_framework.views import APIView
from dataedit.models import Table as DBTable

from rest_framework import status
from django.http import Http404

import sqlalchemy as sqla
import geoalchemy2  # Although this import seems unused is has to be here


def api_exception(f):
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except actions.APIError as e:
            return JsonResponse({'reason': e.message},
                                status=e.status)
    return wrapper


def permission_wrapper(permission, f):
    def wrapper(caller, request, *args, **kwargs):
        schema = kwargs.get('schema')
        table = kwargs.get('table')
        if request.user.is_anonymous or request.user.get_table_permission_level(
                DBTable.load(schema, table)) < permission:
            raise PermissionDenied
        else:
            return f(caller, request,*args, **kwargs)
    return wrapper


def require_write_permission(f):
    return permission_wrapper(login_models.WRITE_PERM, f)


def require_delete_permission(f):
    return permission_wrapper(login_models.DELETE_PERM, f)


def require_admin_permission(f):
    return permission_wrapper(login_models.ADMIN_PERM, f)


class Table(APIView):
    """
    Handels the creation of tables and serves information on existing tables
    """
    @api_exception
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

        schema, table = actions.get_table_name(schema, table, restrict_schemas=False)

        return JsonResponse({
            'schema': schema,
            'name': table,
            'columns': actions.describe_columns(schema, table),
            'indexed': actions.describe_indexes(schema, table),
            'constraints': actions.describe_constraints(schema, table)
        })

    @api_exception
    def post(self, request, schema, table):
        """
        Changes properties of tables and table columns
        :param request:
        :param schema:
        :param table:
        :return:
        """
        if schema not in ['model_draft', 'sandbox', 'test']:
            raise PermissionDenied
        if schema.startswith('_'):
            raise PermissionDenied
        json_data = request.data

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

    @api_exception
    def put(self, request, schema, table):
        """
        Every request to unsave http methods have to contain a "csrftoken".
        This token is used to deny cross site reference forwarding.
        In every request the header had to contain "X-CSRFToken" with the actual csrftoken.
        The token can be requested at / and will be returned as cookie.

        :param request:
        :return:
        """
        if schema not in ['model_draft', 'sandbox', 'test']:
            raise PermissionDenied
        if schema.startswith('_'):
            raise PermissionDenied
        if request.user.is_anonymous():
            raise PermissionDenied
        json_data = request.data['query']
        constraint_definitions = []
        column_definitions = []

        for constraint_definiton in json_data.get('constraints',[]):
            constraint_definiton.update({"action": "ADD",
                                         "c_table": table,
                                         "c_schema": schema})
            constraint_definitions.append(constraint_definiton)

        if 'columns' not in json_data:
            raise actions.APIError("Table contains no columns")
        for column_definition in json_data['columns']:
            column_definition.update({"c_table": table,
                                      "c_schema": schema})
            column_definitions.append(column_definition)

        result = actions.table_create(schema, table, column_definitions, constraint_definitions)

        perm, _ = login_models.UserPermission.objects.get_or_create(table=DBTable.load(schema, table),
                                                    holder=request.user)
        perm.level = login_models.ADMIN_PERM
        perm.save()
        request.user.save()
        return JsonResponse(result, status=status.HTTP_201_CREATED)


class Index(APIView):
    def get(self, request):
        pass

    def post(self, request):
        pass

    def put(self, request):
        pass


class Column(APIView):
    @api_exception
    def get(self, request, schema, table, column=None):
        schema, table = actions.get_table_name(schema, table, restrict_schemas=False)
        response = actions.describe_columns(schema, table)
        if column:
            try:
                response = response[column]
            except KeyError:
                raise actions.APIError('The column specified is not part of '
                                       'this table.')
        return JsonResponse(response)

    @api_exception
    @require_write_permission
    def post(self, request, schema, table, column):
        schema, table = actions.get_table_name(schema, table)
        response = actions.column_alter(request.data, {}, schema, table, column)
        return JsonResponse(response)

    @api_exception
    @require_write_permission
    def put(self, request, schema, table, column):
        schema, table = actions.get_table_name(schema, table)
        actions.column_add(schema, table, column, request.data['query'])
        return JsonResponse({}, status=201)


class Fields(APIView):
    def get(self, request, schema, table, id, column=None):
        schema, table = actions.get_table_name(schema, table, restrict_schemas=False)
        if not parser.is_pg_qual(table) or not  parser.is_pg_qual(schema) or not parser.is_pg_qual(id) or not parser.is_pg_qual(column):
            return ModHttpResponse({"error": "Bad Request", "http_status": 400})

        returnValue = actions.getValue(schema, table, column, id);

        return HttpResponse(returnValue if returnValue is not None else "", status= (404 if returnValue is None else 200))

    def post(self, request):
        pass

    def put(self, request):
        pass


class Rows(APIView):
    @api_exception
    def get(self, request, schema, table, row_id=None):
        schema, table = actions.get_table_name(schema, table, restrict_schemas=False)
        columns = request.GET.getlist('column')

        where = request.GET.get('where')
        if row_id and where:
            raise actions.APIError('Where clauses and row id are not allowed in the same query')

        orderby = request.GET.getlist('orderby')
        if row_id and orderby:
            raise actions.APIError('Order by clauses and row id are not allowed in the same query')

        limit = request.GET.get('limit')
        if row_id and limit:
            raise actions.APIError('Limit by clauses and row id are not allowed in the same query')

        offset = request.GET.get('offset')
        if row_id and offset:
            raise actions.APIError('Order by clauses and row id are not allowed in the same query')

        if offset is not None and not offset.isdigit():
            raise actions.APIError("Offset must be integer")
        if limit is not None and not limit.isdigit():
            raise actions.APIError("Limit must be integer")
        if not all(parser.is_pg_qual(c) for c in columns):
            raise actions.APIError("Columns are no postgres qualifiers")
        if not all(parser.is_pg_qual(c) for c in orderby):
            raise actions.APIError("Columns in groupby-clause are no postgres qualifiers")

        # OPERATORS could be EQUALS, GREATER, LOWER, NOTEQUAL, NOTGREATER, NOTLOWER
        # CONNECTORS could be AND, OR
        # If you connect two values with an +, it will convert the + to a space. Whatever.

        where_clauses = self.__read_where_clause(where)

        if row_id:
            where_clauses.append({'first': 'id',
             'operator': 'EQUALS',
             'second': row_id})

        # TODO: Validate where_clauses. Should not be vulnerable
        data = {'schema': schema,
                'table': table,
                'columns': columns,
                'where': where_clauses,
                'orderby': orderby,
                'limit': limit,
                'offset': offset
                }

        return_obj = self.__get_rows(request, data)

        # Extract column names from description
        cols = [col[0] for col in return_obj['description']]
        dict_list = [dict(zip(cols,row)) for row in return_obj['data']]

        if row_id:
            if dict_list:
                dict_list = dict_list[0]
            else:
                raise Http404

        # TODO: Figure out what JsonResponse does different.
        return JsonResponse(dict_list, safe=False)

    @api_exception
    @require_write_permission
    def post(self, request, schema, table, row_id=None, action=None):
        schema, table = actions.get_table_name(schema, table)
        column_data = request.data['query']
        status_code = status.HTTP_200_OK
        if row_id:
            response = self.__update_rows(request, schema, table, column_data, row_id)
        else:
            if action=='new':
                response = self.__insert_row(request, schema, table, column_data, row_id)
                status_code=status.HTTP_201_CREATED
            else:
                response = self.__update_rows(request, schema, table, column_data, None)
        actions.apply_changes(schema, table)
        return JsonResponse(response, status=status_code)

    @api_exception
    @require_write_permission
    def put(self, request, schema, table, row_id=None):
        schema, table = actions.get_table_name(schema, table)
        if not row_id:
            return JsonResponse(actions._response_error('This methods requires an id'),
                                status=status.HTTP_400_BAD_REQUEST)

        column_data = request.data['query']

        if row_id and column_data.get('id', int(row_id)) != int(row_id):
            raise actions.APIError(
                'Id in URL and query do not match. Ids may not change.',
                status=status.HTTP_409_CONFLICT)

        engine = actions._get_engine()
        conn = engine.connect()

        # check whether id is already in use
        exists = conn.execute('select count(*) '
                             'from {schema}.{table} '
                             'where id = {id};'.format(schema=schema,
                                                     table=table,
                                                     id=row_id)).first()[0] > 0 if row_id else False
        conn.close()
        if exists:
            response = self.__update_rows(request, schema, table, column_data, row_id)
            actions.apply_changes(schema, table)
            return JsonResponse(response)
        else:
            result = self.__insert_row(request, schema, table, column_data, row_id)
            actions.apply_changes(schema, table)
            return JsonResponse(result, status=status.HTTP_201_CREATED)


    def delete(self, request, table, schema, row_id=None):
        schema, table = actions.get_table_name(schema, table)
        result = self.__delete_rows(request, schema, table, row_id)
        actions.apply_changes(schema, table)
        return JsonResponse(result)

    @actions.load_cursor
    def __delete_rows(self, request, schema, table, row_id=None):
        where = request.GET.get('where')
        query = {
            'schema': schema,
            'table': table,
            'where': self.__read_where_clause(where),
        }

        context = {'cursor_id': request.data['cursor_id'],
                   'user': request.user}

        if row_id:
            query['where'].append({
                'left': {
                    'type': 'column',
                    'column': 'id'
                },
                'operator': '=',
                'right': row_id,
                'type': 'operator_binary'
            })
        return actions.data_delete(query, context)

    def __read_where_clause(self, where):
        where_expression = '^(?P<first>[\w\d_\.]+)\s*(?P<operator>' \
                           + '|'.join(parser.sql_operators) \
                           + ')\s*(?P<second>(^]).+)$'
        where_clauses = []
        if where:
            where_splitted = re.findall(where_expression, where)
            where_clauses = [{'first': match[0],
                              'operator': match[1],
                              'second': match[2]} for match in where_splitted]

        return where_clauses
    @actions.load_cursor
    def __insert_row(self, request, schema, table, row, row_id=None):
        if row_id and row.get('id', int(row_id)) != int(row_id):
            return actions._response_error('The id given in the query does not '
                                           'match the id given in the url')
        if row_id:
            row['id'] = row_id
        if not all(map(parser.is_pg_qual, row.keys())):
            return actions.get_response_dict(success=False,
                                             http_status_code=400,
                                             reason="Your request was malformed.")

        context = {'cursor_id': request.data['cursor_id'],
                   'user': request.user}

        query = {
            'schema': schema,
            'table': table,
            'values': [row]
        }

        if not row_id:
            query['returning'] = ['id']
        result = actions.data_insert(query, context)

        return result

    @actions.load_cursor
    def __update_rows(self, request, schema, table, row, row_id=None):
        context = {'cursor_id': request.data['cursor_id'],
                   'user': request.user}

        where = request.GET.get('where')

        query = {
            'schema': schema,
            'table': table,
            'where': self.__read_where_clause(where),
            'values': row
        }
        if row_id:
            query['where'].append({
                'left': {
                    'type': 'column',
                    'column': 'id'
                },
                'operator': '=',
                'right': row_id,
                'type': 'operator_binary'
            })
        return actions.data_update(query, context)

    @actions.load_cursor
    def __get_rows(self, request, data):
        table = actions._get_table(data['schema'], table=data['table'])
        params = {}
        params_count = 0
        columns = data.get('columns')

        if not columns:
            query = table.select()
        else:
            columns = [getattr(table.c, c) for c in columns]
            query = sqla.select(columns=columns)

        where_clauses = data.get('where')

        if where_clauses:
            for clause in where_clauses:
                first = getattr(table.c, clause['first'])
                second = clause['second']
                operator = parser.parse_sqla_operator(clause['operator'], first, second)
                query = query.where(operator)

        orderby = data.get('orderby')
        if orderby:
            query = query.order_by(orderby)

        limit = data.get('limit')
        if limit and limit.isdigit():
            query = query.limit(int(limit))

        offset = data.get('offset')
        if offset and offset.isdigit():
            query = query.offset(int(offset))

        cursor = actions._load_cursor(request.data['cursor_id'])
        actions._execute_sqla(query, cursor)

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


def create_ajax_handler(func):
    """
    Implements a mapper from api pages to the corresponding functions in
    api/actions.py
    :param func: The name of the callable function
    :return: A JSON-Response that contains a dictionary with the corresponding response stored in *content*
    """
    class AJAX_View(APIView):

        def get(self, request):
            return JsonResponse(self.execute(request))


        def post(self, request):
            return JsonResponse(self.execute(request))

        @actions.load_cursor
        def execute(self, request):
            content = request.data
            context = {'user': request.user,
                       'cursor_id': request.data['cursor_id']}
            data = func(json.loads(content.get('query', ['{}'])[0]),
                        context)

            # This must be done in order to clean the structure of non-serializable
            # objects (e.g. datetime)
            response_data = json.loads(json.dumps(data, default=date_handler))
            return {'content': response_data,
                    'cursor_id': context['cursor_id']}

    return AJAX_View.as_view()


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
