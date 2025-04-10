# SPDX-FileCopyrightText: 2025 Christian Winger <c@wingechr.de>
# SPDX-FileCopyrightText: 2025 Johann Wagner <johann@wagnerdevelopment.de>
# SPDX-FileCopyrightText: 2025 Jonas Huber <jonas.huber@rl-institut.de>
#
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
