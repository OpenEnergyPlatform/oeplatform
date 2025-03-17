# SPDX-FileCopyrightText: 2019 Johann Wagner <johannwagner>
# SPDX-FileCopyrightText: 2022 Christian Winger <wingechr>
# SPDX-FileCopyrightText: 2024 Jonas Huber <jh-RLI> © Reiner Lemoine Institut
# SPDX-FileCopyrightText: oeplatform <https://github.com/OpenEnergyPlatform/oeplatform/>
# SPDX-License-Identifier: MIT

import os

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def add_arguments(self, parser):
        parser.add_argument("command", choices=["download", "update"])

    def handle(self, *args, **options):
        if options["command"] == "download":
            os.system("git pull --recurse-submodules")

        if options["command"] == "update":
            os.system("git submodule update")
