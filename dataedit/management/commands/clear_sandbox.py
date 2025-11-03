"""
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.

SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from typing import List

from django.core.management.base import BaseCommand

from dataedit.models import Table
from login.permissions import DELETE_PERM
from oedb.utils import _OedbSchema, _OedbTable
from oeplatform.settings import SCHEMA_DEFAULT_TEST_SANDBOX

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# IMPORTANT: change this code carefully, you dont want to delete
# your entire productive database by accident
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


schema = _OedbSchema(validated_schema_name=SCHEMA_DEFAULT_TEST_SANDBOX)
meta_schema = schema.get_meta_schema()


def get_sandbox_tables_django() -> List[Table]:
    """
    Returns:
        List[Table]: list of table objects in django db in sandbox schema
    """
    return list(Table.objects.filter(is_sandbox=True).all())


def get_sandbox_tables_oedb() -> List[_OedbTable]:
    """
    Returns:
        List[str]: list of table names in oedb in sandbox schema
    """
    return list(schema.get_oedb_tables(permission_level=DELETE_PERM))


def get_sandbox_meta_tables_oedb() -> List[_OedbTable]:
    """
    Returns:
        List[str]: list of table names in oedb in sandbox meta schema
    """

    return list(meta_schema.get_oedb_tables(permission_level=DELETE_PERM))


def clear_sandbox(interactive: bool = True) -> None:
    """delete all tables from the sandbox schema.

    Maybe we should use the API (not just django objects)
    so all the other actions like deleting the meta tables
    are also performed properly

    For now, we delete tables in oedb and django individually

    !!! DANGER ZONE !!! MAKE SURE YOU KNOW WHAT YOU ARE DOING!


    Args:
        output: if True, print actions

    """

    # 1. Step: collect and display all django table objects
    tables = get_sandbox_tables_django()
    table_count = len(tables)

    if interactive:
        for table in tables:
            print(table)

        if not table_count:
            print("Nothing to do")
        elif input(f"Delete {table_count} tables from {schema} [y|n]: ") != "y":
            print("Abort")
            return
    # actually deleting
    for table in tables:
        table.delete()

    # now schema should be empty:
    oedb_meta_tables = get_sandbox_meta_tables_oedb()
    oedb_tables = get_sandbox_tables_oedb()
    leftover_oedb_tables = oedb_meta_tables + oedb_tables
    table_count = len(leftover_oedb_tables)
    if not table_count:
        return  # all good

    if interactive:
        for oedb_table in leftover_oedb_tables:
            print(oedb_table)
        if (
            input(f"Delete {table_count} artefact tables from {meta_schema} [y|n]: ")
            != "y"
        ):
            print("Abort")
            return
    # actually deleting
    for oedb_table in leftover_oedb_tables:
        oedb_table.drop_if_exists()


class Command(BaseCommand):
    def handle(self, *args, **options):
        clear_sandbox(interactive=True)
