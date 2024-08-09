import logging
import os
from pathlib import Path

from django.http import Http404
from django.shortcuts import HttpResponse, render
from django.views import View

from oeplatform.settings import (
    OEO_EXT_OWL_NAME,
    OEO_EXT_OWL_PATH,
    ONTOLOGY_ROOT,
    OPEN_ENERGY_ONTOLOGY_NAME,
)
from ontology.utils import collect_modules, get_common_data, get_ontology_version

LOGGER = logging.getLogger("oeplatform")

LOGGER.info("Start loading the oeo from local static files.")
OEO_BASE_PATH = Path(ONTOLOGY_ROOT, OPEN_ENERGY_ONTOLOGY_NAME)
OEO_VERSION = get_ontology_version(OEO_BASE_PATH)
OEO_PATH = OEO_BASE_PATH / OEO_VERSION
OEO_MODULES_MAIN = collect_modules(OEO_PATH)
OEO_MODULES_SUBMODULES = collect_modules(OEO_PATH / "modules")
OEO_MODULES_IMPORTS = collect_modules(OEO_PATH / "imports")
OEO_COMMON_DATA = get_common_data(OPEN_ENERGY_ONTOLOGY_NAME)
LOGGER.info(
    "Loading completed! The content form the oeo files is parse into python data types."
)


class OntologyVersion(View):
    def get(self, request, ontology="oeo", version=None):
        onto_base_path = Path(ONTOLOGY_ROOT, ontology)

        if not onto_base_path.exists():
            raise Http404
        versions = os.listdir(onto_base_path)
        LOGGER.info(f"Loaded oeo version {version}")
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
                ontology_data = OEO_COMMON_DATA

                submodules = OEO_MODULES_SUBMODULES

                desired_keys = ["oeo-physical", "oeo-model", "oeo-social", "oeo-sector"]

                relevant_modules = {
                    key: value
                    for key, value in submodules.items()
                    if key in desired_keys
                }

                # Collect all file names
                imports = OEO_MODULES_IMPORTS

                partial = render(
                    request,
                    "ontology/partial_ontology_content.html",
                    dict(
                        ontology=ontology_data["ontology"],
                        version=ontology_data["version"],
                        submodules=relevant_modules.items(),
                        imports=imports.items(),
                        ontology_description=ontology_data["oeo_context_data"][
                            "ontology_description"
                        ],
                    ),
                ).content.decode("utf-8")

                return HttpResponse(partial)


class PartialOntologyOverviewSidebarContent(View):
    def get(self, request):
        version = OEO_VERSION
        main_module = OEO_MODULES_MAIN

        if OPEN_ENERGY_ONTOLOGY_NAME in main_module.keys():
            main_module_name = OPEN_ENERGY_ONTOLOGY_NAME
        else:
            raise Exception(
                f"The main module '{OPEN_ENERGY_ONTOLOGY_NAME}' "
                + "is not available in {path}."
            )

        main_module = main_module[main_module_name]
        main_module["name"] = main_module_name
        partial = render(
            request,
            "ontology/partial_ontology_sidebar_content.html",
            dict(
                ontology=OPEN_ENERGY_ONTOLOGY_NAME,
                version=version,
                main_module=main_module,
            ),
        ).content.decode("utf-8")

        return HttpResponse(partial)


def initial_for_pageload(request):
    if request.headers.get("HTTP_HX_REQUEST") == "true":
        if request.method == "GET":
            return render(request, "ontology/initial_response_htmx.html")


class OntologyOverview(View):
    def get(
        self,
        request,
        ontology=OPEN_ENERGY_ONTOLOGY_NAME,
        module_or_id=None,
        version=None,
        imports=False,
    ):
        onto_base_path = Path(ONTOLOGY_ROOT, OPEN_ENERGY_ONTOLOGY_NAME)

        if not onto_base_path.exists():
            raise Http404
        versions = os.listdir(onto_base_path)
        if not version:
            version = max(
                (d for d in versions), key=lambda d: [int(x) for x in d.split(".")]
            )
        if "text/html" in request.headers.get("accept", "").split(","):
            if module_or_id and "oeo" in module_or_id:
                # Possibly handle specific module or ID-based logic here
                pass
            else:
                return render(
                    request,
                    "ontology/oeo.html",
                    {"ontology": OPEN_ENERGY_ONTOLOGY_NAME, "version": version},
                )
        else:
            # Handling other types of requests or default case
            return HttpResponse("Unsupported media type", status=415)

        # If none of the above conditions are met
        return HttpResponse("Invalid request parameters", status=400)


class OntologyViewClasses(View):
    def get(
        self,
        request,
        ontology=OPEN_ENERGY_ONTOLOGY_NAME,
        module_or_id=None,
        version=None,
        imports=False,
    ):
        ontology_data = OEO_COMMON_DATA
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
                ontology=ontology,
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


class OeoExtendedFileServe(View):
    def __init__(self) -> None:
        self.oeo_ext_static = self.read_owl_file()
        self.file_extension = "owl"
        self.file_name = OEO_EXT_OWL_NAME

    @staticmethod
    def read_owl_file():
        if os.path.exists(OEO_EXT_OWL_PATH):
            with open(OEO_EXT_OWL_PATH, "br") as f:
                return f.read()
        else:
            return None

    def get(self, request):
        if self.oeo_ext_static:
            response = HttpResponse(
                self.oeo_ext_static, content_type="application/rdf+xml; charset=utf-8"
            )
            response[
                "Content-Disposition"
            ] = f'attachment; filename="{self.file_name}.{self.file_extension}"'
        else:
            response = HttpResponse("File not found!", status_code=404)

        return response
