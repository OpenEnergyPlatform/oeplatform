# SPDX-FileCopyrightText: 2025 Administrator <admin+git@iks.cs.uni-magdeburg.de>
# SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
# SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
# SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import sqlalchemy as sqla
from django.core.management.base import BaseCommand

from api.connection import _get_engine
from dataedit.models import Schema, Table
from dataedit.views import schema_whitelist


class Command(BaseCommand):
    def handle(self, *args, **options):
        engine = _get_engine()
        inspector = sqla.inspect(engine)
        real_tables = {
            (schema, table_name)
            for schema in schema_whitelist
            for table_name in inspector.get_table_names(schema=schema)
            if schema in schema_whitelist
        }
        table_objects = {(t.schema.name, t.name) for t in Table.objects.all()}

        # delete all django table objects if no table in oedb

        delete_schema_tables = list(table_objects.difference(real_tables))
        for schema, table in delete_schema_tables:
            print(schema, table)

        if delete_schema_tables:
            inp = input("delete the table objects listed above? [Y|n]:")
            if inp == "Y":
                for schema, table in delete_schema_tables:
                    print(schema, table)
                    Table.objects.get(name=table, schema__name=schema).delete()

        print("---")
        # create django table objects if table in oedb and not in django
        for schema, table in real_tables.difference(table_objects):
            schema = "dataset"
            print(schema, table)
            s = Schema.objects.get(name=schema)
            t = Table(name=table, schema=s)
            t.save()
