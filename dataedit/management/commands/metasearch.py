# SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
# SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
#
# SPDX-License-Identifier: MIT

import sqlalchemy as sqla
from django.core.management.base import BaseCommand

from api.actions import update_meta_search
from api.connection import _get_engine
from dataedit.views import schema_whitelist


class Command(BaseCommand):
    def handle(self, *args, **options):
        engine = _get_engine()
        inspector = sqla.inspect(engine)
        for schema in schema_whitelist:
            for table_name in inspector.get_table_names(schema=schema):
                update_meta_search(table_name, schema)
