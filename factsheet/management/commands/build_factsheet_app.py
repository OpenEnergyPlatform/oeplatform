# SPDX-FileCopyrightText: 2025 Adel Memariani <memarian@haskell2go.iks.cs.ovgu.de>
# SPDX-FileCopyrightText: 2025 Jonas Huber <jonas.huber@rl-institut.de>
# SPDX-FileCopyrightText: 2025 Christian Winger <Christian Winger@oeko.de>
#
# SPDX-License-Identifier: MIT

import os
import subprocess as sp

from django.core.management.base import BaseCommand


def execute(cmd, cwd):
    """run os command

    Args:
        cmd (list): command and arguments as list
        cwd (str): path to work directory

    """
    proc = sp.run(cmd, cwd=cwd)
    assert proc.returncode == 0


class Command(BaseCommand):
    help = "build factsheet web app in static"

    def handle(self, *args, **options):
        pwd = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
        # execute(["npm", "install", "--legacy-peer-deps", "--no-save"], cwd=pwd)
        execute(["npm", "run", "create"], cwd=pwd)

        print("The factsheet app has been compiled and deployed successfully!")
