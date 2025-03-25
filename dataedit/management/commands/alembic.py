# SPDX-FileCopyrightText: 2017 Martin Glauer <MGlauer>
# SPDX-FileCopyrightText: 2022 Christian Winger <wingechr>
# SPDX-FileCopyrightText: oeplatform <https://github.com/OpenEnergyPlatform/oeplatform/>
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
