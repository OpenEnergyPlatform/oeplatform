import os
import subprocess as sp
from rdflib import Graph, RDFS, URIRef
import json
from rdflib.namespace import XSD, Namespace
from collections import defaultdict

from django.core.management.base import BaseCommand
from django.conf import settings
from django.apps import apps

from oeplatform.settings import ONTOLOGY_FOLDER

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
        #execute(["npm", "install", "--legacy-peer-deps", "--no-save"], cwd=pwd)
        execute(["npm", "run", "create"], cwd=pwd)

        print('The factsheet app has been compiled and deployed successfully!')
