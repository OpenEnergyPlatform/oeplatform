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


def delete_sandbox_django_tables(interactive: bool = True) -> bool:
    tables = get_sandbox_tables_django()

    if not tables:
        # nohing to do
        return True

    if interactive:
        for table in tables:
            print(table)

        if input(f"Delete {len(tables)} tables from {schema} [Y|n]: ") != "Y":
            print("Abort")
            return False
    # actually deleting
    for table in tables:
        if interactive:
            print(f"Deleting {table}")
        table.delete()

    return True


def delete_sandbox_artefact_tables(interactive: bool = True) -> bool:
    # now schema should be empty:
    oedb_meta_tables = get_sandbox_meta_tables_oedb()
    oedb_tables = get_sandbox_tables_oedb()
    leftover_oedb_tables = oedb_meta_tables + oedb_tables

    if not leftover_oedb_tables:
        # nohing to do
        return True

    if interactive:
        for oedb_table in leftover_oedb_tables:
            print(oedb_table)

        if (
            input(
                f"Delete {len(leftover_oedb_tables)} tables from {meta_schema} [Y|n]: "
            )
            != "Y"
        ):
            print("Abort")
            return False

    # actually deleting
    for oedb_table in leftover_oedb_tables:
        if interactive:
            print(f"Deleting {oedb_table}")
        oedb_table.drop_if_exists()

    return True


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

    if not delete_sandbox_django_tables(interactive=interactive):
        return
    if not delete_sandbox_artefact_tables(interactive=interactive):
        return

    print("Finished")


class Command(BaseCommand):
    def handle(self, *args, **options):
        clear_sandbox(interactive=True)
