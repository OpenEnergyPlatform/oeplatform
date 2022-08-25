"""Contains functions to interact with the postgres oedb"""

import sqlalchemy as sqla
from sqlalchemy.orm import sessionmaker

from api import DEFAULT_SCHEMA
from dataedit.models import Schema, Table

try:
    import oeplatform.securitysettings as sec
except Exception:
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
    schema = schema or DEFAULT_SCHEMA
    engine = _get_engine()
    conn = engine.connect()
    try:
        result = engine.dialect.has_table(conn, table, schema=schema)
    finally:
        conn.close()
    return result


def table_exists_in_django(table, schema=None):
    """check if table exists in django

    Args:
        table (str): table name
        schema (str, optional): table schema name

    Returns:
        bool
    """
    schema = schema or DEFAULT_SCHEMA
    schema_obj = Schema.objects.get_or_create(name=schema)[0]
    try:
        Table.objects.get(name=table, schema=schema_obj)
        return True
    except Table.DoesNotExist:
        return False


def create_oedb_session():
    """Return a sqlalchemy session to the oedb

    Should only be created once per user request.
    """
    return sessionmaker(bind=_get_engine())()
