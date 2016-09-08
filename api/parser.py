###########
# Parsers #
###########
import re
from sqlalchemy import Table, MetaData
from datetime import datetime

pgsql_qualifier = re.compile(r"^[\w\d_\.]+$")


def is_pg_qual(x):
    return pgsql_qualifier.search(x)


def read_pgvalue(x):
    # TODO: Implement check for valid values
    if isinstance(x,str):
        return "'" + x + "'"
    if x is None:
        return 'null'
    return x


def read_operator(x, right):
    # TODO: Implement check for valid operators
    if right['type'] == 'value' and ('value' not in right or right['value'] is None and x == '='):
        return 'is'
    return x

class ValidationError(Exception):
    def __init__(self, message, value):
        self.message = message
        self.value = value


def read_bool(s):
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
    val_dict['_submitted'] = datetime.now()
    val_dict['_autocheck'] = False
    val_dict['_humancheck'] = False
    val_dict['_type'] = method
    val_dict['_message'] = message
    return val_dict


def parse_insert(d, engine, context, message=None):
    table = Table(read_pgid(d['table']), MetaData(bind=engine), autoload=True,
                  schema=read_pgid(d['schema']))

    meta_cols = ['_message', '_user', '_submitted', '_autocheck',
                   '_humancheck', '_type']

    field_strings = []
    for field in d.get('fields',[]):
        assert ('type' in field and field['type'] == 'column'), 'Only pure column expressions are allowed in insert'

        field_strings.append(parse_expression(field))


    query = table.insert()



    if d['method'] == 'default':
        query.values()
    elif d['method'] == 'values':
        if field_strings:
            assert(isinstance(d['values'],list))
            values = map(lambda x: zip(field_strings,x), d['values'])
        else:
            values = d['values']

        def clear_meta(vals):
            val_dict = vals
            # make sure meta fields are not compromised
            val_dict = set_meta_info('insert', context['user'].name, message)
            return val_dict

        values = list(map(clear_meta, values))

        query = query.values(values)
    elif d['method'] == 'query':
        raise NotImplementedError

    if 'returning' in d:
        query = query.returning(*map(parse_expression, d['returning']))

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
        if d['distinct']:
            s += ' (' + ', '.join(map(parse_expression, d)) + ') '

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
        s = 'only ' if d.pop('only', False) else ''
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
            if d['join_type'].lower() in ['join', 'inner join', 'left join',
                                          'left outer join', 'right join',
                                          'right outer join', 'full join',
                                          'full inner join', 'cross join']:
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


def parse_expression(d):
    # TODO: Implement
    if d['type'] == 'column':
        return d['column']
    if d['type'] == 'star':
        return ' * '
    if d['type'] == 'operator':
        return parse_operator(d)
    if d['type'] == 'function':
        return parse_function(d)
    if d['type'] == 'value':
        if 'value' in d:
            return read_pgvalue(d['value'])
        else:
            return 'null'
    raise NotImplementedError()


def parse_condition(dl):
    # TODO: Implement
    if type(dl) == dict:
        dl = [dl]
    conditionlist = []
    for d in dl:
        if d['type'] == 'operator_binary':
            conditionlist.append("%s %s %s" % (
                parse_expression(d['left']), read_operator(d['operator'],d['right']),
                parse_expression(d['right'])))

    return " " + " AND ".join(conditionlist)


def parse_operator(d):
    if d['operator'] == 'as':
        return parse_expression(d['labeled']) + " AS " + d['label_name']
    if d['operator'] == 'function':
        assert (read_pgid(d['function']))
        return '{f}({ops})'.format(f=d['function'], ops=', '.join(
            map(parse_expression, d['operands'])))
    return d


def parse_function(d):
    assert (read_pgid(d['function']))
    return '{f}({ops})'.format(f=d['function'], ops=', '.join(
        map(parse_expression, d['operands'])))


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
