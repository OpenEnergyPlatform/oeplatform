"""Contains functions to interact with the postgres oedb"""

import sqlalchemy as sqla
from api import DEFAULT_SCHEMA

try:
    import oeplatform.securitysettings as sec
except:
    import logging
    logging.error("No securitysettings found. Triggerd in api/connection.py")

def get_connection_string():
    return "postgresql://{0}:{1}@{2}:{3}/{4}".format(
        sec.dbuser, sec.dbpasswd, sec.dbhost, sec.dbport, sec.dbname
    )


__ENGINE = sqla.create_engine(
    get_connection_string(), pool_size=0, pool_recycle=600, max_overflow=200
)


def _get_engine():
    return __ENGINE


def table_exists_in_oedb(table, schema=None):
    """check if table exists in oedb

    Args:
        table (str): table name
        schema (str, optional): table schema name

    Returns:
        bool
    """
    engine = _get_engine()
    schema = schema or DEFAULT_SCHEMA
    conn = engine.connect()
    try:
        result = engine.dialect.has_table(conn, table, schema=schema)
    finally:
        conn.close()
    return result