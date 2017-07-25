###########
# Parsers #
###########
import decimal
import re
from datetime import datetime

from sqlalchemy import Table, MetaData, Column

pgsql_qualifier = re.compile(r"^[\w\d_\.]+$")


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
    if isinstance(right, dict) and right['type'] == 'value' and ('value' not in right or right['value'] is None and x == '='):
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
    else:
        raise ValidationError("Invalid value in binary field", s)


def read_pgid(s):
    if is_pg_qual(s):
        return s
    raise ValidationError("Invalid identifier", s)


def set_meta_info(method, user, message=None):
    val_dict = {}
    val_dict['_user'] = user  # TODO: Add user handling
    val_dict['_message'] = message
    return val_dict


def parse_insert(d, engine, context, message=None):
    table = Table(read_pgid(d['table']), MetaData(bind=engine), autoload=True,
                  schema=read_pgid(d['schema']))

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
            assert (isinstance(d['values'], list))
            values = map(lambda x: zip(field_strings, x), d['values'])
        else:
            values = d['values']

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

    return query


def parse_select(d):
    """
        Defintion of a select query according to 
        http://www.postgresql.org/docs/9.3/static/sql-select.html
        
        not implemented:
            [ WITH [ RECURSIVE ] with_query [, ...] ]
            [ WINDOW window_name AS ( window_definition ) [, ...] ]
            [ FOR { UPDATE | NO KEY UPDATE | SHARE | KEY SHARE } [ OF table_name [, ...] ] [ NOWAIT ] [...] ]
    """
    s = 'SELECT'
    # [ ALL | DISTINCT [ ON ( expression [, ...] ) ] ]
    if 'all' in d and read_bool(d['all']):
        s += ' ALL'
    elif 'distinct' in d:
        s += ' DISTINCT'

    L = []

    if 'fields' in d and d['fields']:
        for field in d['fields']:
            ss = parse_expression(field)
            if 'as' in field and '_count' not in d:
                ss += ' AS ' + read_pgid(field['as'])
            L.append(ss)
        s += ' ' + ', '.join(L)
    else:
        s += ' * '

    # [ FROM from_item [, ...] ]
    if 'from' in d:
        s += ' FROM ' + ', '.join(parse_from_item(f) for f in d['from'])

    # [ WHERE condition ]
    if 'where' in d:
        s += ' WHERE ' + parse_condition(d['where'])

    if 'group_by' in d:
        s += ' GROUP BY ' + ', '.join(
            parse_expression(f) for f in d['group_by'])

    if 'having' in d:
        s += ' HAVING ' + ', '.join(parse_condition(f) for f in d['having'])

    if 'select' in d:
        sel = d['select']
        if sel['type'].lower() in ['union', 'intersect', 'except']:
            s += ' ' + sel['type']
        else:
            raise ValidationError('UNION/INTERSECT/EXCEPT expected')
        if 'all' in sel and read_bool(sel['all']):
            s += ' ALL '
        elif 'distinct' in sel and read_bool(sel['distinct']):
            s += ' DISTINCT '
        s += parse_select(sel['select'])

    if 'order_by' in d:
        L = []
        for ob in d['order_by']:
            ss = ''
            ss += ' ORDER BY ' + parse_expression(ob)
            if 'ordering' in ob:
                if ob['ordering'] in ['asc', 'desc']:
                    ss += ' ' + ob['ordering']
                else:
                    ss += parse_operator(ob['ordering'])
            if 'nulls' in ob:
                ss += ' NULLS '
                if ob['nulls'].lower() in ['first', 'last']:
                    ss += ob['nulls']
                else:
                    raise ValidationError('Invalid NULLS option')
            L.append(ss)
        s += ', '.join(L)

    if 'limit' in d:
        s += ' LIMIT'
        if isinstance(d['limit'], str) and d['limit'].lower() == 'all':
            s += ' ALL'
        elif isinstance(d['limit'], int) or d['limit'].is_digit():
            s += ' ' + str(d['limit'])
        else:
            raise ValidationError('Invalid LIMIT (expected ALL or a digit)')

    if 'offset' in d and (
                isinstance(d['offset'], int) or d['offset'].is_digit()):
        s += ' OFFSET {} ROWS'.format(d['offset'])

    if 'fetch' in d and d['fetch'].is_digit():
        s += ' FETCH NEXT {} ROWS ONLY'.format(d['fetch'])
    return s


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
    if d['type'] == 'table':
        s = 'only ' if d.get('only', True) else ''
        schema = read_pgid(d.pop('schema', ''))
        if schema:
            s += schema + "."
        s += read_pgid(d['table'])
        if 'star' in d and read_bool(d['star']):
            s += ' * '
        if 'alias' in d and read_bool(d['alias']):
            s += ' AS ' + read_pgid(d['alias'])
            s += ' (' + \
                 ', '.join(
                     map(read_pgid, d['alias'].pop('column_aliases', []))) + \
                 ')'

    elif d['type'] == 'select':
        s = 'LATERAL ' if read_bool(d['lateral']) else ''
        s += '(' + parse_select(d['select']) + ') '
        if 'alias' in d and read_bool(d['alias']):
            s += ' AS ' + read_pgid(d['alias'])
            s += ' (' + \
                 ', '.join(
                     map(read_pgid, d['alias'].pop('column_aliases', []))) + \
                 ')'

    elif d['type'] == 'join':
        s = parse_from_item(d['left'])
        if 'natural' in d and read_bool(d['natural']):
            s += ' NATURAL'
        if 'join_type' in d:
            if d['join_type'].lower().strip() in ['join', 'inner join', 'left join',
                                          'left outer join', 'right join',
                                          'right outer join', 'full join',
                                          'full inner join', 'full outer join', 'cross join']:
                s += ' ' + d['join_type']
            else:
                raise ValidationError('Invalid join type')
        else:
            s += ' JOIN '

        s += ' ' + parse_from_item(d['right'])

        if 'on' in d:
            s += ' ON ' + parse_condition(d['on'])
        elif 'using' in d:
            s += ' USING (' + ', '.join(map(read_pgid, d['using'])) + ')'
    return s


def parse_expression(d, separator=', '):
    # TODO: Implement
    if isinstance(d, dict):
        if d['type'] == 'column':
            name = quote(d['column'])
            if 'table' in d:
                name = quote(d['table']) + '.' + name
                if 'schema' in d:
                    name = quote(d['schema']) + '.' + name
            return name
        if d['type'] == 'grouping':
            return '(' + parse_expression(d['grouping']) + ')'
        if d['type'] == 'star':
            return ' * '
        if d['type'] == 'operator':
            return parse_operator(d)
        if d['type'] == 'operator_binary':
            return parse_operator(d)
        if d['type'] == 'operator_unary':
            return parse_operator_unary(d)
        if d['type'] == 'modifier_unary':
            return parse_modifier_unary(d)
        if d['type'] == 'function':
            return parse_function(d)
        if d['type'] == 'value':
            if 'value' in d:
                return read_pgvalue(d['value'])
            else:
                return 'null'
    if isinstance(d, list):
        return separator.join(parse_expression(x) for x in d)
    if isinstance(d, str):
        return '\'' + d + '\''
    else:
        return d


def parse_condition(dl):
    # TODO: Implement
    if type(dl) == dict:
        dl = [dl]

    return " " + " AND ".join([parse_expression(d, separator=' AND ') for d in dl])


def parse_operator(d):
    if d['operator'] == 'as':
        return parse_expression(d['labeled']) + " AS " + d['label_name']
    else:
        return "%s %s %s" % (
            parse_expression(d['left']), read_operator(d['operator'], d['right']),
            parse_expression(d['right']))


def parse_operator_unary(d):
    return "%s %s" % (read_operator(d['operator'], d['operand']),
                      parse_expression(d['operand']))

def parse_modifier_unary(d):
    return "%s %s" % (parse_expression(d['operand']),
                      read_operator(d['operator'], d['operand']))

def parse_function(d):
    assert (read_pgid(d['function']))
    operand_struc = d['operands']
    if isinstance(operand_struc, list):
        operands = '(' + (', '.join(map(parse_expression, d['operands']))) + ')'
    else:
        operands = parse_expression(operand_struc)

    return '{f}{ops}'.format(f=d['function'], ops=operands)


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
          + read_pgid(d['name']))

    fieldstrings = []

    for field in d.pop('fields', []):
        fs = ''
        if field['type'] == 'column':
            fs += read_pgid(field['name']) + ' '
            fs += read_pgid(field['data_type']) + ' '
            collate = field.pop('collate', None)
            if collate:
                fs += read_pgid(collate)
            fs += ', '.join([parse_column_constraint(cons)
                             for cons in field.pop('constraints', [])]) + ' '
        elif field['type'] == 'table_constraint':
            fs += parse_table_constraint(field)
        elif field['type'] == 'like':
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

    notnull = None
    is_nullable = column_description.get('is_nullable')
    if is_nullable is not None:
        notnull = 'NO' in is_nullable

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


sql_operators = {'EQUAL': '=',
                 'GREATER': '>',
                 'LOWER': '<',
                 'NOTEQUAL': '!=',
                 'NOTGREATER': '<=',
                 'NOTLOWER': '>=',
                 }


def parse_sql_operator(key: str) -> str:
    return sql_operators.get(key)
