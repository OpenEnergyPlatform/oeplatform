"""
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.

SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from typing import List

from django.core.management.base import BaseCommand
from sqlalchemy import inspect

from dataedit.models import Table
from oedb.connection import _get_engine
from oeplatform.settings import SCHEMA_DEFAULT_TEST_SANDBOX


def get_sandbox_tables_django() -> List[Table]:
    """
    Returns:
        List[Table]: list of table objects in django db in sandbox schema
    """
    return Table.objects.filter(is_sandbox=True).all()


def get_sandbox_table_names_oedb() -> List[str]:
    """
    Returns:
        List[str]: list of table names in oedb in sandbox schema
    """
    engine = _get_engine()
    return inspect(engine).get_table_names(schema=SCHEMA_DEFAULT_TEST_SANDBOX)


def get_sandbox_meta_table_names_oedb() -> List[str]:
    """
    Returns:
        List[str]: list of table names in oedb in sandbox meta schema
    """
    engine = _get_engine()
    return inspect(engine).get_table_names(schema="_" + SCHEMA_DEFAULT_TEST_SANDBOX)


def clear_sandbox(output: bool = False) -> None:
    """delete all tables from the sandbox schema.

    Maybe we should use the API (not just django objects)
    so all the other actions like deleting the meta tables
    are also performed properly

    For now, we delete tables in oedb and django individually

    !!! DANGER ZONE !!! MAKE SURE YOU KNOW WHAT YOU ARE DOING!


    Args:
        output: if True, print actions

    """

    # delete all from oedb
    engine = _get_engine()
    for table_name in get_sandbox_table_names_oedb():
        sql = f'DROP TABLE "{SCHEMA_DEFAULT_TEST_SANDBOX}"."{table_name}" CASCADE;'
        if output:
            print(f"oedb: {sql}")
        engine.execute(sql)

    for table_name in get_sandbox_meta_table_names_oedb():
        sql = f'DROP TABLE "_{SCHEMA_DEFAULT_TEST_SANDBOX}"."{table_name}" CASCADE;'
        if output:
            print(f"oedb: {sql}")
        engine.execute(sql)

    # delete all from django
    for table in get_sandbox_tables_django():
        if output:
            print(f"django: delete {table.name}")
        table.delete()


class Command(BaseCommand):
    def handle(self, *args, **options):
        # ask for confirmation
        answ = input(f"Delete all tables from {SCHEMA_DEFAULT_TEST_SANDBOX} [y|n]: ")
        if not answ == "y":
            print("Abort")
            return

        clear_sandbox(output=True)

        print("Done")
