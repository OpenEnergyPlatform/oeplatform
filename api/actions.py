import re
import sqlalchemy as sqla
import json
import api.references

# debug
import sys
import traceback
import parser
from api.parser import is_pg_qual, read_bool, read_pgid
from sqlalchemy.engine import reflection
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy
from oeplatform.securitysettings import *
pgsql_qualifier = re.compile(r"^[\w\d_\.]+$")
_ENGINES = {}
from api import references
from sqlalchemy.sql.ddl import CreateTable

Base = declarative_base()


class DataStore(Base):
    __tablename__ = 'ckan_datastore'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True,
                           autoincrement=True)
    schema = sqlalchemy.Column(sqlalchemy.String(30))
    table = sqlalchemy.Column(sqlalchemy.String(30))
    resource = sqlalchemy.Column(sqlalchemy.String(40))
    dataset = sqlalchemy.Column(sqlalchemy.String(30))

def get_packages(context):
    return p.toolkit.get_action('package_list')(context, data_dict={})

def schema_create(context, data):
    schema = data['schema']
    resource_dict = p.toolkit.get_action('package_create')(context,
                                                            data_dict={
                                                                "name": schema,
                                                                "type": "data",
                                                                "owner_org": "oedb",
                                                            })
    return resource_dict


def get_table_resource(schema, table):
    result = sqlalchemy.select(DataStore.c.resource, DataStore.c.dataset).where(
        DataStore.c.table == table, DataStore.c.schema == schema)
    if not result:
        return None
    else:
        return result.first()


def comment_table_create(session, schema, table):
    session.execute("create table {schema}{table}_cor (like _comment_base including all) inherits (_comment_base)".format(schema=schema + "." if schema else "", table="_"+table))
    #session.execute("alter table {schema}{table}_cor add primary key using index")


def comment_table_drop(session, schema, table):
    session.execute("drop table {schema}{table}_cor".format(schema=schema + "." if schema else "", table="_"+table))


def table_create(context, data_dict):
    # TODO: Authentication
    # TODO: column constrains: Unique,
    # load schema name and check for sanity 
    db = data_dict["db"]
    if db in ["test"]:
        engine = _get_engine(db)
    connection = engine.connect()

    schema = read_pgid(data_dict["schema"])
    create_schema = not has_schema(context, data_dict)
    # Check whether schema exists

    # load table name and check for sanity
    table = read_pgid(data_dict.pop("table"))
    if len(table) > 100:
        # This is a constraint on CKAN resources
        raise p.toolkit.ValidationError(
            "Length of table name not between 2 and 100")

    # Process fields
    fieldstrings = []
    fields = data_dict.pop("fields", [])
    foreign_keys = []
    primary_keys = []
    for field in fields:
        fname = read_pgid(field["name"])
        type_name = field["type"]

        # TODO: check whether type_name is an actual postgres type
        # if not engine.dialect.has_type(connection,type_name):
        #    raise p.toolkit.ValidationError("Invalid field type: '%s'"% type_name )
        fieldstrings.append(field["name"] + " " + type_name)
        if "pk" in field:
            if read_bool(field["pk"]):
                primary_keys.append([field["name"]])

    table_constraints = {"unique": [], "pk": primary_keys, "fk": foreign_keys}
    for (name, cons) in data_dict.pop('constraints', []):
        if name.lower() == "fk":
            for fk in cons:
                if not all(map(is_pg_qual,
                               [fk["schema"], fk["table"], fk["field"]])):
                    raise p.toolkit.ValidationError("Invalid identifier")
                if fk["on delete"].lower() not in ["cascade", "no action",
                                                   "restrict", "set null",
                                                   "set default"]:
                    raise p.toolkit.ValidationError("Invalid action")
                foreign_keys.append(([field["name"]],
                                     fk["schema"],
                                     fk["table"],
                                     fk["field"],
                                     fk["on delete"]))

    fieldstrings.append("_comment int")


    foreign_keys.append(("_comment", schema, "_"+table+"_cor", "id", "no action"))
    fk_constraints = []
    for (
            fk_field1, fk_schema, fk_table, fk_field2,
            fk_on_delete) in foreign_keys:
        fk_constraints.append(
            "constraint {field1}_{schema}_{table}_{field2}_fk foreign key ({field1}) references {schema}.{table} ({field2}) match simple on update no action on delete {ondel}".format(
                field1=fk_field1, schema=fk_schema, table=fk_table,
                field2=fk_field2, ondel=fk_on_delete)
        )
    constraints = ", ".join(fk_constraints)
    fields = "(" + (
    ", ".join(fieldstrings + fk_constraints) if fieldstrings else "") + ")"
    sql_string = "create table {schema}.{table} {fields} {constraints}".format(
        schema=schema, table=table, fields=fields, constraints="")

    create_dict = {'name': table}
    # resource_dict = p.toolkit.get_action('resource_create')(
    # context, data_dict['resource'])

    # TODO: Add author/maintainer, tags, license

    resource_dict = None
    session = sessionmaker(bind=engine)()
    try:
        if create_schema:
            session.execute("create schema %s" % schema)
        comment_table_create(session, schema, table)
        session.execute(sql_string.replace('%', '%%'))

        resource_dict = p.toolkit.get_action('resource_create')(context,
                                                                data_dict={
                                                                    "package_id": schema.replace(
                                                                        "_",
                                                                        "-"),
                                                                    "url": "/data/{db}/{schema}/{table}".format(
                                                                        schema=schema,
                                                                        table=table,
                                                                        db=db),
                                                                    "name": table,
                                                                    "owner_org": "oedb",
                                                                    })

        ds = DataStore(schema=schema, table=table, dataset=schema,
                       resource=resource_dict['id'])
        session.add(ds)

    except Exception as e:
        traceback.print_exc()
        session.rollback()
        raise e
    else:
        session.commit()
    return {'success': True}

def data_delete(context, data_dict):
    raise NotImplementedError()


def table_drop(context, data_dict):
    db = data_dict["db"]
    if db in ["test"]:
        engine = _get_engine(db)
    connection = engine.connect()

    # load schema name and check for sanity    
    schema = data_dict.pop("schema", None)
    if not is_pg_qual(schema):
        raise p.toolkit.ValidationError("Invalid schema name")
        # Check whether schema exists

    # load table name and check for sanity
    table = data_dict.pop("table", None)

    if not is_pg_qual(table):
        raise p.toolkit.ValidationError("Invalid table name")

    try:
        exists = bool(data_dict.pop("exists", False))
    except:
        raise p.toolkit.ValidationError("Invalid value in field 'exists'")
    option = data_dict.pop("option", None)
    if option and option.lower() not in ["cascade", "restrict"]:
        raise p.toolkit.ValidationError("Invalid value in field 'option'")

    sql_string = "drop table {exists} {schema}.{table} {option} ".format(
        schema=schema,
        table=table,
        option=option if option else "",
        exists="IF EXISTS" if exists else "")

    session = sessionmaker(bind=engine)()
    try:
        resources = session.query(DataStore).filter(DataStore.schema == schema, DataStore.table == table).all()
        for res_item in resources:
            p.toolkit.get_action('resource_delete')(context, data_dict={"package_id": res_item.dataset, "id": res_item.resource})
            session.delete(res_item)
        session.execute(sql_string.replace('%', '%%'))
        comment_table_drop(session, schema, table)
    except Exception as e:
        traceback.print_exc()
        session.rollback()
        raise e
    else:
        session.commit()

    return {}

def data_search(context, data_dict):
    db = data_dict["db"]
    if db in ["test"]:
        engine = _get_engine(db)
    connection = engine.connect()
    query = parser.parse_select(data_dict)
    result = connection.execute(query)
    description = result.context.cursor.description
    data = [list(r) for r in result]
    return {'data': data,
            'description': [[col.name, col.type_code, col.display_size,
                             col.internal_size, col.precision, col.scale,
                             col.null_ok] for col in description]}


def _get_header(results):
    header = []
    for field in results.cursor.description:
        header.append({
            'id': field[0],#.decode('utf-8'),
            'type': field[1]
        })
    return header


def search(db, schema, table, fields=None, pk = None, limit = 100):
    if not fields:
        fields = '*'
    else:
        fields = ', '.join(fields)
    if db in ["test"]:
        engine = _get_engine(db)
    connection = engine.connect()
    refs = connection.execute(references.Entry.__table__.select())

    sql_string = "select {fields} from {schema}.{table}".format(
        schema=schema, table=table, fields=fields)

    if pk:
         sql_string += " where {} = {}".format(pk[0],pk[1])

    sql_string += " limit {}".format(limit)

    return connection.execute(sql_string, ), [dict(refs.first()).items()]


def clear_dict(d):
    return {
    k.replace(" ", "_"): d[k] if not isinstance(d[k], dict) else clear_dict(
        d[k]) for k in d}


def get_comment_table(db, schema, table):
    if db in ["test"]:
        engine = _get_engine(db)
    connection = engine.connect()

    sql_string = "select obj_description('{schema}.{table}'::regclass::oid, 'pg_class');".format(
        schema=schema, table=table)

    res = connection.execute(sql_string)
    return {}
    if res:
        jsn = res.first().obj_description
        return json.loads(jsn)
    else:
        return {}


def data_insert(context, data_dict):
    db = data_dict["db"]
    if db in ["test"]:
        engine = _get_engine(db)
    # load schema name and check for sanity    
    schema = data_dict["schema"]

    if not is_pg_qual(schema):
        raise p.toolkit.ValidationError("Invalid schema name")
        # Check whether schema exists

    # load table name and check for sanity
    table = data_dict.pop("table", None)
    if not is_pg_qual(table):
        raise p.toolkit.ValidationError("Invalid table name")

    fields = data_dict.pop("fields", "*")
    if fields != "*" and not all(map(is_pg_qual, fields)):
        raise p.toolkit.ValidationError("Invalid field name")
    fieldsstring = "(" + (", ".join(fields)) + ")" if fields != "*" else ""

    if bool(data_dict.pop("default", False)):
        data = " DEFAULT VALUES"
    else:
        data = data_dict.pop("values", [])

    returning = data_dict.pop("returning", '')
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
        return data_dict


def data_info(context, data_dict):
    return data_dict


def _get_engine(db):
    '''Get either read or write engine.'''
    engine = _ENGINES.get(db)

    if not engine:
        engine = sqla.create_engine(
            "postgresql://{user}:{passw}@{host}:{port}/{db}".format(
                user=dbuser, passw=dbpasswd, host=dbhost,
                port=dbport, db='test'))
        _ENGINES[db] = engine
    return engine


def has_schema(context, data_dict):
    engine = _get_engine(data_dict['db'])
    result = engine.dialect.has_schema(engine.connect(), data_dict['schema'])
    return result


def has_table(context, data_dict):
    engine = _get_engine(data_dict['db'])
    schema= data_dict.pop('schema', None)
    table = data_dict['table_name']
    result = engine.dialect.has_table(engine.connect(), table,
                                      schema=schema)
    return result


def has_sequence(context, data_dict):
    engine = _get_engine(data_dict['db'])
    result = engine.dialect.has_sequence(engine.connect(),
                                         data_dict['sequence_name'],
                                         schema=data_dict.pop('schema', None))
    return result


def has_type(context, data_dict):
    engine = _get_engine(data_dict['db'])
    result = engine.dialect.has_schema(engine.connect(),
                                       data_dict['sequence_name'],
                                       schema=data_dict.pop('schema', None))
    return result


@reflection.cache
def get_table_oid(context, data_dict):
    engine = _get_engine(data_dict['db'])
    result = engine.dialect.get_table_oid(engine.connect(),
                                          data_dict['table_name'],
                                          schema=data_dict['schema'],
                                          **data_dict)
    return result


@reflection.cache
def get_schema_names(context, data_dict):
    engine = _get_engine(data_dict['db'])
    result = engine.dialect.get_schema_names(engine.connect(), **data_dict)
    return result


@reflection.cache
def get_table_names(context, data_dict):
    engine = _get_engine(data_dict['db'])
    result = engine.dialect.get_table_names(engine.connect(),
                                            schema=data_dict.pop('schema',
                                                                 None),
                                            **data_dict)
    return result


@reflection.cache
def get_view_names(context, data_dict):
    engine = _get_engine(data_dict['db'])
    result = engine.dialect.get_view_names(engine.connect(),
                                           schema=data_dict.pop('schema', None),
                                           **data_dict)
    return result


@reflection.cache
def get_view_definition(context, data_dict):
    engine = _get_engine(data_dict['db'])
    result = engine.dialect.get_schema_names(engine.connect(),
                                             data_dict['view_name'],
                                             schema=data_dict.pop('schema',
                                                                  None),
                                             **data_dict)
    return result


@reflection.cache
def get_columns(context, data_dict):
    engine = _get_engine(data_dict['db'])
    result = engine.dialect.get_columns(engine.connect(),
                                        data_dict['table_name'],
                                        schema=data_dict.pop('schema', None),
                                        **data_dict)
    return result


@reflection.cache
def get_pk_constraint(context, data_dict):
    engine = _get_engine(data_dict['db'])
    result = engine.dialect.get_pk_constraint(engine.connect(),
                                              data_dict['table_name'],
                                              schema=data_dict.pop('schema',
                                                                   None),
                                              **data_dict)
    return result


@reflection.cache
def get_foreign_keys(context, data_dict):
    engine = _get_engine(data_dict['db'])
    result = engine.dialect.get_foreign_keys(engine.connect(),
                                             data_dict['table_name'],
                                             schema=data_dict.pop('schema',
                                                                  None),
                                             postgresql_ignore_search_path=data_dict.pop(
                                                 'postgresql_ignore_search_path',
                                                 False),
                                             **data_dict)
    return result


@reflection.cache
def get_indexes(context, data_dict):
    engine = _get_engine(data_dict['db'])
    result = engine.dialect.get_indexes(engine.connect(),
                                        data_dict['table_name'],
                                        data_dict['schema'],
                                        **data_dict)
    return result


@reflection.cache
def get_unique_constraints(context, data_dict):
    engine = _get_engine(data_dict['db'])
    result = engine.dialect.get_foreign_keys(engine.connect(),
                                             data_dict['table_name'],
                                             schema=data_dict.pop('schema',
                                                                  None),
                                             **data_dict)
    return result
