from django.core.management.base import BaseCommand, CommandError
import os
import glob
import re
import json
import uuid

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
            # We need to generate the HTML files from the python notebooks.
            os.system('jupyter nbconvert examples/**/*.ipynb --output-dir=examples/build --to html --template examples/template/openenergyplatform.tpl')
            # We need to parse the titles from the HTML files to be able to show them within the overview.


            # This is no special regex, i just looked at the HTML and figured out how they are generated
            htmlMatchPattern = '<h[12] [^>]*>(.*?)<'

            metaData = []
            for htmlFileName in glob.glob('./examples/build/*.html'):
                with open(os.path.join(os.getcwd(), htmlFileName), 'r') as htmlFile:
                    htmlFileContent = htmlFile.read()
                    matchResults = re.findall(htmlMatchPattern, htmlFileContent, re.MULTILINE)

                    validMatchForFile = None
                    print('fileName=%s,matchResults=%i' % (htmlFileName, len(matchResults)))
                    for matchEntry in matchResults:
                        # If we already found a title, we do not want to find one again.
                        # Actually we should return from this loop but python does not support gotos, I guess.

                        # I also removed some matches, which are generally semantically wrong formatted titles
                        # They are technically no titles, but h1 was used to style them,
                        # which is viewable, but not parseable or readable for screen readers.

                        if not validMatchForFile and not (matchEntry.lower().startswith('openenergy') or matchEntry.lower().startswith('rli')):
                            validMatchForFile = matchEntry
                    print('fileName=%s,generatedTitle=%s' % (htmlFileName, validMatchForFile))
                    shortFileName = htmlFileName.split("/")[-1]
                    metaData.append({
                        'title': validMatchForFile if not None else shortFileName,
                        'id': str(uuid.uuid4()),
                        'fileName': shortFileName
                    })

            with open(os.path.join(os.getcwd(), './examples/build/meta.json'), 'w') as jsonFile:
                json.dump(metaData, jsonFile, ensure_ascii=False, indent=4)