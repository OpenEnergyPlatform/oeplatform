from django.core.management.base import BaseCommand, CommandError
import os

class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def add_arguments(self, parser):
        parser.add_argument('command', choices=['download', 'update', 'build'])
        parser.add_argument("--update")
        parser.add_argument("--build")

    def handle(self, *args, **options):

        if options["command"] == "download":
            os.system('git pull --recurse-submodules')

        if options["command"] == "update":
            os.system('git submodule update')

        if options["command"] == "build":
            os.system('jupyter nbconvert examples/**/*.ipynb --output-dir=examples/build --to html --template examples/templates/base.tpl')

