"""
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import argparse

from alembic.config import main
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "run alembic command, "
        "e.g. alembic upgrade head, or alembic revision --autogenerate"
    )

    def add_arguments(self, parser):
        # collect all commandline args and pass to alembic
        parser.add_argument("argv", nargs=argparse.REMAINDER)

    def handle(self, *args, **options):
        main(argv=options["argv"])
