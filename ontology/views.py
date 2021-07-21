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

def get_classRelations(aGraph, aClass):
    sub_classes = []
    super_classes = []

    for s, p, o in aGraph.triples((None, RDFS.subClassOf, None)):
        if (aClass in o):
            sub_classes.append(s)
        if (aClass in s):
            super_classes.append(o)

    return sub_classes, super_classes

def get_RelationDetails(sub_classes, super_classes, dictOfNames):
    sub_classes_detail = []
    super_classes_detail = []

    for sub_class in sub_classes:
        sub_class_ID = sub_class.split('/')[-1]
        sub_classes_detail.append({
                            'sub_class_ID': sub_class_ID,
                            'sub_class_URI': sub_class,
                            'sub_class_name': dictOfNames[sub_class_ID]
                        })

    for super_class in super_classes:
        super_class_URI = super_class.split('/')
        if len(super_class_URI) > 1:
            super_class_ID = super_class_URI[-1]
            super_classes_detail.append({
                                'super_class_ID': super_class_ID,
                                'super_class_URI': super_class,
                                'super_class_name': dictOfNames[super_class_ID]
                            })

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

                class_name = ''
                qString = g.query(""" SELECT * {?x ?y ?z} """)

                class_names_dict = {}
                for row in qString:
                    if ('#label' in row.y):
                        class_name = row.x.split('/')[-1]
                        class_names_dict[class_name] = row.z

                sub_classes, super_classes = get_classRelations(g, module_or_id)
                sub_classes_info, super_classes_info = get_RelationDetails(sub_classes, super_classes, class_names_dict)

                return render(request, "ontology/class.html", dict(
                    class_id = module_or_id,
                    class_name = class_names_dict[module_or_id],
                    sub_classes = sub_classes_info,
                    super_classes = super_classes_info,
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
