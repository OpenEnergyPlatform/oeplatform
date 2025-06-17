# SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
# SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
#
# SPDX-License-Identifier: MIT

from alembic.config import main
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument("commands", nargs="+")

    def handle(self, *args, **options):
        main(argv=options["commands"])
