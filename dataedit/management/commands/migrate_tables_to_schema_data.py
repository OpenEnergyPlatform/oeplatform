"""
SPDX-FileCopyrightText: 2025 Christian Winger
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import logging

from django.core.management.base import BaseCommand

from api.actions import get_schema_names, get_table_names
from dataedit.models import Table
from oedb.connection import _get_engine
from oedb.utils import MAX_TABLE_NAME_LENGTH
from oeplatform.settings import SCHEMA_DATA, SCHEMA_DEFAULT_TEST_SANDBOX

logger = logging.getLogger("oeplatform")
# copied from dataedit.views, because it may be removed later
schemas_whitelist = {
    "boundaries",
    "climate",
    "demand",
    "economy",
    "emission",
    "environment",
    "grid",
    "model_draft",
    "openstreetmap",
    "policy",
    "reference",
    "scenario",
    "society",
    "supply",
}
schema_sandbox = SCHEMA_DEFAULT_TEST_SANDBOX
schema_dataset = SCHEMA_DATA
schemas_test = {"test"}
schemas_special = {
    "public",
    "openfred",
    "topology",
    "information_schema",
}
schemas_data = schemas_whitelist | schemas_test | {schema_sandbox, schema_dataset}
meta_schemas_data = {"_" + s for s in schemas_data}
schemas_all = schemas_data | meta_schemas_data | schemas_special


def get_schema_tables_oedb() -> set[tuple[str, str]]:
    # get schemas and tables (with user data) in OEDB
    result = set()
    for schema in get_schema_names({}):
        if schema not in schemas_all:
            logger.warning(f"Unexpected schema: {schema}")
            continue
        elif schema.lstrip("_") not in schemas_whitelist:
            continue
        for table_name in get_table_names({"schema": schema}):
            result.add((schema, table_name))
    return result


def get_schema_tables_oep() -> set[tuple[str, str]]:
    # get schemas and tables in OEP
    result = set()
    table_names = set()  # check for duplicates of just the names
    for table in Table.objects.all():
        table_name = table.name
        schema = table.schema.name
        if schema == schema_sandbox:
            continue
        elif schema not in schemas_whitelist:
            raise Exception(
                f"Invald schema: {schema}.{table_name}",
            )
        if table_name in table_names:
            raise Exception(
                f"Duplicate table name: {schema}.{table_name}",
            )
        table_names.add(table_name)

        meta_schema = "_" + schema
        result.add((schema, table_name))
        for action in ["delete", "edit", "insert"]:
            _meta_table_name = f"_{table_name}_{action}"
            meta_table_name = _meta_table_name[:MAX_TABLE_NAME_LENGTH]
            if meta_table_name != _meta_table_name:
                logger.warning(
                    f"table name too long {_meta_table_name} => {meta_table_name}"
                )
            if meta_table_name in table_names:
                # we warn, but will ignore it
                logger.error("duplicate meta table name: %s", meta_table_name)
                continue
            table_names.add(meta_table_name)
            result.add((meta_schema, meta_table_name))

    return result


def get_schema_tables_migration() -> set[tuple[str, str]]:
    schema_tables_oedb = get_schema_tables_oedb()
    schema_tables_oep = get_schema_tables_oep()

    schema_tables_oedb_missing = schema_tables_oep - schema_tables_oedb
    # meta tables can be missing
    schema_tables_oedb_missing = {
        s_t for s_t in schema_tables_oedb_missing if s_t[0][0] != "_"
    }
    if schema_tables_oedb_missing:
        raise Exception(f"Missing tables in oedb: {schema_tables_oedb_missing}")

    schema_tables_oep_missing = schema_tables_oedb - schema_tables_oep
    if schema_tables_oep_missing:
        raise Exception(f"Missing tables in oep: {schema_tables_oep_missing}")

    return schema_tables_oep & schema_tables_oedb


def get_migration_sql() -> str:
    meta_schema_dataset = "_" + schema_dataset

    sql = ""
    sql += f'CREATE SCHEMA IF NOT EXISTS "{schema_dataset}";\n'
    sql += f'CREATE SCHEMA IF NOT EXISTS "{meta_schema_dataset}";\n'

    schema_tables = get_schema_tables_migration()
    if not schema_tables:
        logger.info("No tables to migrate")
    else:
        for schema, table in sorted(schema_tables):
            schema_new = (
                meta_schema_dataset if schema.startswith("_") else schema_dataset
            )
            sql += f'ALTER TABLE "{schema}"."{table}" SET SCHEMA "{schema_new}";\n'

    for schema in schemas_whitelist:
        sql += f'DROP SCHEMA IF EXISTS "{schema}";\n'
        sql += f'DROP SCHEMA IF EXISTS "_{schema}";\n'

    return sql


class Command(BaseCommand):
    help = (
        "checks consistency, then prepares and runs sql script "
        "to migrate data to single schema"
    )

    def handle(self, *args, **options):
        sql = get_migration_sql()
        logger.info("Here is the proposed migration sql code")
        print(sql)  # print so we could pipe it into psql or file

        inp = input("Run the migration script now? [Y|n]:")
        if inp != "Y":
            logger.info("No changes applied")
            return
        else:
            with _get_engine().connect() as con:
                con.execute(sql)
            logger.info("Changes applied successfully!")
