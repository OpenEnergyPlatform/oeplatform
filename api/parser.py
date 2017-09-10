###########
# Parsers #
###########
import decimal
import re
from datetime import datetime
from sqlalchemy import Table, MetaData, Column, select, column, func
from api.error import APIError, APIKeyError
from api.connection import _get_engine
import geoalchemy2  # Although this import seems unused is has to be here

pgsql_qualifier = re.compile(r"^[\w\d_\.]+$")


def get_or_403(dictionary, key):
    try:
        return dictionary[key]
    except KeyError:
        raise APIKeyError(dictionary, key)


def is_pg_qual(x):
    return pgsql_qualifier.search(x)


def quote(x):
    if not x.startswith('"') and '(' not in x:
        return '"' + x + '"'
    else:
        return x

def read_pgvalue(x):
    # TODO: Implement check for valid values
    if isinstance(x, str):
        return "'" + x + "'"
    if x is None:
        return 'null'
    return x


def read_operator(x, right):
    # TODO: Implement check for valid operators
    if isinstance(right, dict) and get_or_403(right, 'type') == 'value' and ('value' not in right or get_or_403(right, 'value') is None and x == '='):
        return 'is'
    return x


class ValidationError(Exception):
    def __init__(self, message, value):
        self.message = message
        self.value = value


def read_bool(s):
    if isinstance(s, bool):
        return s
    if s.lower() in ["true", "false"]:
        return s.lower() == "true"
    elif s.lower() in ["yes", "no"]:
        return s.lower() == "true"
    else:
        raise APIError("Invalid value in binary field", s)


def read_pgid(s):
    if is_pg_qual(s):
        return s
    raise APIError("Invalid identifier: '%s'"%s)


def set_meta_info(method, user, message=None):
    val_dict = {}
    val_dict['_user'] = user  # TODO: Add user handling
    val_dict['_message'] = message
    return val_dict


def parse_insert(d, context, message=None):
    table = Table(read_pgid(get_or_403(d, 'table')), MetaData(bind=_get_engine())
                  , autoload=True, schema=read_pgid(get_or_403(d, 'schema')))

    meta_cols = ['_message', '_user']

    field_strings = []
    for field in d.get('fields', []):
        assert ('type' in field and field['type'] == 'column'), 'Only pure column expressions are allowed in insert'

        field_strings.append(parse_expression(field))

    query = table.insert()

    if not 'method' in d:
        d['method'] = 'values'
    if d['method'] == 'values':
        if field_strings:
            raw_values = get_or_403(d, 'values')
            assert (isinstance(raw_values, list))
            values = map(lambda x: zip(field_strings, x), raw_values)
        else:
            values = get_or_403(d, 'values')

        def clear_meta(vals):
            val_dict = vals
            # make sure meta fields are not compromised
            if context['user'].is_anonymous:
                username = 'Anonymous'
            else:
                username = context['user'].name
            val_dict.update(set_meta_info('insert', username, message))
            return val_dict

        values = list(map(clear_meta, values))

        query = query.values(values)

    if 'returning' in d:
        query = query.returning(*map(Column, d['returning']))

    return query, values


def parse_select(d):
    """
        Defintion of a select query according to 
        http://www.postgresql.org/docs/9.3/static/sql-select.html
        
        not implemented:
            [ WITH [ RECURSIVE ] with_query [, ...] ]
            [ WINDOW window_name AS ( window_definition ) [, ...] ]
            [ FOR { UPDATE | NO KEY UPDATE | SHARE | KEY SHARE } [ OF table_name [, ...] ] [ NOWAIT ] [...] ]
    """
    distinct = d.get('distinct', False)

    L = None

    if 'fields' in d and d['fields']:
        L = []
        for field in d['fields']:
            col = parse_expression(field)
            if 'as' in field:
                col.label(read_pgid(field['as']))
            L.append(col)
    from_clause = parse_from_item(get_or_403(d, 'from'))
    if not L:
        L = '*'
    query = select(columns=L, distinct=distinct, from_obj=from_clause)

    # [ WHERE condition ]
    if d.get('where', False):
        query = query.where(parse_condition(d['where']))

    if 'group_by' in d:
        query = query.group_by([parse_expression(f) for f in d['group_by']])

    if 'having' in d:
        query.having([parse_condition(f) for f in d['having']])

    if 'select' in d:
        for constraint in d['select']:
            type = get_or_403(constraint, 'type')
            subquery = parse_select(get_or_403(constraint, 'query'))
            if type.lower() == 'union':
                query.union(subquery)
            elif type.lower() == 'intersect':
                query.intersect(subquery)
            elif type.lower() == 'except':
                query.except_(subquery)
    if 'order_by' in d:
        for ob in d['order_by']:
            expr = parse_expression(ob)
            desc = ob.get('ordering', 'asc').lower() == 'desc'
            if desc:
                expr = expr.desc()
            query = query.order_by(expr)

    if 'limit' in d:
        if isinstance(d['limit'], int) or d['limit'].is_digit():
            query = query.limit(int(d['limit']))
        else:
            raise APIError('Invalid LIMIT: Expected a digit')

    if 'offset' in d:
        if isinstance(d['offset'], int) or d['offset'].is_digit():
            query = query.offset(int(d['offset']))
        else:
            raise APIError('Invalid LIMIT: Expected a digit')
    return query


def parse_from_item(d):
    """
        Defintion of a from_item according to 
        http://www.postgresql.org/docs/9.3/static/sql-select.html
        
        return: A from_item string with checked psql qualifiers.
        
        Not implemented:
            with_query_name [ [ AS ] alias [ ( column_alias [, ...] ) ] ]
            [ LATERAL ] function_name ( [ argument [, ...] ] ) [ AS ] alias [ ( column_alias [, ...] | column_definition [, ...] ) ]
            [ LATERAL ] function_name ( [ argument [, ...] ] ) AS ( column_definition [, ...] )
    """
    # TODO: If 'type' is not set assume just a table name is present
    if isinstance(d, str):
        d = {'type': 'table', 'table': d}
    dtype = get_or_403(d, 'type')
    if dtype == 'table':
        schema_name = read_pgid(d['schema']) if 'schema' in d else None
        only = d.get('only', False)
        table_name = read_pgid(get_or_403(d, 'table'))
        table = Table(table_name, MetaData(bind=_get_engine()), schema=schema_name)
        if 'alias' in d:
            table = table.alias(read_pgid(d['alias']))
        engine = _get_engine()
        conn = engine.connect()
        exists = engine.dialect.has_table(conn, table.name, table.schema)
        conn.close()
        if not exists:
            raise APIError('Table not found: ' + str(table))

        return table
    elif dtype == 'select':
        return parse_select(d)
    elif dtype == 'join':
        left = parse_from_item(get_or_403(d, 'left'))
        right = parse_from_item(get_or_403(d, 'right'))
        is_outer = parse_from_item(get_or_403(d, 'is_outer'))
        full = parse_from_item(get_or_403(d, 'is_full'))
        on_clause = None
        if 'on' in d:
            on_clause = parse_condition(d['on'])
        return left.join(right,onclause=on_clause, isouter=is_outer, full=full)
    else:
        raise APIError('Unknown from-item: ' + dtype)


def parse_expression(d):
    # TODO: Implement
    if isinstance(d, dict):
        dtype = get_or_403(d, 'type')
        if dtype == 'column':
            name = get_or_403(d, 'column')
            if 'table' in d:
                name = d['table'] + '.' + name
                if 'schema' in d:
                    name = d['schema'] + '.' + name
            return column(name)
        if dtype == 'grouping':
            return parse_expression(get_or_403(d, 'grouping'))
        if dtype == 'operator':
            return parse_operator(d)
        if dtype == 'operator_binary':
            return parse_operator(d)
        if dtype == 'operator_unary':
            return parse_operator_unary(d)
        if dtype == 'modifier_unary':
            return parse_modifier_unary(d)
        if dtype == 'function':
            return parse_function(d)
        if dtype == 'value':
            if 'value' in d:
                return read_pgvalue(get_or_403(d, 'value'))
            else:
                return None
    if isinstance(d, list):
        return [parse_expression(x) for x in d]
    return d


def parse_condition(dl):
    if type(dl) == dict:
        dl = [dl]
    conditions = [parse_expression(d) for d in dl]
    query = conditions[0]
    for condition in conditions[1:]:
        query=query._and(condition)
    return query


def parse_operator(d):
    query = parse_sqla_operator(get_or_403(d, 'operator'),
                                parse_expression(get_or_403(d, 'left')),
                                parse_expression(get_or_403(d, 'right')))
    if 'as' in d:
        query = query.label(d['as'])
    return query



def parse_operator_unary(d):
    return "%s %s" % (read_operator(get_or_403(d,'operator'),
                                    get_or_403(d,'operand')),
                      parse_expression(get_or_403(d,'operand')))

def parse_modifier_unary(d):
    return "%s %s" % (parse_expression(get_or_403(d,'operand')),
                      read_operator(get_or_403(d, 'operator'),
                                    get_or_403(d,'operand')))

def parse_function(d):
    function = getattr(func, read_pgid(get_or_403(d, 'function')))
    operand_struc = get_or_403(d, 'operands')
    if isinstance(operand_struc, list):
        operands=map(parse_expression, operand_struc)
    else:
        operands = [parse_expression(operand_struc)]

    return function(*operands)


def cadd(d, key, string=None):
    if not string:
        string = key.upper() + ' '
    if d.pop(key, None):
        return string
    else:
        return ''


def parse_create_table(d):
    s = 'CREATE '
    if d.pop('global', None):
        s += 'GLOBAL '
    elif d.pop('local', None):
        s += 'LOCAL '

    s += (cadd(d, 'temp')
          + cadd(d, 'unlogged')
          + 'TABLE '
          + cadd(d, 'if_not_exists', 'IF NOT EXISTS ')
          + read_pgid(get_or_403(d,'name')))

    fieldstrings = []

    for field in d.pop('fields', []):
        fs = ''
        ftype = get_or_403(field, 'type')
        if ftype == 'column':
            fs += read_pgid(get_or_403(field,'name')) + ' '
            fs += read_pgid(get_or_403(field,'data_type')) + ' '
            collate = field.pop('collate', None)
            if collate:
                fs += read_pgid(collate)
            fs += ', '.join([parse_column_constraint(cons)
                             for cons in field.pop('constraints', [])]) + ' '
        elif ftype == 'table_constraint':
            fs += parse_table_constraint(field)
        elif ftype == 'like':
            fs += 'LIKE '


def parse_column_constraint(d):
    raise NotImplementedError
    # TODO: Implement


def parse_table_constraint(d):
    raise NotImplementedError
    # TODO: Implement


def parse_scolumnd_from_columnd(schema, table, name, column_description):
    # Migrate Postgres to Python Structures
    data_type = column_description.get('data_type')
    size = column_description.get('character_maximum_length')
    if size is not None and data_type is not None:
        data_type += "(" + str(size) + ")"

    notnull = column_description.get('is_nullable', False)

    return {'column_name': name,
            'not_null': notnull,
            'data_type': data_type,
            'new_name': column_description.get('new_name'),
            'c_schema': schema,
            'c_table': table
            }


def parse_sconstd_from_constd(schema, table, name_const, constraint_description):
    defi = constraint_description.get('definition')
    return {
        'action': None,  # {ADD, DROP}
        'constraint_type': constraint_description.get('constraint_typ'),  # {FOREIGN KEY, PRIMARY KEY, UNIQUE, CHECK}
        'constraint_name': name_const,
        'constraint_parameter': constraint_description.get('definition').split('(')[1].split(')')[0],
        # Things in Brackets, e.g. name of column
        'reference_table': defi.split('REFERENCES ')[1].split('(')[2] if 'REFERENCES' in defi else None,
        'reference_column': defi.split('(')[2].split(')')[1] if 'REFERENCES' in defi else None,
        'c_schema': schema,
        'c_table': table
    }


def replace_None_with_NULL(dictonary):
    # Replacing None with null for Database
    for key, value in dictonary.items():
        if value is None:
            dictonary[key] = 'NULL'

    return dictonary


def split(string, seperator):
    if string is None:
        return None
    else:
        return str(string).split(seperator)


def replace(string, occuring_symb, replace_symb):
    if string is None:
        return None
    else:
        return str(string).replace(occuring_symb, replace_symb)


def alchemyencoder(obj):
    """JSON encoder function for SQLAlchemy special classes."""
    if isinstance(obj, datetime.date):
        return obj.isoformat()
    elif isinstance(obj, decimal.Decimal):
        return float(obj)


sql_operators = {'EQUALS': '=',
                 'GREATER': '>',
                 'LOWER': '<',
                 'NOTEQUAL': '!=',
                 'NOTGREATER': '<=',
                 'NOTLOWER': '>=',
                 '=': '=',
                 '>': '>',
                 '<': '<',
                 '!=': '!=',
                 '<>': '!=',
                 '<=': '<=',
                 '>=': '>=',
                 }


def parse_sql_operator(key: str) -> str:
    return sql_operators.get(key)

def parse_sqla_operator(key, x, y):
    if key in ['EQUALS','=']:
        return x == y
    if key in ['GREATER', '>']:
        return x > y
    if key in ['LOWER', '<']:
        return x < y
    if key in ['NOTEQUAL', '<>', '!=']:
        return x != y
    if key in ['NOTGREATER', '<=']:
        return x <= y
    if key in ['NOTLOWER', '>=']:
        return x >= y
    raise APIError("Operator %s not supported"%key)