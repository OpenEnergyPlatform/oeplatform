"""
SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg

SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import logging
import os
import tempfile
import zipfile
from functools import cache
from pathlib import Path

from django.http import Http404, HttpRequest
from django.shortcuts import HttpResponse, render
from django.views import View

from oeplatform.settings import (  # OEO_EXT_NAME,; OEO_EXT_PATH,
    OEO_EXT_OWL_NAME,
    OEO_EXT_OWL_PATH,
    ONTOLOGY_ROOT,
    OPEN_ENERGY_ONTOLOGY_FULL_OWL_NAME,
    OPEN_ENERGY_ONTOLOGY_NAME,
)
from ontology.utils import collect_modules, get_common_data, get_ontology_version
from ontology.vocabularies import is_file_backed

logger = logging.getLogger("oeplatform")


OEO_BASE_PATH = Path(ONTOLOGY_ROOT, OPEN_ENERGY_ONTOLOGY_NAME)
OEO_VERSION = get_ontology_version(OEO_BASE_PATH)
OEO_PATH = OEO_BASE_PATH / OEO_VERSION


@cache
def get_OEO_MODULES_MAIN() -> dict:
    return collect_modules(OEO_PATH)


@cache
def get_OEO_MODULES_SUBMODULES() -> dict:
    return collect_modules(OEO_PATH / "modules")


@cache
def get_OEO_MODULES_IMPORTS() -> dict:
    return collect_modules(OEO_PATH / "imports")


@cache
def get_OEO_COMMON_DATA() -> dict:
    return get_common_data(OPEN_ENERGY_ONTOLOGY_NAME)


class OntologyAboutView(View):
    def get(self, request, ontology="oeo", version=None):
        onto_base_path = Path(ONTOLOGY_ROOT, ontology)

        if not onto_base_path.exists():
            raise Http404
        versions = os.listdir(onto_base_path)
        logger.info(f"Loaded oeo version {version}")
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


class PartialOntologyAboutContentView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        if request.headers.get("HX-Request") == "true":
            ontology_data = get_OEO_COMMON_DATA()

            submodules = get_OEO_MODULES_SUBMODULES()

            desired_keys = ["oeo-physical", "oeo-model", "oeo-social", "oeo-sector"]

            relevant_modules = {
                key: value for key, value in submodules.items() if key in desired_keys
            }

            # Collect all file names
            imports = get_OEO_MODULES_IMPORTS()

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
        else:
            # TODO: why do we only return response for HTMX?
            return HttpResponse(b"")


class PartialOntologyAboutSidebarContentView(View):
    def get(self, request):
        version = OEO_VERSION
        main_module = get_OEO_MODULES_MAIN()

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


def ontology_react_view(request, ontology=None, term_id=None):
    """
    Serves the React frontend for both the Search listing and the Entity Detail page.

    The actual routing logic (deciding whether to show search results or
    details) is handled client-side by React Router based on the URL.

    The name is checked against the registry first. This route is the catch-all
    under `/ontology/`, so without that check it rendered a working term page
    for any name at all -- which a reader cannot tell from a real one, and
    which is how a scenario bundle came to render as an ontology term.
    """
    if not is_file_backed(ontology):
        raise Http404(f"{ontology!r} is not an ontology served by this platform.")

    context = {
        "ontology_id": ontology,
        "term_id": term_id,
    }
    return render(request, "react/entities.html", context)


class OntologyStaticsView(View):
    def get(
        self,
        request,
        ontology,
        file=None,
        version=None,
        extension=None,
        imports=False,
        glossary=False,
        full=False,
    ):
        """
        Returns the requested file `{file}.{extension}` of version `version`
        of ontology `ontology`

        Note: This function is used in multiple places and therefore quite fragile.
        Due to limited time i will not refactor it but use multiple returns.

        :param version: default: highest version in folder
        :param extension: default: `.owl`
        :return:
        """

        # Two checks, and they answer different questions. The registry says
        # whether we serve this name at all -- a permanent answer, and the one
        # that used to be missing entirely. The directory check says whether
        # this deployment has the files for a name we do serve, which is a
        # deployment fault rather than a client error. Both are 404 to a
        # client, because there is nothing at the address either way; what
        # neither may be is the 500 `os.listdir` raised for both.
        if not is_file_backed(ontology):
            raise Http404(f"{ontology!r} is not an ontology served by this platform.")

        onto_base_path = Path(ONTOLOGY_ROOT, ontology)
        if not onto_base_path.is_dir():
            logger.error(
                "The ontology %r is registered but %s is not on disk.",
                ontology,
                onto_base_path,
            )
            raise Http404(f"The files for {ontology!r} are not available here.")

        if not extension:
            extension = "owl"
        if not version:
            version = max(
                (d for d in os.listdir(onto_base_path)),
                key=lambda d: [int(x) for x in d.split(".")],
            )
        if imports:
            file_path = onto_base_path / version / "imports" / f"{file}.{extension}"
        elif glossary:
            file = "glossary"
            extension = "csv"
            file_path = onto_base_path / version / "glossary" / f"{file}.{extension}"
            if os.path.exists(file_path):
                with open(file_path, "br") as f:
                    response = HttpResponse(
                        f, content_type="application/csv; charset=utf-8"
                    )
                    response["Content-Disposition"] = (
                        f'attachment; filename="{file}.{extension}"'
                    )
                    return response
            else:
                raise Http404
        elif full:
            result_file = f"{ontology}-{version}"
            extension = "zip"
            file_path = onto_base_path / version

            if not os.path.exists(file_path):
                return HttpResponse("Directory not found.", status=404)

            # Create a temporary file to store the zip
            temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
            zip_file_path = temp_zip.name

            try:
                # Create a zip file from the directory
                with zipfile.ZipFile(zip_file_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(file_path):
                        for file in files:
                            _file_path = os.path.join(root, file)
                            arcname = os.path.relpath(_file_path, file_path)
                            zipf.write(_file_path, arcname)

                # Prepare the response
                with open(zip_file_path, "rb") as zip_file:
                    response = HttpResponse(
                        zip_file.read(), content_type="application/zip"
                    )
                    response["Content-Disposition"] = (
                        f'attachment; filename="{result_file}.{extension}"'
                    )
                    response["Content-Length"] = os.path.getsize(zip_file_path)

                    return response

            finally:
                # Clean up the temporary file
                os.remove(zip_file_path)

        else:
            file_path = onto_base_path / version / OPEN_ENERGY_ONTOLOGY_FULL_OWL_NAME

            if file in ["oeo-closure"]:
                file_path = onto_base_path / version / f"{file}.{extension}"

        if os.path.exists(file_path):
            with open(file_path, "br") as f:
                response = HttpResponse(
                    f, content_type="application/rdf+xml; charset=utf-8"
                )

                if not file:
                    file = "oeo-full"

                response["Content-Disposition"] = (
                    f'attachment; filename="{file}.{extension}"'
                )

                return response
        else:
            file_path = onto_base_path / version / "modules" / f"{file}.{extension}"
            if not os.path.exists(file_path):
                raise Http404
            with open(file_path, "br") as f:
                response = HttpResponse(
                    f, content_type="application/rdf+xml; charset=utf-8"
                )
                response["Content-Disposition"] = (
                    f'attachment; filename="{file}.{extension}"'
                )
                return response


class OeoExtendedFileServeView(View):
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
            response["Content-Disposition"] = (
                f'attachment; filename="{self.file_name}.{self.file_extension}"'
            )
        else:
            response = HttpResponse("File not found!", status_code=404)

        return response
