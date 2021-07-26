from django.shortcuts import render, HttpResponse, redirect, Http404
from django.views import View
from rdflib import Graph, RDFS, URIRef
from oeplatform.settings import ONTOLOGY_FOLDER
from collections import OrderedDict

import os
import re


def collect_modules(path):
    modules = dict()
    for file in os.listdir(path):
        if not os.path.isdir(os.path.join(path,file)):
            match = re.match("^(?P<filename>.*)\.(?P<extension>\w+)$", file)
            filename, extension = match.groups()
            if filename not in modules:
                modules[filename] = dict(extensions=[], comment="No description found")
            if extension == "owl":
                #g = Graph()
                #g.parse(os.path.join(path, file))
                #root = dict(g.namespaces())['']
                #comments = g.objects(root, RDFS.comment)
                #try:
                #    modules[filename]["comment"] = next(comments)
                #except StopIteration:
                modules[filename]["comment"] = "No description found"
            modules[filename]["extensions"].append(extension)
    return modules



def get_RelationDetails(sub_classes, super_classes, classes_names):

    return sub_classes_detail, super_classes_detail

class OntologyOverview(View):
    def get(self, request, ontology, module_or_id=None, version=None, imports=False):
        if not os.path.exists(f"{ONTOLOGY_FOLDER}/{ontology}"):
            raise Http404
        versions = os.listdir(f"{ONTOLOGY_FOLDER}/{ontology}")
        if not version:
            version = max((d for d in versions), key=lambda d:[int(x) for x in d.split(".")])

        if "text/html" in request.headers.get("accept","").split(","):
            if module_or_id:
                path = f"{ONTOLOGY_FOLDER}/{ontology}/{version}"

                #This should be placed in securitysettings.py
                file = "oeo-full.owl"

                Ontology_URI = os.path.join(path, file)
                g = Graph()
                g.parse(Ontology_URI)

                q_global = g.query("""
                    SELECT DISTINCT ?s ?o
                    WHERE { ?s rdfs:subClassOf ?o }
                    """)

                q_label =  g.query("""
                    SELECT DISTINCT ?s ?o
                    WHERE { ?s rdfs:label ?o }
                    """)

                classes_name = {}
                for row in q_label:
                    class_name = row.s.split('/')[-1]
                    classes_name[class_name] = row.o

                q_definition =  g.query("""
                    SELECT DISTINCT ?s ?o
                    WHERE { ?s obo:IAO_0000115 ?o }
                    """)

                classes_definitions = {}
                for row in q_definition:
                    class_name = row.s.split('/')[-1]
                    classes_definitions[class_name] = row.o

                sub_classes = []
                super_classes = []

                for row in q_global:
                    if (module_or_id in row.o):
                        sub_class_ID = row.s.split('/')[-1]
                        sub_class_name = ''
                        if sub_class_ID in classes_name.keys():
                            sub_class_name = classes_name[sub_class_ID]
                            sub_class_definition = 'No description found'
                            if sub_class_ID in classes_definitions.keys():
                                sub_class_definition = classes_definitions[sub_class_ID]
                            sub_classes.append({ 'URI':row.s, 'ID':sub_class_ID, 'name': sub_class_name, 'definition': sub_class_definition})
                    if (module_or_id in row.s):
                        super_class_ID = row.o.split('/')[-1]
                        super_class_name = ''
                        if super_class_ID in classes_name.keys():
                            super_class_name = classes_name[super_class_ID]
                            super_class_definition = 'No description found'
                            if super_class_ID in classes_definitions.keys():
                                super_class_definition = classes_definitions[super_class_ID]
                            super_classes.append({ 'URI':row.o, 'ID':super_class_ID, 'name': super_class_name , 'definition': super_class_definition})




                q_note =  g.query("""
                    SELECT DISTINCT ?s ?o
                    WHERE { ?s obo:IAO_0000116 ?o }
                    """)


                class_name = ''
                if module_or_id in classes_name.keys():
                    class_name = classes_name[module_or_id]

                class_definition = ''
                if module_or_id in classes_definitions.keys():
                    class_definition = classes_definitions[module_or_id]

                return render(request, "ontology/class.html", dict(
                    class_id = module_or_id,
                    class_name = class_name,
                    sub_classes = sub_classes,
                    super_classes = super_classes,
                    class_definition = class_definition,
                ))
            else:
                main_module = collect_modules(f"{ONTOLOGY_FOLDER}/{ontology}/{version}")
                main_module_name = list(main_module.keys())[0]
                main_module = main_module[main_module_name]
                main_module["name"] = main_module_name
                submodules = collect_modules(f"{ONTOLOGY_FOLDER}/{ontology}/{version}/modules")
                # Collect all file names
                imports = collect_modules(f"{ONTOLOGY_FOLDER}/{ontology}/{version}/imports")

                return render(request, "ontology/oeo.html", dict(
                    ontology=ontology,
                    version=version,
                    main_module=main_module,
                    submodules=submodules.items(),
                    imports=imports.items()
            ))
        else:
            module_name = None
            if module_or_id:
                if imports:
                    submodules = collect_modules(f"{ONTOLOGY_FOLDER}/{ontology}/{version}/imports")
                else:
                    submodules = collect_modules(f"{ONTOLOGY_FOLDER}/{ontology}/{version}/modules")
                # If module_or_id is the name of a valid submodule, use this module
                if module_or_id in submodules:
                    module_name = module_or_id
                if imports:
                    return redirect(f"/ontology/{ontology}/releases/{version}/imports/{module_name}.owl")
                else:
                    return redirect(f"/ontology/{ontology}/releases/{version}/{module_name}.owl")
            # If no module was requested or the requested id was not a module, serve main ontology
            if module_name is None:
                main_module = collect_modules(f"{ONTOLOGY_FOLDER}/{ontology}/{version}")
                module_name = list(main_module.keys())[0]
            return redirect(f"/ontology/{ontology}/releases/{version}/{module_name}.owl")


class OntologyStatics(View):
    def get(self, request, ontology, file, version=None, extension=None, imports=False):
        """
        Returns the requested file `{file}.{extension}` of version `version`
        of ontology `ontology`

        :param version: default: highest version in folder
        :param extension: default: `.owl`
        :return:
        """

        if not extension:
            extension = "owl"
        if not version:
            version = max((d for d in os.listdir(f"{ONTOLOGY_FOLDER}/{ontology}")), key=lambda d:[int(x) for x in d.split(".")])
        if imports:
            file_path = f"{ONTOLOGY_FOLDER}/{ontology}/{version}/imports/{file}.{extension}"
        else:
            file_path = f"{ONTOLOGY_FOLDER}/{ontology}/{version}/{file}.{extension}"
        if os.path.exists(file_path):
            with open(file_path, "br") as f:
                response = HttpResponse(f, content_type="application/rdf+xml; charset=utf-8")
                response["Content-Disposition"] = f'attachment; filename="{file}.{extension}"'
                return response
        else:
            file_path = f"{ONTOLOGY_FOLDER}/{ontology}/{version}/modules/{file}.{extension}"
            if not os.path.exists(file_path):
                raise Http404
            with open(file_path, "br") as f:
                response = HttpResponse(f, content_type="application/rdf+xml; charset=utf-8")
                response["Content-Disposition"] = f'attachment; filename="{file}.{extension}"'
                return response
