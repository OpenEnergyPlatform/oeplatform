# SPDX-FileCopyrightText: 2025 Administrator <admin+git@iks.cs.uni-magdeburg.de>
# SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
# SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
# SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import sqlalchemy as sqla
from django.core.management.base import BaseCommand

from api.connection import _get_engine
from dataedit.models import Table


class Command(BaseCommand):
    def handle(self, *args, **options):
        engine = _get_engine()
        inspector = sqla.inspect(engine)
        real_tables = set(inspector.get_table_names(schema="dataset"))
        table_objects = {t.name for t in Table.objects.filter(is_sandbox=False)}

        # delete all django table objects if no table in oedb

        delete_tables = list(table_objects.difference(real_tables))
        for table_name in delete_tables:
            print(table_name)

        if delete_tables:
            inp = input("delete the table objects listed above? [Y|n]:")
            if inp == "Y":
                for table_name in delete_tables:
                    print(table_name)
                    Table.objects.get(name=table_name).delete()

        print("---")
        # create django table objects if table in oedb and not in django
        for table_name in real_tables.difference(table_objects):
            print(table_name)
            t = Table(name=table_name, is_sandbox=False)
            t.save()
