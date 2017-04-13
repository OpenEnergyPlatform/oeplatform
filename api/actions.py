import re
import sqlalchemy as sqla
import json

import traceback

from api import parser
from api.parser import is_pg_qual, read_bool, read_pgid

from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy
from api import references
from sqlalchemy import func, MetaData, Table
from datetime import datetime
import oeplatform.securitysettings as sec

pgsql_qualifier = re.compile(r"^[\w\d_\.]+$")
_ENGINES = {}


import geoalchemy2

Base = declarative_base()

class InvalidRequest(Exception):
    pass


def _get_table(schema, table):
    engine = _get_engine()
    metadata = MetaData()

    return Table(table, metadata, autoload=True, autoload_with=engine, schema=schema)

class DataStore(Base):
    __tablename__ = 'ckan_datastore'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True,
                           autoincrement=True)
    schema = sqlalchemy.Column(sqlalchemy.String(30))
    table = sqlalchemy.Column(sqlalchemy.String(30))
    resource = sqlalchemy.Column(sqlalchemy.String(40))
    dataset = sqlalchemy.Column(sqlalchemy.String(30))



def get_table_resource(schema, table):
    result = sqlalchemy.select(DataStore.c.resource, DataStore.c.dataset).where(
        DataStore.c.table == table, DataStore.c.schema == schema)
    if not result:
        return None
    else:
        return result.first()

def table_create(request, context=None):
    # TODO: Authentication
    # TODO: column constrains: Unique,
    # load schema name and check for sanity
    engine = _get_engine()

    schema = read_pgid(request["schema"])
    create_schema = not has_schema(request)
    # Check whether schema exists

    # load table name and check for sanity
    table = read_pgid(request.pop("table"))

    # Process fields
    fieldstrings = []
    fields = request.pop("fields", [])
    foreign_keys = []
    primary_keys = []
    for field in fields:
        fname = read_pgid(field["name"])
        type_name = field["type"]

        # TODO: check whether type_name is an actual postgres type
        # if not engine.dialect.has_type(connection,type_name):
        #    raise p.toolkit.ValidationError("Invalid field type: '%s'"% type_name )
        fs = field["name"] + " " + type_name

        if "pk" in field:
            if read_bool(field["pk"]):
                primary_keys.append([field["name"]])
                fs += " PRIMARY KEY"

        fieldstrings.append(fs)

    table_constraints = {"unique": [], "pk": primary_keys, "fk": foreign_keys}
    constraints = request.pop('constraints', {})
    if 'fk' in constraints:
        assert isinstance(constraints['fk'], list), \
            "Foreign Keys should be a list"
        for fk in constraints['fk']:
            print(fk)
            assert all(map(is_pg_qual, [fk["schema"], fk["table"]] + fk["fields"] + fk["names"])), "Invalid identifier"
            if 'on_delete' in fk:
                assert fk["on delete"].lower() in ["cascade", "no action",
                                               "restrict", "set null",
                                               "set default"], "Invalid on delete action"
            else:
                fk["on_delete"] = "no action"
            foreign_keys.append((fk["names"],
                                 fk["schema"],
                                 fk["table"],
                                 fk["fields"],
                                 fk["on_delete"]))

    #fieldstrings.append("_comment int")


    #foreign_keys.append(("_comment", schema, "_"+table+"_cor", "id", "no action"))
    fk_constraints = []
    for (
            fk_field1, fk_schema, fk_table, fk_field2,
            fk_on_delete) in foreign_keys:
        fk_constraints.append(
            "FOREIGN KEY ({field1}) references {schema}.{table} ({field2}) match simple on update no action on delete {ondel}".format(
                field1=",".join(fk_field1), schema=fk_schema, table=fk_table,
                field2=",".join(fk_field2), ondel=fk_on_delete)
        )
    constraints = ", ".join(fk_constraints)
    fields = "(" + (
    ", ".join(fieldstrings + fk_constraints) if fieldstrings else "") + ")"
    sql_string = "create table {schema}.{table} {fields}".format(
        schema=schema, table=table, fields=fields, constraints=constraints)
    print(fk_constraints)
    session = sessionmaker(bind=engine)()
    try:
        if create_schema:
            session.execute("create schema %s" % schema)

        session.execute(sql_string.replace('%', '%%'))
        #create_meta(schema, table)
    except Exception as e:
        traceback.print_exc()
        session.rollback()
        raise e
    else:
        session.commit()
    return {'success': True}

def data_delete(request, context=None):
    raise NotImplementedError()


def data_update(request, context=None):
    engine = _get_engine()
    connection = engine.connect()
    query = {
        'from': [{
            'type': 'table',
            'schema': request['schema'],
            'table': request['table']
        }],
        'where': request['where']
    }
    user = context['user'].name
    rows = data_search(query, context)
    setter = request['values']
    message = request.get('message', None)
    meta_fields = list(parser.set_meta_info('update', user, message).items())
    fields = [field[0] for field in rows['description']] + [f[0] for f in meta_fields]

    table_name = request['table']
    meta = MetaData(bind=engine)
    table = Table(table_name, meta, autoload=True, schema=request['schema'])
    pks = [c for c in table.columns if c.primary_key]

    insert_strings = []
    if rows['data']:
        for row in rows['data']:
            insert = []
            for (key,value) in list(zip(fields, row)) + meta_fields:
                if key in setter:
                    if not (key in pks and value != setter[key]):
                        value = setter[key]
                    else:
                        raise InvalidRequest(
                            "Primary keys must remain unchanged.")
                insert.append(process_value(value))


            insert_strings.append('('+(', '.join(insert))+')')

        # Add metadata for insertions
        schema = request['schema']
        schema = get_meta_schema_name(schema) if not schema.startswith('_') else schema

        s = "INSERT INTO {schema}.{table} ({fields}) VALUES {values}".format(
            schema=read_pgid(schema),
            table=read_pgid(get_edit_table_name(table_name)),
            fields=', '.join(fields),
            values=', '.join(insert_strings)
        )
        print(s)
        connection.execute(s)
    return {'affected':len(rows['data'])}

def data_insert(request, context=None):
    print("INSERT: ", request)
    engine = _get_engine()
    connection = engine.connect()
    query = request

    # If the insert request is not for a meta table, change the request to do so
    assert not query['table'].startswith('_') or query['table'].endswith('_cor'), "Insertions on meta tables are only allowed on comment tables"
    query['table'] = '_' + query['table'] + '_insert'
    if not query['schema'].startswith('_'):
        query['schema'] = '_' + query['schema']

    query = parser.parse_insert(request, engine, context)
    print(query, query.__dict__)
    result = connection.execute(query)
    connection.close()
    description = result.context.cursor.description
    if not result.returns_rows:
        return {}

    data = [list(r) for r in result]
    return {'data': data,
            'description': [[col.name, col.type_code, col.display_size,
                             col.internal_size, col.precision, col.scale,
                             col.null_ok] for col in description]}

def process_value(val):
    if isinstance(val,str):
        return "'" + val + "'"
    if isinstance(val, datetime):
        return "'" + str(val) + "'"
    if val is None:
        return 'null'
    else:
        return str(val)

def table_drop(request, context=None):
    db = request["db"]
    engine = _get_engine()
    connection = engine.connect()

    # load schema name and check for sanity    
    schema = request.pop("schema", "public")
    if not is_pg_qual(schema):
        return {'success':False, 'reason':'Invalid schema name: %s'%schema}
        # Check whether schema exists

    # load table name and check for sanity
    table = request.pop("table", None)

    if not is_pg_qual(table):
        return {'success': False, 'reason': 'Invalid table name: %s' % table}

    try:
        exists = bool(request.pop("exists", False))
    except:
        return {'success': False,
                'reason': 'Invalid exists clause: %s' % exists}

    option = request.pop("option", None)
    if option and option.lower() not in ["cascade", "restrict"]:
        return {'success': False, 'reason': 'Invalid option clause name: %s' % option}

    sql_string = "drop table {exists} {schema}.{table} {option} ".format(
        schema=schema,
        table=table,
        option=option if option else "",
        exists="IF EXISTS" if exists else "")

    session = sessionmaker(bind=engine)()
    try:
        session.execute(sql_string.replace('%', '%%'))
    except Exception as e:
        traceback.print_exc()
        session.rollback()
        raise e
    else:
        session.commit()

    return {}

def data_search(request, context=None):
    engine = _get_engine()
    connection = engine.connect()
    query = parser.parse_select(request)
    print(query)
    result = connection.execute(query)
    description = result.context.cursor.description
    data = [list(r) for r in result]
    return {'data': data,
            'description': [[col.name, col.type_code, col.display_size,
                             col.internal_size, col.precision, col.scale,
                             col.null_ok] for col in description]}


def _get_count(q):
    count_q = q.statement.with_only_columns([func.count()]).order_by(None)
    count = q.session.execute(count_q).scalar()
    return count


def count_all(request, context=None):
    table = request['table']
    schema = request['schema']
    engine = _get_engine()
    session = sessionmaker(bind=engine)()
    t = _get_table(schema, table)
    return session.query(t).count()#_get_count(session.query(t))

def _get_header(results):
    header = []
    for field in results.cursor.description:
        header.append({
            'id': field[0],#.decode('utf-8'),
            'type': field[1]
        })
    return header


def analyze_columns(db, schema, table):
    engine = _get_engine()
    connection = engine.connect()
    result = connection.execute(
        "select column_name as id, data_type as type from information_schema.columns where table_name = '{table}' and table_schema='{schema}';".format(
            schema=schema, table=table))
    return [{'id':r['id'],'type':r['type']} for r in result]

def quote(x):
    if not x.startwith('"') and '(' not in x:
        return '"' + x + '"'
    else:
        return x

def search(db, schema, table, fields=None, pk = None, offset = 0, limit = 100):

    if not fields:
        fields = '*'
    else:
        fields = ', '.join(map(quote(fields)))
    engine = _get_engine()
    connection = engine.connect()
    refs = connection.execute(references.Entry.__table__.select())

    sql_string = "select {fields} from {schema}.{table}".format(
        schema=schema, table=table, fields=fields)

    if pk:
         sql_string += " where {} = {}".format(pk[0],pk[1])

    sql_string += " limit {}".format(limit)
    sql_string += " offset {}".format(offset)
    return connection.execute(sql_string, ), [dict(refs.first()).items()]


def clear_dict(d):
    return {
    k.replace(" ", "_"): d[k] if not isinstance(d[k], dict) else clear_dict(
        d[k]) for k in d}

def create_meta(schema, table):

    meta_schema = get_meta_schema_name(schema)

    if not has_schema({'schema': '_'+schema}):
        create_meta_schema(schema)

    # Comment table
    if not has_table(
            {'schema': meta_schema,
             'table': get_comment_table_name(table)}):
        create_comment_table(schema, table)

    # Table for updates
    if not has_table(
            {'schema': meta_schema,
             'table': get_edit_table_name(table)}):
        create_edit_table(schema, table)

    # Table for inserts
    if not has_table(
            {'schema': meta_schema,
             'table': get_insert_table_name(table)}):
        create_insert_table(schema, table)

    table = get_comment_table_name(table)
    # Table for updates on comments
    if not has_table(
            {'schema': meta_schema,
             'table': get_edit_table_name(table)}):
        create_edit_table(meta_schema, table, meta_schema=meta_schema)

    # Table for inserts on comments
    if not has_table(
            {'schema': meta_schema,
             'table': get_insert_table_name(table)}):
        create_insert_table(meta_schema, table, meta_schema=meta_schema)



def get_comment_table(db, schema, table):
    engine = _get_engine()
    connection = engine.connect()

    sql_string = "select obj_description('{schema}.{table}'::regclass::oid, 'pg_class');".format(
        schema=schema, table=table)
    res = connection.execute(sql_string)
    if res:
        jsn = res.first().obj_description
        if jsn:
            jsn = jsn.replace('\n','')
        else:
            return {}
        try:
            return json.loads(jsn)
        except ValueError:
            return{'error': 'No json format', 'content': jsn}
    else:
        return {}

"""
def data_insert(request):
    engine = _get_engine()
    # load schema name and check for sanity    
    schema = request["schema"]

    if not is_pg_qual(schema):
        raise parser.ValidationError("Invalid schema name")
        # Check whether schema exists

    # load table name and check for sanity
    table = request.pop("table", None)
    if not is_pg_qual(table):
        raise parser.ValidationError("Invalid table name")

    fields = request.pop("fields", "*")
    if fields != "*" and not all(map(is_pg_qual, fields)):
        raise parser.ValidationError("Invalid field name")
    fieldsstring = "(" + (", ".join(fields)) + ")" if fields != "*" else ""

    if bool(request.pop("default", False)):
        data = " DEFAULT VALUES"
    else:
        data = request.pop("values", [])

    returning = request.pop("returning", '')
    if returning:
        returning = 'returning ' + ', '.join(map(parser.parse_expression, returning))

    connection = engine.connect()

    result = connection.execute(
        "INSERT INTO {schema}.{table} {fields} VALUES{markers} {returning}".format(
            schema=schema, table=table, fields=fieldsstring,
            markers="(" + (",".join("%s" for i in range(len(data[0])))) + ")",
            returning=returning),
        data)
    if returning:
        description = result.context.cursor.description
        data = [list(r) for r in result]
        return {'data': data,
                'description': [[col.name, col.type_code, col.display_size,
                                 col.internal_size, col.precision, col.scale,
                                 col.null_ok] for col in description]}
    else:
        return request
"""

def data_info(request, context=None):
    return request


def connect():
    engine = _get_engine()
    insp = sqla.inspect(engine)
    return insp

def _get_engine():
    engine = sqla.create_engine(
        'postgresql://{0}:{1}@{2}:{3}/{4}'.format(
            sec.dbuser,
            sec.dbpasswd,
            sec.dbhost,
            sec.dbport,
            sec.dbname))
    return engine


def has_schema(request, context=None):
    engine = _get_engine()
    result = engine.dialect.has_schema(engine.connect(), request['schema'])
    return result


def has_table(request, context=None):
    engine = _get_engine()
    schema= request.pop('schema', None)
    table = request['table']
    result = engine.dialect.has_table(engine.connect(), table,
                                      schema=schema)
    return result


def has_sequence(request, context=None):
    engine = _get_engine()
    result = engine.dialect.has_sequence(engine.connect(),
                                         request['sequence_name'],
                                         schema=request.pop('schema', None))
    return result


def has_type(request, context=None):
    engine = _get_engine()
    result = engine.dialect.has_schema(engine.connect(),
                                       request['sequence_name'],
                                       schema=request.pop('schema', None))
    return result



def get_table_oid(request, context=None):
    engine = _get_engine()
    result = engine.dialect.get_table_oid(engine.connect(),
                                          request['table'],
                                          schema=request['schema'],
                                          **request)
    return result



def get_schema_names(request, context=None):
    engine = _get_engine()
    result = engine.dialect.get_schema_names(engine.connect(), **request)
    return result



def get_table_names(request, context=None):
    engine = _get_engine()
    result = engine.dialect.get_table_names(engine.connect(),
                                            schema=request.pop('schema',
                                                                 None),
                                            **request)
    return result


def get_view_names(request, context=None):
    engine = _get_engine()
    result = engine.dialect.get_view_names(engine.connect(),
                                           schema=request.pop('schema', None),
                                           **request)
    return result


def get_view_definition(request, context=None):
    engine = _get_engine()
    result = engine.dialect.get_schema_names(engine.connect(),
                                             request['view_name'],
                                             schema=request.pop('schema',
                                                                  None),
                                             **request)
    return result


def get_columns(request, context=None):
    engine = _get_engine()
    result = engine.dialect.get_columns(engine.connect(),
                                        request['table'],
                                        schema=request.pop('schema', None),
                                        **request)
    return result


def get_pk_constraint(request, context=None):
    engine = _get_engine()
    result = engine.dialect.get_pk_constraint(engine.connect(),
                                              request['table'],
                                              schema=request.pop('schema',
                                                                   None),
                                              **request)
    return result


def get_foreign_keys(request, context=None):
    engine = _get_engine()
    result = engine.dialect.get_foreign_keys(engine.connect(),
                                             request['table'],
                                             schema=request.pop('schema',
                                                                  None),
                                             postgresql_ignore_search_path=request.pop(
                                                 'postgresql_ignore_search_path',
                                                 False),
                                             **request)
    return result


def get_indexes(request, context=None):
    engine = _get_engine()
    result = engine.dialect.get_indexes(engine.connect(),
                                        request['table'],
                                        request['schema'],
                                        **request)
    return result



def get_unique_constraints(request, context=None):
    engine = _get_engine()
    result = engine.dialect.get_foreign_keys(engine.connect(),
                                             request['table'],
                                             schema=request.pop('schema',
                                                                  None),
                                             **request)
    return result


def get_comment_table_name(table):
    return '_' + table + '_cor'


def get_edit_table_name(table):
    return '_' + table + '_edit'


def get_insert_table_name(table):
    return '_' + table + '_insert'

def get_meta_schema_name(schema):
    return '_' + schema


def create_meta_schema(schema):
    engine = _get_engine()
    query = 'CREATE SCHEMA {schema}'.format(schema=get_meta_schema_name(schema))
    connection = engine.connect()
    connection.execute(query)


def create_edit_table(schema, table, meta_schema=None):
    if not meta_schema:
        meta_schema = get_meta_schema_name(schema)
    engine = _get_engine()
    query = 'CREATE TABLE {meta_schema}.{edit_table} ' \
            '(LIKE {schema}.{table} INCLUDING ALL EXCLUDING INDEXES, PRIMARY KEY (_id)) ' \
            'INHERITS (_edit_base);'.format(
                meta_schema=meta_schema,
                edit_table=get_edit_table_name(table),
                schema=schema,
                table=table)
    print(query)
    connection = engine.connect()
    connection.execute(query)


def create_insert_table(schema, table, meta_schema=None):
    if not meta_schema:
        meta_schema = get_meta_schema_name(schema)
    engine = _get_engine()
    query = 'CREATE TABLE {meta_schema}.{edit_table} () ' \
            'INHERITS (_insert_base, {schema}.{table});'.format(
                meta_schema=meta_schema,
                edit_table=get_insert_table_name(table),
                schema=schema,
                table=table)
    print(query)
    connection = engine.connect()
    connection.execute(query)


def create_comment_table(schema, table, meta_schema=None):
    if not meta_schema:
        meta_schema = get_meta_schema_name(schema)
    engine = _get_engine()
    query = 'CREATE TABLE {schema}.{table} (PRIMARY KEY (_id)) ' \
            'INHERITS (_comment_base); '.format(
                schema=meta_schema,
                table=get_comment_table_name(table))
    connection = engine.connect()
    connection.execute(query)