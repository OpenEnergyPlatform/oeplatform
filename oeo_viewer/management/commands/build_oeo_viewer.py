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
    help = "build oeo viewer web app in static"

    def handle(self, *args, **options):
        pwd = os.path.join(os.path.dirname(__file__), "..", "..", "client")
        execute(["npm", "install", "--legacy-peer-deps"], cwd=pwd)
        execute(["npm", "run", "build"], cwd=pwd)
