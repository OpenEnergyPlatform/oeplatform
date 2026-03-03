"""
SPDX-FileCopyrightText: 2025 Administrator <admin+git@iks.cs.uni-magdeburg.de>
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.core.management.base import BaseCommand

from dataedit.models import Table
from login.permissions import DELETE_PERM
from oedb.utils import OedbTableProxy, _OedbSchema, _OedbTable
from oeplatform.settings import SCHEMA_DATA

data_schema = _OedbSchema(validated_schema_name=SCHEMA_DATA)
data_meta_schema = data_schema.get_meta_schema()


def delete_django_tables_without_oedb_table() -> bool:
    # get all regular table objects in django
    tables_django = list(Table.objects.filter(is_sandbox=False))
    # get tables in data schema, with permission to potentially delete
    tables_oedb_names = set(data_schema.get_table_names())

    # delete all django table objects if no table in oedb
    # because if no oedb table exists, there is no point
    # in having the django object
    # but first: print and ask

    delete_tables_django = [t for t in tables_django if t.name not in tables_oedb_names]
    delete_tables_django = sorted(delete_tables_django, key=lambda x: x.name)

    if delete_tables_django:
        for table_django in delete_tables_django:
            print(table_django)
        inp = input(
            f"delete the {len(delete_tables_django)} django tables "
            "without corresponding oedb tables listed above? [Y|n]:"
        )
        if inp == "Y":
            for table_django in delete_tables_django:
                print(f"Deleting {table_django}")
                table_django.delete()
            print("---")
        else:
            print("Abort")
            return False
    return True


def create_django_tables_for_orphaned_oedb_table() -> bool:
    # get all regular table objects in django
    tables_django = list(Table.objects.filter(is_sandbox=False))
    tables_django_names = set(t.name for t in tables_django)
    # get tables in data schema, with permission to potentially delete
    tables_oedb_names = set(data_schema.get_table_names())

    add_table_names = [n for n in tables_oedb_names if n not in tables_django_names]
    add_table_names = sorted(add_table_names)

    if add_table_names:
        for name in add_table_names:
            print(name)
        inp = input(
            f"create the {len(add_table_names)} django tables "
            "with orpahend oedb table listed above? [Y|n]:"
        )
        if inp == "Y":
            for name in add_table_names:
                print(f"Creating {name}")
                Table.objects.create(name=name, is_sandbox=False)
            print("---")
        else:
            print("Abort")
            return False

    return True


def delete_artefact_oedb_meta_table() -> bool:
    # find / delete artefact tables in meta schema
    # first find all expected meta tables
    tables_oedb_names = set(data_schema.get_table_names())
    expected_meta_table_names: set[str] = set()
    for name in tables_oedb_names:
        otg = OedbTableProxy(validated_table_name=name, schema_name=SCHEMA_DATA)
        expected_meta_table_names.add(otg._main_table.name)
        expected_meta_table_names.add(otg._edit_table.name)
        expected_meta_table_names.add(otg._insert_table.name)
        expected_meta_table_names.add(otg._delete_table.name)

    meta_table_names = set(data_meta_schema.get_table_names())

    delete_oedb_meta_tables_names = meta_table_names - expected_meta_table_names
    delete_oedb_meta_tables_names = sorted(delete_oedb_meta_tables_names)

    if delete_oedb_meta_tables_names:
        for name in delete_oedb_meta_tables_names:
            print(name)
        inp = input(
            f"delete the {len(delete_oedb_meta_tables_names)} orphaned meta tables "
            "listed above? [Y|n]:"
        )
        if inp == "Y":
            for name in delete_oedb_meta_tables_names:
                print(f"Deleting {name}")
                _OedbTable(
                    validated_table_name=name,
                    validated_schema_name=data_meta_schema._validated_schema_name,
                    permission_level=DELETE_PERM,
                ).drop_if_exists()
            print("---")
        else:
            print("Abort")
            return False

    return True


class Command(BaseCommand):
    def handle(self, *args, **options):
        if not delete_django_tables_without_oedb_table():
            return
        if not create_django_tables_for_orphaned_oedb_table():
            return
        if not delete_artefact_oedb_meta_table():
            return

        print("Finished")
