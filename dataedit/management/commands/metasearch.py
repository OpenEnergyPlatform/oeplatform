"""
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import sqlalchemy as sqla
from django.core.management.base import BaseCommand

from api.actions import update_meta_search
from api.connection import _get_engine
from oeplatform.securitysettings import SCHEMA_DATA


class Command(BaseCommand):
    def handle(self, *args, **options):
        engine = _get_engine()
        inspector = sqla.inspect(engine)
        for table_name in inspector.get_table_names(schema=SCHEMA_DATA):
            update_meta_search(table=table_name)
