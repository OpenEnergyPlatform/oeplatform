from api.actions import _get_engine


def get_comment_table_name(table):
    return '_' + table + '_cor'


def get_edit_table_name(table):
    return '_' + table + '_edit'


def get_meta_schema_name(schema):
    return '_' + schema


def create_meta_schema(schema):
    engine = _get_engine()
    query = 'CREATE SCHEMA {schema}'.format(schema=get_meta_schema_name(schema))
    connection = engine.connect()
    connection.execute(query)


def create_edit_table(schema, table):
    engine = _get_engine()
    query = 'CREATE TABLE {meta_schema}.{edit_table} ' \
            '(LIKE {schema}.{table}, PRIMARY KEY (_id)) ' \
            'INHERITS (_edit_base); '.format(
                meta_schema=get_meta_schema_name(schema),
                edit_table=get_edit_table_name(table),
                schema=schema,
                table=table)
    connection = engine.connect()
    connection.execute(query)


def create_comment_table(schema, table):
    engine = _get_engine()
    query = 'CREATE TABLE {schema}.{table} (PRIMARY KEY (_id)) ' \
            'INHERITS (_comment_base); '.format(
                schema=get_meta_schema_name(schema),
                table=get_comment_table_name(table))
    connection = engine.connect()
    connection.execute(query)