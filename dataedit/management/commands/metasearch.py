"""
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.core.management.base import BaseCommand
from sqlalchemy import inspect

from api.actions import update_meta_search
from oedb.connection import _get_engine
from oeplatform.settings import SCHEMA_DATA


class Command(BaseCommand):
    def handle(self, *args, **options):
        engine = _get_engine()
        inspector = inspect(engine)
        for table_name in inspector.get_table_names(schema=SCHEMA_DATA):
            update_meta_search(table=table_name)
