import os
import re
from collections import defaultdict

from pathlib import Path

from django.shortcuts import Http404, HttpResponse, redirect, render
from django.views import View
from rdflib import Graph

from oeplatform.settings import (
    ONTOLOGY_ROOT,
    OPEN_ENERGY_ONTOLOGY_NAME,
)


def collect_modules(path):
    modules = dict()

    for file in os.listdir(path):
        if not os.path.isdir(os.path.join(path, file)):
            match = re.match(r"^(?P<filename>.*)\.(?P<extension>\w+)$", file)
            filename, extension = match.groups()
            if filename not in modules:
                modules[filename] = dict(extensions=[], comment="No description found")
            if extension == "owl":
                g = Graph()
                g.parse(os.path.join(path, file))

                # Set the namespaces in the graph
                for prefix, uri in g.namespaces():
                    g.bind(prefix, uri)

                # Extract the description from the RDF graph (rdfs:comment)
                comment_query = f"""
                    SELECT ?description
                    WHERE {{
                        ?ontology rdf:type owl:Ontology .
                        ?ontology rdfs:comment ?description .
                    }}
                """
                # Execute the SPARQL query for comment
                comment_results = g.query(comment_query)

                # Update the comment in the modules dictionary if found
                for row in comment_results:
                    modules[filename]["comment"] = row[0]

                # If the comment is still "No description found," try extracting from dc:description
                if modules[filename]["comment"] == "No description found":
                    description_query = f"""
                        SELECT ?description
                        WHERE {{
                            ?ontology rdf:type owl:Ontology .
                            ?ontology dc:description ?description .
                        }}
                    """
                    # Execute the SPARQL query for description
                    description_results = g.query(
                        description_query
                    )

                    # Update the comment in the modules dictionary if found
                    for row in description_results:
                        modules[filename]["comment"] = row[0]

            modules[filename]["extensions"].append(extension)
    return modules


def read_oeo_context_information(path, file):
    Ontology_URI = path / file
    g = Graph()
    g.parse(Ontology_URI.as_posix())

    q_global = g.query(
        """
        SELECT DISTINCT ?s ?o
        WHERE { ?s rdfs:subClassOf ?o
        filter(!isBlank(?o))
        }
        """
    )

    q_label = g.query(
        """
        SELECT DISTINCT ?s ?o
        WHERE { ?s rdfs:label ?o }
        """
    )

    q_definition = g.query(
        """
        SELECT DISTINCT ?s ?o
        WHERE { ?s obo:IAO_0000115 ?o }
        """
    )

    q_note = g.query(
        """
        SELECT DISTINCT ?s ?o
        WHERE { ?s obo:IAO_0000116 ?o }
        """
    )

    q_main_description = g.query(
        """
        SELECT ?s ?o
        WHERE { ?s dc:description ?o }
        """
    )

    classes_name = {}
    for row in q_label:
        class_name = row.s.split("/")[-1]
        classes_name[class_name] = row.o

    classes_definitions = defaultdict(list)
    for row in q_definition:
        class_name = row.s.split("/")[-1]
        classes_definitions[class_name].append(row.o)

    classes_notes = defaultdict(list)
    for row in q_note:
        class_name = row.s.split("/")[-1]
        classes_notes[class_name].append(row.o)

    ontology_description = ""
    for row in q_main_description:
        if row.s.split("/")[-1] == "":
            ontology_description = row.o

    result = {
        "q_global": q_global,
        "classes_name": classes_name,
        "classes_definitions": dict(classes_definitions),
        "classes_notes": dict(classes_notes),
        "ontology_description": ontology_description,
    }

    return result


def get_ontology_version(path, version=None):
    if not path.exists():
        raise Http404

    versions = os.listdir(path)
    if not version:
        version = max(
            (d for d in versions), key=lambda d: [int(x) for x in d.split(".")]
        )

    return version


def get_common_data(ontology, version=None, path=None):
    onto_base_path = Path(ONTOLOGY_ROOT, ontology)

    version = get_ontology_version(onto_base_path, version=version)
    file = "oeo-full.owl"

    path = onto_base_path / version
    oeo_context_data = read_oeo_context_information(path=path, file=file)

    return {
        "ontology": ontology,
        "version": version,
        "path": path,
        "oeo_context_data": oeo_context_data,
    }


class OntologyVersion(View):
    def get(self, request, ontology="oeo", version=None):
        onto_base_path = Path(ONTOLOGY_ROOT, ontology)

        if not onto_base_path.exists():
            print("test")
            raise Http404
        versions = os.listdir(onto_base_path)
        print(versions)
        if not version:
            version = max(
                (d for d in versions), key=lambda d: [int(x) for x in d.split(".")]
            )
        return render(
            request,
            "ontology/about.html",
            dict(
                version=version,
            ),
        )


class PartialOntologyOverviewContent(View):
    def get(self, request):
        if request.headers.get("HX-Request") == "true":
            if request.method == "GET":
                onto_base_path = Path(ONTOLOGY_ROOT, OPEN_ENERGY_ONTOLOGY_NAME)

                version = get_ontology_version(onto_base_path)
                path = onto_base_path / version
                ontology_data = get_common_data(OPEN_ENERGY_ONTOLOGY_NAME)

                submodules = collect_modules(path / "modules")
                # Collect all file names
                imports = collect_modules(path / "imports")

                partial = render(
                    request,
                    "ontology/partial_ontology_content.html",
                    dict(
                        ontology=OPEN_ENERGY_ONTOLOGY_NAME,
                        version=ontology_data["version"],
                        submodules=submodules.items(),
                        imports=imports.items(),
                        ontology_description=ontology_data["oeo_context_data"][
                            "ontology_description"
                        ],
                    ),
                ).content.decode("utf-8")

                return HttpResponse(partial)


class PartialOntologyOverviewSidebarContent(View):
    def get(self, request):
        onto_base_path = Path(ONTOLOGY_ROOT, OPEN_ENERGY_ONTOLOGY_NAME)

        version = get_ontology_version(onto_base_path)
        path = onto_base_path / version
        main_module = collect_modules(
            path
        )  # TODO fix varname - not clear what path this is
        if OPEN_ENERGY_ONTOLOGY_NAME in main_module.keys():
            main_module_name = OPEN_ENERGY_ONTOLOGY_NAME
        else:
            raise Exception(
                f"The main module '{OPEN_ENERGY_ONTOLOGY_NAME}' is not available in {path}."
            )

        main_module = main_module[main_module_name]
        main_module["name"] = main_module_name
        partial = render(
            request,
            "ontology/partial_ontology_sidebar_content.html",
            dict(
                ontology=OPEN_ENERGY_ONTOLOGY_NAME,
                main_module=main_module,
            ),
        ).content.decode("utf-8")

        return HttpResponse(partial)


def initial_for_pageload(request):
    if request.headers.get("HTTP_HX_REQUEST") == "true":
        if request.method == "GET":
            return render(request, "ontology/initial_response_htmx.html")


class OntologyOverview(View):
    def get(self, request, ontology, module_or_id=None, version=None, imports=False):
        # ignore whatever is in ontology
        ontology = OPEN_ENERGY_ONTOLOGY_NAME
        onto_base_path = Path(ONTOLOGY_ROOT, OPEN_ENERGY_ONTOLOGY_NAME)

        if not onto_base_path.exists():
            raise Http404
        versions = os.listdir(onto_base_path)
        if not version:
            version = max(
                (d for d in versions), key=lambda d: [int(x) for x in d.split(".")]
            )

        path = onto_base_path / version
        # This is temporary (macOS related)
        file = "oeo-full.owl"
        Ontology_URI = path / file
        g = Graph()
        g.parse(Ontology_URI.as_posix())

        q_global = g.query(
            """
            SELECT DISTINCT ?s ?o
            WHERE { ?s rdfs:subClassOf ?o
            filter(!isBlank(?o))
            }
            """
        )

        q_label = g.query(
            """
            SELECT DISTINCT ?s ?o
            WHERE { ?s rdfs:label ?o }
            """
        )

        q_definition = g.query(
            """
            SELECT DISTINCT ?s ?o
            WHERE { ?s obo:IAO_0000115 ?o }
            """
        )

        q_note = g.query(
            """
            SELECT DISTINCT ?s ?o
            WHERE { ?s obo:IAO_0000116 ?o }
            """
        )

        q_main_description = g.query(
            """
            SELECT ?s ?o
            WHERE { ?s dc:description ?o }
            """
        )

        classes_name = {}
        for row in q_label:
            class_name = row.s.split("/")[-1]
            classes_name[class_name] = row.o

        classes_definitions = defaultdict(list)
        for row in q_definition:
            class_name = row.s.split("/")[-1]
            classes_definitions[class_name].append(row.o)

        classes_notes = defaultdict(list)
        for row in q_note:
            class_name = row.s.split("/")[-1]
            classes_notes[class_name].append(row.o)

        ontology_description = ""
        for row in q_main_description:
            if row.s.split("/")[-1] == "":
                ontology_description = row.o

        # Begin prepare data for oeo-viewer. Only need to be executed once per release
        # graphLinks = []
        # graphNodes = []
        #
        # for row in q_global:
        #     source = row.o.split('/')[-1]
        #     target = row.s.split('/')[-1]
        #
        #     #if source in classes_name.keys() and target in classes_name.keys():
        #     graphLinks.append({
        #         "source": source,
        #         "target": target
        #         })
        #
        #     target_found = False
        #     source_found = False
        #
        #     for item in graphNodes:
        #         if item["id"] == target:
        #             target_found = True
        #         if item["id"] == source:
        #             source_found = True
        #
        #     try:
        #         if not target_found:
        #             graphNodes.append({
        #                 "id": target,
        #                 "name": classes_name[target],
        #                 "description": classes_definitions[target],
        #                 "editor_note": classes_notes[target]
        #                 })
        #
        #         if not source_found:
        #             graphNodes.append({
        #                 "id": source,
        #                 "name": classes_name[source],
        #                 "description": classes_definitions[source],
        #                 "editor_note": classes_notes[source]
        #                 })
        #     except:
        #         pass
        #
        # with open('GraphData.json', 'w') as f:
        #     json.dump({"nodes": graphNodes,
        #                 "links": graphLinks}, f)
        # End prepare data for oeo-viewer

        if "text/html" in request.headers.get("accept", "").split(","):
            if module_or_id and "oeo" in module_or_id:
                pass
            else:
                return render(
                    request,
                    "ontology/oeo.html",
                    {"ontology": OPEN_ENERGY_ONTOLOGY_NAME},
                )
        else:
            module_name = None
            if module_or_id:
                if imports:
                    submodules = collect_modules(path / "imports")
                else:
                    submodules = collect_modules(f"{path}/modules")
                # If module_or_id is the name of a valid submodule, use this module
                if module_or_id in submodules:
                    module_name = module_or_id
                if imports:
                    return redirect(f"{path}/imports/{module_name}.owl")  # noqa
                else:
                    return redirect(f"{path}/{module_name}.owl")
            # If no module was requested or the requested id was not a module,
            # serve main ontology
            if module_name is None:
                main_module = collect_modules(path)
                module_name = list(main_module.keys())[0]
            return redirect(
                f"/ontology/{ontology}/releases/{version}/{module_name}.owl"
            )


class OntologyViewClasses(View):
    def get(self, request, ontology, module_or_id=None, version=None, imports=False):
        ontology_data = get_common_data(ontology=OPEN_ENERGY_ONTOLOGY_NAME)

        sub_classes = []
        super_classes = []
        if module_or_id:
            for row in ontology_data["oeo_context_data"]["q_global"]:
                if module_or_id in row.o:
                    sub_class_ID = row.s.split("/")[-1]
                    sub_class_name = ""
                    sub_class_definition = ""
                    sub_class_note = ""
                    if (
                        sub_class_ID
                        in ontology_data["oeo_context_data"]["classes_name"].keys()
                    ):
                        sub_class_name = ontology_data["oeo_context_data"][
                            "classes_name"
                        ][sub_class_ID]
                        if (
                            sub_class_ID
                            in ontology_data["oeo_context_data"][
                                "classes_definitions"
                            ].keys()
                        ):
                            sub_class_definition = ontology_data["oeo_context_data"][
                                "classes_definitions"
                            ][sub_class_ID]
                        if (
                            sub_class_ID
                            in ontology_data["oeo_context_data"]["classes_notes"].keys()
                        ):
                            sub_class_note = ontology_data["oeo_context_data"][
                                "classes_notes"
                            ][sub_class_ID]
                        sub_classes.append(
                            {
                                "URI": row.s,
                                "ID": sub_class_ID,
                                "name": sub_class_name,
                                "definitions": sub_class_definition,
                                "notes": sub_class_note,
                            }
                        )
                if module_or_id in row.s:
                    super_class_ID = row.o.split("/")[-1]
                    super_class_name = ""
                    super_class_definition = ""
                    super_class_note = ""
                    if (
                        super_class_ID
                        in ontology_data["oeo_context_data"]["classes_name"].keys()
                    ):
                        super_class_name = ontology_data["oeo_context_data"][
                            "classes_name"
                        ][super_class_ID]
                        if (
                            super_class_ID
                            in ontology_data["oeo_context_data"][
                                "classes_definitions"
                            ].keys()
                        ):
                            super_class_definition = ontology_data["oeo_context_data"][
                                "classes_definitions"
                            ][super_class_ID]
                        if (
                            super_class_ID
                            in ontology_data["oeo_context_data"]["classes_notes"].keys()
                        ):
                            super_class_note = ontology_data["oeo_context_data"][
                                "classes_notes"
                            ][super_class_ID]
                        super_classes.append(
                            {
                                "URI": row.o,
                                "ID": super_class_ID,
                                "name": super_class_name,
                                "definitions": super_class_definition,
                                "notes": super_class_note,
                            }
                        )

        class_name = ""
        if module_or_id in ontology_data["oeo_context_data"]["classes_name"].keys():
            class_name = ontology_data["oeo_context_data"]["classes_name"][module_or_id]

        class_definitions = ""
        if (
            module_or_id
            in ontology_data["oeo_context_data"]["classes_definitions"].keys()
        ):
            class_definitions = ontology_data["oeo_context_data"][
                "classes_definitions"
            ][module_or_id]

        class_notes = ""
        if module_or_id in ontology_data["oeo_context_data"]["classes_notes"].keys():
            class_notes = ontology_data["oeo_context_data"]["classes_notes"][
                module_or_id
            ]

        return render(
            request,
            "ontology/class.html",
            dict(
                class_id=module_or_id,
                class_name=class_name,
                sub_classes=sub_classes,
                super_classes=super_classes,
                class_definitions=class_definitions,
                class_notes=class_notes,
            ),
        )


class OntologyStatics(View):
    def get(self, request, ontology, file, version=None, extension=None, imports=False):
        """
        Returns the requested file `{file}.{extension}` of version `version`
        of ontology `ontology`

        :param version: default: highest version in folder
        :param extension: default: `.owl`
        :return:
        """

        onto_base_path = Path(ONTOLOGY_ROOT, ontology)

        if not extension:
            extension = "owl"
        if not version:
            version = max(
                (d for d in os.listdir(onto_base_path)),
                key=lambda d: [int(x) for x in d.split(".")],
            )
        if imports:
            file_path = onto_base_path / version / "imports" / f"{file}.{extension}"
        else:
            file_path = onto_base_path / version / f"{file}.{extension}"

        if os.path.exists(file_path):
            with open(file_path, "br") as f:
                response = HttpResponse(
                    f, content_type="application/rdf+xml; charset=utf-8"
                )
                response[
                    "Content-Disposition"
                ] = f'attachment; filename="{file}.{extension}"'
                return response
        else:
            file_path = onto_base_path / version / "modules" / f"{file}.{extension}"
            if not os.path.exists(file_path):
                raise Http404
            with open(file_path, "br") as f:
                response = HttpResponse(
                    f, content_type="application/rdf+xml; charset=utf-8"
                )
                response[
                    "Content-Disposition"
                ] = f'attachment; filename="{file}.{extension}"'
                return response
