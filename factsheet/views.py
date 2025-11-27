"""
SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Bryan Lancien <https://github.com/bmlancien> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import json
import logging

from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import render
from django.utils.cache import patch_response_headers
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from rdflib import RDF, Graph, Literal, URIRef
from rdflib.compare import graph_diff, to_isomorphic

from factsheet.helper import (
    FUNDING_PROP,
    HAS_PART,
    HAS_URL_OR_IRI,
    INSTITUTION_PROP,
    OEO_FRAMEWORK,
    OEO_MODEL,
    OEO_PUBLICATION,
    OEO_SCENARIO,
    PUB_AUTHOR,
    PUB_DATE,
    PUB_DOI,
    PUB_LINK,
    PUB_UID,
    SCENARIO_DESCRIPTOR,
    SCENARIO_INTERREG,
    SCENARIO_REGION,
    SCENARIO_YEAR,
    SECTOR,
    SECTOR_DIVISION,
    TECHNOLOGY,
    build_sector_dropdowns_from_oeo,
    clean_name,
    get_all_sub_classes,
    get_scenario_type_iri,
    is_owner,
    set_ownership,
)
from factsheet.models import OEKG_Modifications
from factsheet.oekg.connection import oekg, oeo, oeo_owl
from factsheet.oekg.filters import OekgQuery
from factsheet.oekg.namespaces import DC, OBO, OEKG, OEO, RDFS, XSD
from factsheet.permission_decorator import only_if_user_is_owner_of_scenario_bundle
from factsheet.utils import remove_non_printable, serialize_publication_date
from login import models as login_models
from modelview.utils import get_framework_metadata_by_id, get_model_metadata_by_id
from oekg.sparqlQuery import (
    bundle_scenarios_filter,
    list_factsheets_oekg,
    normalize_factsheets_rows,
)

logger = logging.getLogger("oeplatform")


def factsheets_index_view(request, *args, **kwargs):
    return render(request, "factsheet/index.html")


def check_ownership_view(request, bundle_id):
    if bundle_id == "new":
        return JsonResponse({"isOwner": True})

    if not request.user.is_authenticated:
        return JsonResponse({"isOwner": False}, status=401)

    if request.user.is_admin:
        return JsonResponse({"isOwner": True})

    is_owner_flag = is_owner(request.user, bundle_id)
    return JsonResponse({"isOwner": is_owner_flag})


def get_oekg_modifications_view(request, *args, **kwargs):
    histroy = OEKG_Modifications.objects.all()
    histroy_json = serializers.serialize("json", histroy)
    response = JsonResponse(histroy_json, safe=False, content_type="application/json")
    patch_response_headers(response, cache_timeout=1)
    return response


# @login_required
@require_POST
def create_factsheet_view(request, *args, **kwargs):
    """
    Creates a scenario bundle based on user's data. Currently, the minimum requirement
    to create a bundle is the "acronym". The "acronym" must be unique. If the provided
    acronym already exists in the OEKG, then the function returns a "Duplicate error".

    Args:
        request (HttpRequest): The incoming HTTP GET request.
        uid (str): The unique ID for the bundle.
        acronym (str): The acronym for the bundle.
        abstract (str): The abstract for the bundle.
        institution (list of objects): The institutions for the bundle.
        funding_source (list of objects): The funding sources for the bundle.
        contact_person (list of objects): The contact persons for the bundle.
        sector_divisions (list of objects): The sector divisions for the bundle.
        sectors (list of objects): The sectors for the bundle.
        technologies (list of objects): The technologies for the bundle.
        study_keywords (list of strings): The study keywords for the bundle.
        scenarios (list of objects): The scenarios for the bundle.
        models (list of strings): The models for the bundle.
        frameworks (list of strings): The frameworks for the bundle.
        publications (list[object]): A list of n publications related to the bundle
            study_name (str): The study name for the bundle.
            date_of_publication (str): The date of publication for the bundle.
            report_title (str): The report title for the bundle.
            report_doi (str): The report_doi for the bundle.
            place_of_publication (str): The place of publication for the bundle.
            link_to_study_report (str): The link to study for the bundle.
            authors (list of objects): The authors for the bundle.

    Returns:
        "Factsheet saved" if successful, "Duplicate error" if the bundle's
        acronym exists.

    """

    if not request.user.is_authenticated:
        return HttpResponseForbidden("User not authenticated")

    request_body = json.loads(request.body)
    name = request_body["name"]  # noqa
    uid = request_body["uid"]
    acronym = request_body["acronym"]
    study_name = request_body["study_name"]
    abstract = request_body["abstract"]
    institution = request_body["institution"]
    funding_source = request_body["funding_source"]
    contact_person = request_body["contact_person"]
    sector_divisions = request_body["sector_divisions"]
    sectors = request_body["sectors"]
    # expanded_sectors = request_body["expanded_sectors"]  # noqa
    # energy_carriers = request_body['energy_carriers']
    # expanded_energy_carriers = request_body['expanded_energy_carriers']
    # energy_transformation_processes = request_body['energy_transformation_processes']
    # expanded_energy_transformation_processes = request_body['expanded_energy_transformation_processes'] # noqa
    technologies = request_body["technologies"]
    study_keywords = request_body["study_keywords"]
    scenarios = request_body["scenarios"]
    publications = request_body["publications"]
    models = request_body["models"]
    frameworks = request_body["frameworks"]

    Duplicate_study_factsheet = False

    for s, p, o in oekg.triples((None, RDF.type, OEO.OEO_00020227)):
        study_acronym = oekg.value(s, DC.acronym)
        if str(clean_name(acronym)) == str(study_acronym):
            Duplicate_study_factsheet = True

    if Duplicate_study_factsheet == True:  # noqa
        response = JsonResponse(
            "Factsheet exists", safe=False, content_type="application/json"
        )
        patch_response_headers(response, cache_timeout=1)
        return response
    else:
        bundle = Graph()

        study_URI = URIRef("https://openenergyplatform.org/ontology/oekg/" + uid)
        bundle.add((study_URI, RDF.type, OEO.OEO_00020227))

        if acronym != "":
            bundle.add((study_URI, DC.acronym, Literal(remove_non_printable(acronym))))
        if study_name != "":
            bundle.add(
                (
                    study_URI,
                    RDFS.label,
                    Literal(remove_non_printable(study_name)),
                )
            )
        if abstract != "":
            bundle.add(
                (study_URI, DC.abstract, Literal(remove_non_printable(abstract)))
            )

        _publications = json.loads(publications) if publications is not None else []
        for item in _publications:
            publications_URI = URIRef(
                "https://openenergyplatform.org/ontology/oekg/publication/" + item["id"]
            )
            # OEO_00020012
            bundle.add((publications_URI, OEO.OEO_00390095, Literal(item["id"])))
            bundle.add((publications_URI, RDF.type, OEO.OEO_00020012))
            bundle.add((study_URI, OBO.BFO_0000051, publications_URI))
            if item["report_title"] != "":
                bundle.add(
                    (
                        publications_URI,
                        RDFS.label,
                        Literal(remove_non_printable(item["report_title"])),
                    )
                )

            _authors = item["authors"]
            for author in _authors:
                author_URI = URIRef(
                    "https://openenergyplatform.org/ontology/oekg/" + author["iri"]
                )
                bundle.add((author_URI, RDF.type, OEO.OEO_00000064))
                bundle.add((publications_URI, OEO.OEO_00000506, author_URI))

            if item["doi"] != "":
                bundle.add((publications_URI, OEO.OEO_00390098, Literal(item["doi"])))

            if (
                item["date_of_publication"] != "01-01-1900"
                and item["date_of_publication"] != ""
            ):
                bundle.add(
                    (
                        publications_URI,
                        OEO.OEO_00390096,
                        Literal(item["date_of_publication"], datatype=XSD.dateTime),
                    )
                )

            if item["link_to_study_report"] != "":
                bundle.add(
                    (URIRef(item["link_to_study_report"]), RDF.type, OEO.OEO_00000353)
                )
                bundle.add(
                    (
                        publications_URI,
                        OEO.OEO_00390078,
                        URIRef(item["link_to_study_report"]),
                    )
                )

            bundle.add((study_URI, OBO.BFO_0000051, publications_URI))

        _scenarios = json.loads(scenarios) if scenarios is not None else []
        for item in _scenarios:
            if item["acronym"] != "":
                scenario_URI = URIRef(
                    "https://openenergyplatform.org/ontology/oekg/scenario/"
                    + item["id"]
                )
                bundle.add((study_URI, OBO.BFO_0000051, scenario_URI))
                bundle.add(
                    (
                        scenario_URI,
                        DC.acronym,
                        Literal(remove_non_printable(item["acronym"])),
                    )
                )
                if item["name"] != "":
                    bundle.add(
                        (
                            scenario_URI,
                            RDFS.label,
                            Literal(remove_non_printable(item["name"])),
                        )
                    )
                    bundle.add((scenario_URI, RDF.type, OEO.OEO_00000365))
                if item["abstract"] != "":
                    bundle.add(
                        (
                            scenario_URI,
                            DC.abstract,
                            Literal(remove_non_printable(item["abstract"])),
                        )
                    )

                bundle.add((scenario_URI, OEO.OEO_00390095, Literal(item["id"])))

                if "regions" in item:
                    for region in item["regions"]:
                        region_URI = URIRef(region["iri"])
                        scenario_region = URIRef(
                            "https://openenergyplatform.org/ontology/oekg/region/"
                            + region["iri"].rsplit("/", 1)[1]
                        )
                        bundle.add((scenario_region, RDF.type, OEO.OEO_00020032))
                        bundle.add(
                            (scenario_region, RDFS.label, Literal(region["name"]))
                        )
                        bundle.add((scenario_region, OEO.OEO_00390078, region_URI))
                        bundle.add((scenario_URI, OEO.OEO_00020220, scenario_region))

                if "interacting_regions" in item:
                    for interacting_region in item["interacting_regions"]:
                        interacting_region_URI = URIRef(interacting_region["iri"])
                        scenario_interacting_region = URIRef(
                            "https://openenergyplatform.org/ontology/oekg/"
                            + interacting_region["iri"]
                        )

                        bundle.add(
                            (scenario_interacting_region, RDF.type, OEO.OEO_00020036)
                        )
                        bundle.add(
                            (
                                scenario_interacting_region,
                                RDFS.label,
                                Literal(interacting_region["name"]),
                            )
                        )
                        bundle.add(
                            (
                                scenario_interacting_region,
                                OEO.OEO_00390078,
                                interacting_region_URI,
                            )
                        )
                        bundle.add(
                            (
                                scenario_URI,
                                OEO.OEO_00020222,
                                scenario_interacting_region,
                            )
                        )

                if "scenario_years" in item:
                    for scenario_year in item["scenario_years"]:
                        bundle.add(
                            (
                                scenario_URI,
                                OEO.OEO_00020440,
                                Literal(scenario_year["name"], datatype=XSD.dateTime),
                            )
                        )

                if "descriptors" in item:
                    for descriptor in item["descriptors"]:
                        descriptor = URIRef(descriptor["class"])
                        bundle.add((scenario_URI, OEO.OEO_00390073, descriptor))

                # TODO: Jonas Huber: Update to avoid duplicated table name entries
                if "input_datasets" in item:
                    for input_dataset in item["input_datasets"]:
                        # TODO- set in settings
                        input_dataset_URI = URIRef(
                            "https://openenergyplatform.org/ontology/oekg/input_datasets/"  # noqa
                            + input_dataset["key"]
                        )
                        bundle.add((input_dataset_URI, RDF.type, OEO.OEO_00030029))
                        bundle.add(
                            (
                                input_dataset_URI,
                                RDFS.label,
                                Literal(
                                    remove_non_printable(
                                        input_dataset["value"]["label"]
                                    )
                                ),
                            )
                        )
                        bundle.add(
                            (
                                input_dataset_URI,
                                OEO.OEO_00390094,
                                Literal(input_dataset["value"]["url"]),
                            )
                        )
                        bundle.add(
                            (
                                input_dataset_URI,
                                OEKG["has_id"],
                                Literal(input_dataset["idx"]),
                            )
                        )
                        bundle.add(
                            (
                                input_dataset_URI,
                                OEO.OEO_00390095,
                                Literal(input_dataset["key"]),
                            )
                        )
                        bundle.add((scenario_URI, OEO.OEO_00020437, input_dataset_URI))

                # TODO: Jonas Huber: Update to avoid duplicated table name entries
                if "output_datasets" in item:
                    for output_dataset in item["output_datasets"]:
                        output_dataset_URI = URIRef(
                            "https://openenergyplatform.org/ontology/oekg/output_datasets/"  # noqa
                            + output_dataset["key"]
                        )
                        bundle.add((output_dataset_URI, RDF.type, OEO.OEO_00030030))
                        bundle.add(
                            (
                                output_dataset_URI,
                                RDFS.label,
                                Literal(
                                    remove_non_printable(
                                        output_dataset["value"]["label"]
                                    )
                                ),
                            )
                        )
                        bundle.add(
                            (
                                output_dataset_URI,
                                OEO.OEO_00390094,
                                Literal(output_dataset["value"]["url"]),
                            )
                        )
                        bundle.add(
                            (
                                output_dataset_URI,
                                OEKG["has_id"],
                                Literal(output_dataset["idx"]),
                            )
                        )
                        bundle.add(
                            (
                                output_dataset_URI,
                                OEO.OEO_00390095,
                                Literal(output_dataset["key"]),
                            )
                        )
                        bundle.add((scenario_URI, OEO.OEO_00020436, output_dataset_URI))

        institutions = json.loads(institution) if institution is not None else []
        for item in institutions:
            institution_URI = URIRef(
                "https://openenergyplatform.org/ontology/oekg/" + item["iri"]
            )
            bundle.add((study_URI, OEO.OEO_00000510, institution_URI))

        funding_sources = (
            json.loads(funding_source) if funding_source is not None else []
        )
        for item in funding_sources:
            funding_source_URI = URIRef(
                "https://openenergyplatform.org/ontology/oekg/" + item["iri"]
            )
            bundle.add((study_URI, OEO.OEO_00000509, funding_source_URI))
        contact_persons = (
            json.loads(contact_person) if contact_person is not None else []
        )
        for item in contact_persons:
            contact_person_URI = URIRef(
                "https://openenergyplatform.org/ontology/oekg/" + item["iri"]
            )
            bundle.add((study_URI, OEO.OEO_00000508, contact_person_URI))

        _sector_divisions = (
            json.loads(sector_divisions) if sector_divisions is not None else []
        )
        for item in _sector_divisions:
            sector_divisions_URI = URIRef(item["class"])
            bundle.add((study_URI, OEO.OEO_00390079, sector_divisions_URI))

        _sectors = json.loads(sectors) if sectors is not None else []
        for item in _sectors:
            sector_URI = URIRef(item["class"])
            bundle.add((study_URI, OEO.OEO_00020439, sector_URI))

        _technologies = json.loads(technologies) if technologies is not None else []
        for item in _technologies:
            technology_URI = URIRef(item["class"])
            bundle.add((study_URI, OEO.OEO_00020438, technology_URI))

        _models = json.loads(models) if models is not None else []
        for item in _models:
            model_id = item.get("id")
            if item.get("acronym"):
                model_acronym = item.get("acronym")
            else:
                model_acronym = item.get("name")
            model_url = item.get("url")

            if not model_id or not model_acronym or not model_url:
                continue  # Skip this item if any critical field is empty

            model_URI = URIRef(
                "https://openenergyplatform.org/ontology/oekg/models/" + str(model_id)
            )
            bundle.add((model_URI, RDF.type, OEO.OEO_00000277))
            bundle.add(
                (
                    model_URI,
                    RDFS.label,
                    Literal(remove_non_printable(model_acronym)),
                )
            )
            bundle.add(
                (
                    model_URI,
                    OEO.OEO_00390094,
                    Literal(model_url),
                )
            )
            bundle.add((study_URI, OBO.BFO_0000051, model_URI))

        _frameworks = json.loads(frameworks) if frameworks is not None else []
        for item in _frameworks:
            framework_id = item.get("id")
            if item.get("acronym"):
                framework_acronym = item.get("acronym")
            else:
                framework_acronym = item.get("name")
            framework_url = item.get("url")

            if not framework_id or not framework_acronym or not framework_url:
                continue  # Skip this item if any critical field is empty

            framework_URI = URIRef(
                "https://openenergyplatform.org/ontology/oekg/frameworks/"
                + str(framework_id)
            )

            bundle.add((framework_URI, RDF.type, OEO.OEO_00000172))

            if framework_acronym:
                bundle.add(
                    (
                        framework_URI,
                        RDFS.label,
                        Literal(remove_non_printable(framework_acronym)),
                    )
                )

            if framework_url:
                bundle.add(
                    (
                        framework_URI,
                        OEO.OEO_00390094,
                        Literal(framework_url),
                    )
                )

            bundle.add((study_URI, OBO.BFO_0000051, framework_URI))

        _study_keywords = (
            json.loads(study_keywords) if study_keywords is not None else []
        )
        # TODO:  Literal(keyword) should be URiRef
        if _study_keywords != []:
            for keyword in _study_keywords:
                bundle.add((study_URI, OEO.OEO_00390071, Literal(keyword)))

        for s, p, o in bundle.triples((None, None, None)):
            oekg.add((s, p, o))

        response = JsonResponse(
            "Factsheet saved", safe=False, content_type="application/json"
        )
        result = set_ownership(bundle_uid=uid, user=request.user)
        logger.info(result)
        patch_response_headers(response, cache_timeout=1)

        return response


@login_required
@only_if_user_is_owner_of_scenario_bundle
def update_factsheet_view(request, *args, **kwargs):
    """
    Updates a scenario bundle based on user's data.

    Args:
        request (HttpRequest): The incoming HTTP GET request.
        uid (str): The unique ID for the bundle.
        acronym (str): The acronym for the bundle.
        abstract (str): The abstract for the bundle.
        institution (list of objects): The institutions for the bundle.
        funding_source (list of objects): The funding sources for the bundle.
        contact_person (list of objects): The contact persons for the bundle.
        sector_divisions (list of objects): The sector divisions for the bundle.
        sectors (list of objects): The sectors for the bundle.
        technologies (list of objects): The technologies for the bundle.
        study_keywords (list of strings): The study keywords for the bundle.
        scenarios (list of objects): The scenarios for the bundle.
        models (list of strings): The models for the bundle.
        frameworks (list of strings): The frameworks for the bundle.
        publications (list[object]): A list of n publications related to the bundle
            study_name (str): The study name for the bundle.
            date_of_publication (str): The date of publication for the bundle.
            report_title (str): The report title for the bundle.
            report_doi (str): The report_doi for the bundle.
            place_of_publication (str): The place of publication for the bundle.
            link_to_study_report (str): The link to study for the bundle.
            authors (list of objects): The authors for the bundle.
    """
    request_body = json.loads(request.body)
    fsData = request_body["fsData"]
    # id = request_body["id"]  # noqa
    uid = request_body["uid"]
    # name = request_body["name"]  # noqa
    studyName = request_body["study_name"]
    acronym = request_body["acronym"]
    abstract = request_body["abstract"]
    institution = request_body["institution"]
    funding_source = request_body["funding_source"]
    contact_person = request_body["contact_person"]
    sector_divisions = request_body["sector_divisions"]
    sectors = request_body["sectors"]
    # expanded_sectors = request_body["expanded_sectors"]  # noqa
    # energy_carriers = request_body['energy_carriers']
    # expanded_energy_carriers = request_body['expanded_energy_carriers']
    # energy_transformation_processes = request_body['energy_transformation_processes']
    # expanded_energy_transformation_processes = request_body['expanded_energy_transformation_processes'] # noqa
    technologies = request_body["technologies"]
    study_keywords = request_body["study_keywords"]
    scenarios = request_body["scenarios"]
    models = request_body["models"]
    frameworks = request_body["frameworks"]
    publications = request_body["publications"]

    Duplicate_study_factsheet = False

    for s, p, o in oekg.triples((None, RDF.type, OEO.OEO_00020227)):
        study_acronym = oekg.value(s, DC.acronym)
        if str(clean_name(acronym)) == str(study_acronym) and str(
            clean_name(acronym)
        ) != str(fsData["acronym"]):
            Duplicate_study_factsheet = True

    if Duplicate_study_factsheet == True:  # noqa
        response = JsonResponse(
            "Factsheet exists", safe=False, content_type="application/json"
        )
        patch_response_headers(response, cache_timeout=1)
        return response

    if Duplicate_study_factsheet == False:  # noqa
        study_URI = URIRef("https://openenergyplatform.org/ontology/oekg/" + uid)

        old_bundle = Graph()
        for s, p, o in oekg.triples((study_URI, None, None)):
            old_bundle.add((s, p, o))
        for s, p, o in oekg.triples((study_URI, OBO.BFO_0000051, None)):
            for s1, p1, o1 in oekg.triples((o, None, None)):
                old_bundle.add((s1, p1, o1))

        new_bundle = Graph()
        new_bundle.add((study_URI, RDF.type, OEO.OEO_00020227))

        _publications = json.loads(publications) if publications is not None else []
        for item in _publications:
            publications_URI = URIRef(
                "https://openenergyplatform.org/ontology/oekg/publication/" + item["id"]
            )

            new_bundle.add((publications_URI, OEO.OEO_00390095, Literal(item["id"])))
            new_bundle.add((publications_URI, RDF.type, OEO.OEO_00020012))
            new_bundle.add((study_URI, OBO.BFO_0000051, publications_URI))
            if item["report_title"] != "":
                new_bundle.add(
                    (publications_URI, RDFS.label, Literal(item["report_title"]))
                )

            _authors = item["authors"]

            if _authors:
                for author in _authors:
                    if author["name"]:
                        author_URI = URIRef(
                            "https://openenergyplatform.org/ontology/oekg/"
                            + author["iri"]
                        )
                        new_bundle.add((author_URI, RDF.type, OEO.OEO_00000064))
                        new_bundle.add((publications_URI, OEO.OEO_00000506, author_URI))

            if item["doi"] != "":
                new_bundle.add(
                    (publications_URI, OEO.OEO_00390098, Literal(item["doi"]))
                )

            if (
                item["date_of_publication"] != "1900"
                and item["date_of_publication"] != ""
            ):
                new_bundle.add(
                    (
                        publications_URI,
                        OEO.OEO_00390096,
                        Literal(item["date_of_publication"], datatype=XSD.dateTime),
                    )
                )

            if item["link_to_study_report"] != "":
                new_bundle.add(
                    (URIRef(item["link_to_study_report"]), RDF.type, OEO.OEO_00000353)
                )
                new_bundle.add(
                    (
                        publications_URI,
                        OEO.OEO_00390078,
                        URIRef(item["link_to_study_report"]),
                    )
                )

            new_bundle.add((study_URI, OBO.BFO_0000051, publications_URI))

            # remove old date in publication
            # iterate to make sure it can only have unique publication date
            for _s, _p, _o in oekg.triples((publications_URI, OEO.OEO_00390096, None)):
                oekg.remove((_s, _p, _o))

        _scenarios = json.loads(scenarios) if scenarios is not None else []
        for item in _scenarios:
            if item["acronym"] != "":
                scenario_URI = URIRef(
                    "https://openenergyplatform.org/ontology/oekg/scenario/"
                    + item["id"]
                )

                for s, p, o in oekg.triples((scenario_URI, None, None)):
                    oekg.remove((o, p, o))

                new_bundle.add((scenario_URI, OEO.OEO_00390095, Literal(item["id"])))
                new_bundle.add((scenario_URI, RDF.type, OEO.OEO_00000365))
                # TODO Acronmy wird lavbel
                new_bundle.add(
                    (
                        scenario_URI,
                        DC.acronym,
                        Literal(remove_non_printable(item["acronym"])),
                    )
                )
                if item["name"] != "":
                    new_bundle.add(
                        (
                            scenario_URI,
                            RDFS.label,
                            Literal(remove_non_printable(item["name"])),
                        )
                    )
                if item["abstract"] != "" and item["abstract"] != None:  # noqa
                    new_bundle.add(
                        (
                            scenario_URI,
                            DC.abstract,
                            Literal(remove_non_printable(item["abstract"])),
                        )
                    )

                if "regions" in item:
                    for region in item["regions"]:
                        region_URI = URIRef(region["iri"])
                        scenario_region = URIRef(
                            "https://openenergyplatform.org/ontology/oekg/region/"
                            + region["iri"].rsplit("/", 1)[1]
                        )
                        new_bundle.add((scenario_region, RDF.type, OEO.OEO_00020032))
                        new_bundle.add(
                            (
                                scenario_region,
                                RDFS.label,
                                Literal(region["name"]),
                            )
                        )
                        new_bundle.add(
                            (
                                scenario_region,
                                OEO.OEO_00390078,
                                region_URI,
                            )
                        )
                        new_bundle.add(
                            (scenario_URI, OEO.OEO_00020220, scenario_region)
                        )
                        new_bundle.add(
                            (scenario_URI, OEO.OEO_00390078, scenario_region)
                        )

                if "interacting_regions" in item:
                    for interacting_region in item["interacting_regions"]:
                        interacting_region_URI = URIRef(interacting_region["iri"])
                        scenario_interacting_region = URIRef(
                            "https://openenergyplatform.org/ontology/oekg/"
                            + interacting_region["iri"]
                        )

                        new_bundle.add(
                            (scenario_interacting_region, RDF.type, OEO.OEO_00020036)
                        )
                        new_bundle.add(
                            (
                                scenario_interacting_region,
                                RDFS.label,
                                Literal(interacting_region["name"]),
                            )
                        )
                        new_bundle.add(
                            (
                                scenario_interacting_region,
                                OEO.OEO_00390078,
                                interacting_region_URI,
                            )
                        )

                        new_bundle.add(
                            (
                                scenario_URI,
                                OEO.OEO_00020222,
                                scenario_interacting_region,
                            )
                        )
                # TODO Value does not have datatype xsd:dateTime
                if "scenario_years" in item:
                    for scenario_year in item["scenario_years"]:
                        new_bundle.add(
                            (
                                scenario_URI,
                                OEO.OEO_00020440,
                                Literal(scenario_year["name"], datatype=XSD.dateTime),
                            )
                        )

                if "descriptors" in item:
                    for descriptor in item["descriptors"]:
                        descriptor = URIRef(descriptor["class"])
                        new_bundle.add((scenario_URI, OEO.OEO_00390073, descriptor))

                # TODO: Jonas Huber: Update to avoid duplicated table name entries
                # TODO: Predicate is not allowed (closed shape)
                if "input_datasets" in item:
                    for input_dataset in item["input_datasets"]:
                        input_dataset_URI = URIRef(
                            "https://openenergyplatform.org/ontology/oekg/input_datasets/"  # noqa
                            + input_dataset["key"]
                        )

                        for s, p, o in oekg.triples((input_dataset_URI, None, None)):
                            oekg.remove((o, p, o))

                        new_bundle.add((input_dataset_URI, RDF.type, OEO.OEO_00030029))
                        new_bundle.add(
                            (
                                input_dataset_URI,
                                RDFS.label,
                                Literal(input_dataset["value"]["label"]),
                            )
                        )
                        new_bundle.add(
                            (
                                input_dataset_URI,
                                OEO.OEO_00390094,
                                Literal(input_dataset["value"]["url"]),
                            )
                        )
                        new_bundle.add(
                            (
                                input_dataset_URI,
                                OEKG["has_id"],
                                Literal(input_dataset["idx"]),
                            )
                        )
                        new_bundle.add(
                            (
                                input_dataset_URI,
                                OEO.OEO_00390095,
                                Literal(input_dataset["key"]),
                            )
                        )
                        new_bundle.add(
                            (scenario_URI, OEO.OEO_00020437, input_dataset_URI)
                        )

                # TODO: Jonas Huber: Update to avoid duplicated table name entries
                if "output_datasets" in item:
                    for output_dataset in item["output_datasets"]:
                        output_dataset_URI = URIRef(
                            "https://openenergyplatform.org/ontology/oekg/output_datasets/"  # noqa: E501
                            + output_dataset["key"]
                        )
                        new_bundle.add((output_dataset_URI, RDF.type, OEO.OEO_00030030))
                        new_bundle.add(
                            (
                                output_dataset_URI,
                                RDFS.label,
                                Literal(output_dataset["value"]["label"]),
                            )
                        )
                        new_bundle.add(
                            (
                                output_dataset_URI,
                                OEO.OEO_00390094,
                                Literal(output_dataset["value"]["url"]),
                            )
                        )
                        new_bundle.add(
                            (
                                output_dataset_URI,
                                OEKG["has_id"],
                                Literal(output_dataset["idx"]),
                            )
                        )
                        new_bundle.add(
                            (
                                output_dataset_URI,
                                OEO.OEO_00390095,
                                Literal(output_dataset["key"]),
                            )
                        )
                        new_bundle.add(
                            (scenario_URI, OEO.OEO_00020436, output_dataset_URI)
                        )

                new_bundle.add((study_URI, OBO.BFO_0000051, scenario_URI))

        if acronym != "":
            new_bundle.add(
                (study_URI, DC.acronym, Literal(remove_non_printable(acronym)))
            )

        new_bundle.add(
            (study_URI, RDFS.label, Literal(remove_non_printable(studyName)))
        )

        institutions = json.loads(institution) if institution is not None else []
        for item in institutions:
            institution_URI = URIRef(
                "https://openenergyplatform.org/ontology/oekg/" + item["iri"]
            )
            new_bundle.add((study_URI, OEO.OEO_00000510, institution_URI))

        funding_sources = (
            json.loads(funding_source) if funding_source is not None else []
        )
        for item in funding_sources:
            funding_source_URI = URIRef(
                "https://openenergyplatform.org/ontology/oekg/" + item["iri"]
            )
            new_bundle.add((study_URI, OEO.OEO_00000509, funding_source_URI))

        if abstract != "":
            new_bundle.add(
                (study_URI, DC.abstract, Literal(remove_non_printable(abstract)))
            )

        contact_persons = (
            json.loads(contact_person) if contact_person is not None else []
        )
        for item in contact_persons:
            contact_person_URI = URIRef(
                "https://openenergyplatform.org/ontology/oekg/" + item["iri"]
            )
            new_bundle.add((study_URI, OEO.OEO_00000508, contact_person_URI))

        _sector_divisions = (
            json.loads(sector_divisions) if sector_divisions is not None else []
        )
        for item in _sector_divisions:
            sector_divisions_URI = URIRef(item["class"])
            new_bundle.add((study_URI, OEO.OEO_00390079, sector_divisions_URI))

        _sectors = json.loads(sectors) if sectors is not None else []
        for item in _sectors:
            sector_URI = URIRef(item["class"])
            new_bundle.add((study_URI, OEO.OEO_00020439, sector_URI))

        _technologies = json.loads(technologies) if technologies is not None else []
        for item in _technologies:
            technology_URI = URIRef(item["class"])
            new_bundle.add((study_URI, OEO.OEO_00020438, technology_URI))

        _models = json.loads(models) if models is not None else []
        for item in _models:
            model_id = item.get("id")

            if item.get("acronym"):
                model_acronym = item.get("acronym")
            else:
                model_acronym = item.get("name")
            model_url = item.get("url")

            if not model_id or not model_acronym or not model_url:
                continue  # Skip this item if any critical field is empty

            model_URI = URIRef(
                "https://openenergyplatform.org/ontology/oekg/models/" + str(model_id)
            )
            new_bundle.add((model_URI, RDF.type, OEO.OEO_00000277))

            new_bundle.add(
                (
                    model_URI,
                    RDFS.label,
                    Literal(remove_non_printable(model_acronym)),
                )
            )

            new_bundle.add(
                (
                    model_URI,
                    OEO.OEO_00390094,
                    Literal(model_url),
                )
            )

            new_bundle.add((study_URI, OBO.BFO_0000051, model_URI))

            # remove old labels
            # iterate to make sure only current selection is available
            for _s, _p, _o in oekg.triples((model_URI, RDFS.label, None)):
                oekg.remove((_s, _p, _o))

            # remove old iri´s
            # iterate to make sure only current selection is available
            for _s, _p, _o in oekg.triples((model_URI, OEO.OEO_00390094, None)):
                oekg.remove((_s, _p, _o))

        _frameworks = json.loads(frameworks) if frameworks is not None else []
        for item in _frameworks:
            framework_id = item.get("id")
            if item.get("acronym"):
                framework_acronym = item.get("acronym")
            else:
                framework_acronym = item.get("name")
            framework_url = item.get("url")

            if not framework_id or not framework_url:
                continue  # Skip this item if any critical field is empty

            framework_URI = URIRef(
                "https://openenergyplatform.org/ontology/oekg/frameworks/"
                + str(framework_id)
            )

            new_bundle.add((framework_URI, RDF.type, OEO.OEO_00000172))
            if framework_acronym:
                new_bundle.add(
                    (
                        framework_URI,
                        RDFS.label,
                        Literal(remove_non_printable(framework_acronym)),
                    )
                )
            if framework_url:
                new_bundle.add(
                    (
                        framework_URI,
                        OEO.OEO_00390094,
                        Literal(framework_url),
                    )
                )

            new_bundle.add((study_URI, OBO.BFO_0000051, framework_URI))

            # remove old labels
            # iterate to make sure only current selection is available
            for _s, _p, _o in oekg.triples((framework_URI, RDFS.label, None)):
                oekg.remove((_s, _p, _o))

            # remove old iri´s
            # iterate to make sure only current selection is available
            for _s, _p, _o in oekg.triples((framework_URI, OEO.OEO_00390094, None)):
                oekg.remove((_s, _p, _o))

        _study_keywords = (
            json.loads(study_keywords) if study_keywords is not None else []
        )
        for keyword in _study_keywords:
            new_bundle.add((study_URI, OEO.OEO_00390071, URIRef(keyword)))

        iso_old_bundle = to_isomorphic(old_bundle)
        iso_new_bundle = to_isomorphic(new_bundle)

        in_both, in_first, in_second = graph_diff(iso_old_bundle, iso_new_bundle)

        in_first_json = str(in_first.serialize(format="json-ld"))  # noqa
        in_second_json = str(in_second.serialize(format="json-ld"))  # noqa

        # remove old bundle from oekg
        for s, p, o in oekg.triples((study_URI, OBO.BFO_0000051, None)):
            oekg.remove((o, None, None))
        oekg.remove((study_URI, None, None))

        for s, p, o in oekg.triples((study_URI, OBO.BFO_0000051, None)):
            oekg.remove((o, None, None))
        oekg.remove((study_URI, None, None))

        # add updated bundle to oekg
        for s, p, o in new_bundle.triples((None, None, None)):
            oekg.add((s, p, o))

        OEKG_Modifications_instance = OEKG_Modifications(  # noqa
            bundle_id=uid,
            user=login_models.myuser.objects.filter(name=request.user).first(),
            old_state=in_first.serialize(format="json-ld"),
            new_state=in_second.serialize(format="json-ld"),
        )
        OEKG_Modifications_instance.save()

        response = JsonResponse(
            "factsheet updated!", safe=False, content_type="application/json"
        )
        patch_response_headers(response, cache_timeout=1)
        return response


def is_logged_in_view(request, *args, **kwargs):
    user = None
    if request.user.is_authenticated:
        user = True

    output = ""
    if user is None:
        output = "NOT_LOGGED_IN"
    else:
        output = "LOGGED_IN"
    response = JsonResponse(output, safe=False, content_type="application/json")
    patch_response_headers(response, cache_timeout=1)
    return response


def factsheet_by_id_view(request, *args, **kwargs):
    uid = request.GET.get("id")
    study_URI = URIRef("https://openenergyplatform.org/ontology/oekg/" + uid)
    factsheet = {}

    # --- Basic fields ---
    acronym = oekg.value(study_URI, DC.acronym) or Literal("")
    study_name = oekg.value(study_URI, RDFS.label) or Literal("")
    abstract = oekg.value(study_URI, DC.abstract) or Literal("")

    factsheet["acronym"] = acronym
    factsheet["uid"] = uid
    factsheet["study_name"] = study_name
    factsheet["abstract"] = abstract

    # --- Funding / institutions / contacts ---
    factsheet["funding_sources"] = []
    for _, _, o in oekg.triples((study_URI, FUNDING_PROP, None)):
        label = oekg.value(o, RDFS.label)
        if label is not None:
            factsheet["funding_sources"].append(
                {"iri": str(o).split("/")[-1], "id": label, "name": label}
            )

    factsheet["institution"] = []
    for _, _, o in oekg.triples((study_URI, INSTITUTION_PROP, None)):
        label = oekg.value(o, RDFS.label)
        if label is not None:
            factsheet["institution"].append(
                {"iri": str(o).split("/")[-1], "id": label, "name": label}
            )

    factsheet["contact_person"] = []
    for _, _, o in oekg.triples((study_URI, OEO.OEO_00000508, None)):
        label = oekg.value(o, RDFS.label)
        if label is not None:
            factsheet["contact_person"].append(
                {"iri": str(o).split("/")[-1], "id": label, "name": label}
            )

    # --- Sector divisions / sectors / technologies / keywords ---
    factsheet["sector_divisions"] = []
    for _, _, o in oekg.triples((study_URI, SECTOR_DIVISION, None)):
        label = oeo.value(o, RDFS.label)
        if label is not None:
            factsheet["sector_divisions"].append(
                {"value": label, "name": label, "class": o}
            )

    factsheet["sectors"] = []
    for _, _, o in oekg.triples((study_URI, SECTOR, None)):
        label = oeo.value(o, RDFS.label)
        if label is not None:
            factsheet["sectors"].append(
                {"value": label, "label": label, "class": o, "id": o}
            )

    factsheet["technologies"] = []
    for _, _, o in oekg.triples((study_URI, TECHNOLOGY, None)):
        label = oeo.value(o, RDFS.label)
        if label is not None:
            factsheet["technologies"].append(
                {"value": label, "label": label, "class": o, "id": o}
            )

    factsheet["study_keywords"] = []
    for _, _, o in oekg.triples((study_URI, OEO.OEO_00390071, None)):
        if o is not None:
            factsheet["study_keywords"].append(o)

    # --- Models & Frameworks (filter by type!) ---
    factsheet["models"] = []
    factsheet["frameworks"] = []

    # Iterate parts once and branch by rdf:type
    for _, _, part in oekg.triples((study_URI, HAS_PART, None)):
        # Model factsheets
        if (part, RDF.type, OEO_MODEL) in oekg:
            # Numeric id exists at the end of URI in your TTL
            tail = str(part).rstrip("/").split("/")[-1]
            if tail.isdigit():
                model_id = int(tail)
                # URL for the registry entry if present
                url = oekg.value(part, HAS_URL_OR_IRI)
                model_metadata = get_model_metadata_by_id(model_id, "energymodel")
                if model_metadata:
                    if url:
                        model_metadata["url"] = str(url)
                    factsheet["models"].append(model_metadata)
            continue

        # Framework factsheets
        if (part, RDF.type, OEO_FRAMEWORK) in oekg:
            tail = str(part).rstrip("/").split("/")[-1]
            if tail.isdigit():
                framework_id = int(tail)
                url = oekg.value(part, HAS_URL_OR_IRI)
                framework_metadata = get_framework_metadata_by_id(
                    framework_id, "energyframework"
                )
                if framework_metadata:
                    if url:
                        framework_metadata["url"] = str(url)
                    factsheet["frameworks"].append(framework_metadata)
            continue

    # --- Publications (filter by type!) ---
    temp_dates = set()
    factsheet["publications"] = []

    for _, _, part in oekg.triples((study_URI, HAS_PART, None)):
        if (part, RDF.type, OEO_PUBLICATION) not in oekg:
            continue

        publication = {
            "report_title": "",
            "id": None,
            "authors": [],
            "doi": "",
            "date_of_publication": "",
            "link_to_study_report": "",
        }

        label = oekg.value(part, RDFS.label)
        if label is not None:
            publication["report_title"] = label

        pub_uuid = oekg.value(part, PUB_UID)
        publication["id"] = pub_uuid

        for _, _, auth in oekg.triples((part, PUB_AUTHOR, None)):
            auth_label = oekg.value(auth, RDFS.label)
            publication["authors"].append({"iri": auth, "name": auth_label})

        doi = oekg.value(part, PUB_DOI)
        if doi:
            publication["doi"] = doi

        pub_date = oekg.value(part, PUB_DATE)
        if pub_date:
            pretty = serialize_publication_date(str(pub_date))
            publication["date_of_publication"] = pretty
            temp_dates.add(pretty)  # <-- FIX: add, don’t update with string

        link = oekg.value(part, PUB_LINK)
        if link:
            publication["link_to_study_report"] = link

        factsheet["publications"].append(publication)

    # only set after collecting all dates
    factsheet["collected_scenario_publication_dates"] = list(temp_dates)

    # --- Scenarios (filter by type!) ---
    factsheet["scenarios"] = []
    for _, _, part in oekg.triples((study_URI, HAS_PART, None)):
        if (part, RDF.type, OEO_SCENARIO) not in oekg:
            continue

        scenario = {
            "acronym": None,
            "id": None,
            "scenario_years": [],
            "regions": [],
            "interacting_regions": [],
            "descriptors": [],
            "input_datasets": [],
            "output_datasets": [],
            "name": None,
            "abstract": None,
        }

        # prefer dc:acronym, fallback to rdfs:label
        scen_acr = oekg.value(part, DC.acronym)
        if scen_acr is None:
            scen_acr = oekg.value(part, RDFS.label)
        if scen_acr is not None:
            scenario["acronym"] = scen_acr

        scen_uuid = oekg.value(
            part, PUB_UID
        )  # the same uid property is used in your TTL
        scenario["id"] = scen_uuid

        scenario["name"] = oekg.value(part, RDFS.label)
        scenario["abstract"] = oekg.value(part, DC.abstract)

        for _, _, r in oekg.triples((part, SCENARIO_REGION, None)):
            r_label = oekg.value(r, RDFS.label)
            scenario["regions"].append({"iri": r, "name": r_label})

        for _, _, r in oekg.triples((part, SCENARIO_INTERREG, None)):
            r_label = oekg.value(r, RDFS.label)
            scenario["interacting_regions"].append(
                {"iri": str(r).split("/")[-1], "id": r_label, "name": r_label}
            )

        for _, _, desc in oekg.triples((part, SCENARIO_DESCRIPTOR, None)):
            d_label = oeo.value(desc, RDFS.label)
            scenario["descriptors"].append(
                {"value": d_label, "label": d_label, "class": desc}
            )

        # Input datasets
        for _, _, ds in oekg.triples((part, OEO.OEO_00020437, None)):
            ds_url = oekg.value(ds, HAS_URL_OR_IRI)
            ds_lab = oekg.value(ds, RDFS.label)
            ds_key = oekg.value(ds, PUB_UID)
            ds_idx = oekg.value(ds, OEKG["has_id"])
            scenario["input_datasets"].append(
                {
                    "key": ds_key,
                    "idx": ds_idx,
                    "value": {"label": ds_lab, "url": ds_url},
                }
            )

        # Output datasets
        for _, _, ds in oekg.triples((part, OEO.OEO_00020436, None)):
            ds_url = oekg.value(ds, HAS_URL_OR_IRI)
            ds_lab = oekg.value(ds, RDFS.label)
            ds_key = oekg.value(ds, PUB_UID)
            ds_idx = oekg.value(ds, OEKG["has_id"])
            scenario["output_datasets"].append(
                {
                    "key": ds_key,
                    "idx": ds_idx,
                    "value": {"label": ds_lab, "url": ds_url},
                }
            )

        for _, _, year in oekg.triples((part, SCENARIO_YEAR, None)):
            scenario["scenario_years"].append({"id": year, "name": year})

        factsheet["scenarios"].append(scenario)

    # Cache headers, region label fix you had, etc. (unchanged)
    response = JsonResponse(factsheet, safe=False, content_type="application/json")
    patch_response_headers(response, cache_timeout=1)

    # scenario_region = URIRef(
    #     "https://openenergyplatform.org/ontology/oekg/region/Germany"
    # )
    # for s, p, o in oekg.triples((scenario_region, RDFS.label, None)):
    #     if str(o) == "None":
    #         oekg.remove((s, p, o))
    #         oekg.add((s, p, Literal("Germany")))

    return response


@only_if_user_is_owner_of_scenario_bundle
@login_required
def delete_factsheet_by_id_view(request, *args, **kwargs):
    """
    Removes a scenario bundle based on the provided ID.

    Args:
        request (HttpRequest): The incoming HTTP GET request.
        id (str): The unique ID for the bundle.

    """
    id = request.GET.get("id")
    study_URI = URIRef("https://openenergyplatform.org/ontology/oekg/" + id)

    for s, p, o in oekg.triples((study_URI, OBO.BFO_0000051, None)):
        oekg.remove((o, None, None))
    oekg.remove((study_URI, None, None))

    response = JsonResponse(
        "factsheet removed!", safe=False, content_type="application/json"
    )
    patch_response_headers(response, cache_timeout=1)
    return response


def test_query_view(request, *args, **kwargs):
    scenario_region = URIRef(
        "https://openenergyplatform.org/ontology/oekg/region/UnitedKingdomOfGreatBritainAndNorthernIreland"  # noqa: E501
    )
    for s, p, o in oekg.triples((scenario_region, RDFS.label, None)):
        if str(o) == "None":
            oekg.remove((s, p, o))
    response = JsonResponse("Done!", safe=False, content_type="application/json")
    patch_response_headers(response, cache_timeout=1)
    return response


def get_entities_by_type_view(request, *args, **kwargs):
    """
    Returns all entities (from OEKG) with a certain type.
    The type should be supplied by the user.

    Args:
        request (HttpRequest): The incoming HTTP GET request.
        entity_type (str): The type(OEO class) of the entity.
    """
    entity_type = request.GET.get("entity_type")
    vocab = entity_type.split(".")[0]
    classId = entity_type.split(".")[1]
    prefix = ""
    if vocab == "OEO":
        prefix = "https://openenergyplatform.org/ontology/oeo/"
    if vocab == "OBO":
        prefix = "http://purl.obolibrary.org/obo/"

    entity_URI = URIRef(prefix + classId)

    entities = []
    for s, p, o in oekg.triples((None, RDF.type, entity_URI)):
        sl = oekg.value(s, RDFS.label)
        entities.append({"name": sl, "id": sl, "iri": str(s).split("/")[-1]})

    response = JsonResponse(entities, safe=False, content_type="application/json")
    patch_response_headers(response, cache_timeout=1)
    return response


@login_required
def add_entities_view(request, *args, **kwargs):
    """
    Add entities to OEKG. The minimum requirements for
    adding an entity are the type and label.

    Args:
        request (HttpRequest): The incoming HTTP GET request.
        entity_type (str): The type(OEO class) of the entity.
        entity_label (str): The label of the entity.
        entity_iri (str): The IRI of the entity.
    """
    request_body = json.loads(request.body)
    entity_type = request_body["entity_type"]
    entity_label = request_body["entity_label"]
    entity_iri = request_body["entity_iri"]

    vocab = entity_type.split(".")[0]
    classId = entity_type.split(".")[1]
    prefix = ""
    if vocab == "OEO":
        prefix = "https://openenergyplatform.org/ontology/oeo/"
    if vocab == "OBO":
        prefix = "http://purl.obolibrary.org/obo/"

    entity_type_URI = URIRef(prefix + classId)

    entity_URI = URIRef("https://openenergyplatform.org/ontology/oekg/" + entity_iri)

    oekg.add((entity_URI, RDF.type, entity_type_URI))
    oekg.add((entity_URI, RDFS.label, Literal(entity_label)))

    response = JsonResponse(
        "A new entity added!", safe=False, content_type="application/json"
    )
    patch_response_headers(response, cache_timeout=1)
    return response


@login_required
def add_a_fact_view(request, *args, **kwargs):
    request_body = json.loads(request.body)
    _subject = request_body["subject"]
    _predicate = request_body["predicate"]
    _object = request_body["object"]

    _subject_URI = URIRef(
        "https://openenergyplatform.org/ontology/oekg/" + clean_name(_subject)
    )
    _predicate_URI = URIRef(
        "https://openenergyplatform.org/ontology/oeo/" + clean_name(_predicate)
    )
    _object_URI = URIRef(
        "https://openenergyplatform.org/ontology/oekg/" + clean_name(_object)
    )

    oekg.add((_subject_URI, _predicate_URI, _object_URI))

    response = JsonResponse(
        "A new fact added!", safe=False, content_type="application/json"
    )
    patch_response_headers(response, cache_timeout=1)
    return response


@login_required
def update_an_entity_view(request, *args, **kwargs):
    """
    Updates an entity in OEKG. The minimum requirements for
    updating an entity are the type, the old label, and the
    new label.

    Args:
        request (HttpRequest): The incoming HTTP GET request.
        entity_type (str): The type(OEO class) of the entity.
        entity_label (str): The label of the entity.
        new_entity_label (str): The new label of the entity.
        entity_id (str): The IRI of the entity.
    """
    request_body = json.loads(request.body)
    entity_type = request_body["entity_type"]
    entity_label = request_body["entity_label"]
    new_entity_label = request_body["new_entity_label"]
    entity_id = request_body["entity_iri"]

    vocab = entity_type.split(".")[0]
    classId = entity_type.split(".")[1]
    prefix = ""
    if vocab == "OEO":
        prefix = "https://openenergyplatform.org/ontology/oeo/"
    if vocab == "OBO":
        prefix = "http://purl.obolibrary.org/obo/"

    entity_type_URI = URIRef(prefix + classId)  # noqa
    entity_IRI = URIRef("https://openenergyplatform.org/ontology/oekg/" + (entity_id))

    oekg.add((entity_IRI, RDFS.label, Literal(new_entity_label)))
    oekg.remove((entity_IRI, RDFS.label, Literal(entity_label)))

    response = JsonResponse(
        "entity updated!", safe=False, content_type="application/json"
    )
    patch_response_headers(response, cache_timeout=1)
    return response


def get_all_factsheets_view(request, *args, **kwargs):
    criteria = {
        "institutions": request.GET.getlist("institutions"),
        "authors": request.GET.getlist("authors"),
        "fundingSource": request.GET.getlist("fundingSource"),
        "studyKeywords": request.GET.getlist("studyKeywords")
        or request.GET.getlist("studyKewords"),
        "scenarioYearValue": request.GET.getlist("scenarioYearValue"),  # [start, end]
        "startDateOfPublication": request.GET.get("startDateOfPublication"),
        "endDateOfPublication": request.GET.get("endDateOfPublication"),
        "resultsPerPage": request.GET.get("resultsPerPage", 25),
        "page": request.GET.get("page", 1),
    }

    # 1) Fast list via SPARQL
    res = list_factsheets_oekg(criteria)
    factsheets = normalize_factsheets_rows(res)

    # 2) (Optional) If you still want scenarios embedded,
    # keep your existing call per bundle:
    for f in factsheets:
        data = bundle_scenarios_filter(
            f"https://openenergyplatform.org/ontology/oekg/{f['uid']}"
        )

        def bval(row, key):
            cell = row.get(key)
            return cell.get("value") if cell else None

        f["scenarios"] = [
            {
                "label": bval(r, "label"),
                "abstract": bval(r, "abstract"),
                "full_name": bval(r, "fullName"),
                "uid": bval(r, "uid"),
            }
            for r in data["results"]["bindings"]
        ]

    response = JsonResponse(factsheets, safe=False, content_type="application/json")
    patch_response_headers(response, cache_timeout=1)
    return response


def get_scenarios_view(request, *args, **kwargs):
    scenarios_uid = [
        i.replace("%20", " ") for i in json.loads(request.GET.get("scenarios_uid"))
    ]

    scenarios = []

    # Create an instance of OekgQuery
    oekg_query = OekgQuery()

    for s, p, o in oekg.triples((None, RDF.type, OEO.OEO_00000365)):
        scenario_uid = str(s).split("/")[-1]
        if str(scenario_uid) in scenarios_uid:
            study_descriptors = []
            scenario_descriptors = []
            regions = []
            interacting_regions = []
            scenario_years = []
            input_datasets = []
            output_datasets = []
            abstract = ""

            for s, p, o in oekg.triples((s, DC.abstract, None)):
                abstract = o

            for s1, p1, o1 in oekg.triples((s, OEO.OEO_00390073, None)):
                scenario_descriptors.append(
                    (
                        str(oeo.value(o1, RDFS.label)),
                        get_scenario_type_iri(str(oeo.value(o1, RDFS.label))),
                    )
                )

            for s1, p1, o1 in oekg.triples((s, OEO.OEO_00020220, None)):
                o1_label = oekg.value(o1, RDFS.label)
                regions.append(o1_label)

            for s1, p1, o1 in oekg.triples((s, OEO.OEO_00020222, None)):
                o1_label = oekg.value(o1, RDFS.label)
                interacting_regions.append(o1_label)

            for s4, p4, o4 in oekg.triples((s, OEO.OEO_00020440, None)):
                scenario_years.append(o4)
            for s5, p5, o5 in oekg.triples((s, OEO.OEO_00020437, None)):
                oekg_value = oekg.value(o5, OEO.OEO_00390094)
                comparable = str(oekg_value).split("scenario/")
                input_datasets.append(
                    (
                        oekg.value(o5, RDFS.label),
                        oekg.value(o5, OEO.OEO_00390094),
                        comparable[1],
                    )
                )
            for s6, p6, o6 in oekg.triples((s, OEO.OEO_00020436, None)):
                oekg_value = oekg.value(o6, OEO.OEO_00390094)
                comparable = str(oekg_value).split("scenario/")

                output_datasets.append(
                    (
                        oekg.value(o6, RDFS.label),
                        oekg.value(o6, OEO.OEO_00390094),
                        comparable[1],
                    )
                )

            for s1, p1, o1 in oekg.triples((None, OBO.BFO_0000051, s)):
                study_label = oekg.value(s1, RDFS.label)
                study_abstract = oekg.value(s1, DC.abstract)

            # additionally get the study descriptors from the scenario bundle
            study_descriptors = (
                oekg_query.get_bundle_study_descriptors_where_scenario_is_part_of(
                    scenario_uid=scenario_uid
                )
            )

            scenarios.append(
                {
                    "acronym": oekg.value(s, RDFS.label),
                    "data": {
                        "uid": scenario_uid,
                        "study_descriptors": study_descriptors,
                        "scenario_descriptors": scenario_descriptors,
                        "regions": regions,
                        "interacting_regions": interacting_regions,
                        "scenario_years": scenario_years,
                        "input_datasets": input_datasets,
                        "output_datasets": output_datasets,
                        "abstract": abstract,
                        "study_label": study_label,
                        "study_abstract": study_abstract,
                    },
                }
            )

    response = JsonResponse(scenarios, safe=False, content_type="application/json")
    return response


@login_required
def get_all_factsheets_as_turtle_view(request, *args, **kwargs):
    all_factsheets_as_turtle = oekg.serialize(format="ttl")

    response = HttpResponse(all_factsheets_as_turtle, content_type="text/turtle")
    response["Content-Disposition"] = 'attachment; filename="oekg.ttl"'
    return response


def get_all_factsheets_as_json_ld_view(request, *args, **kwargs):
    all_factsheets_as_json_ld = oekg.serialize(format="json-ld")

    response = HttpResponse(
        all_factsheets_as_json_ld, content_type="application/ld+json"
    )
    response["Content-Disposition"] = 'attachment; filename="oekg.jsonld"'

    return response


# @login_required
def populate_factsheets_elements_view(request, *args, **kwargs):
    """
    This function populates the elements required for creating or updating a factsheet.
    For example: Elements returned form this function populate dropdown elements which
    help the user to select sectors, technologies, scenario descriptors etc.

    Args:
        request (HttpRequest): The incoming HTTP GET request.

    Returns:
        JsonResponse: A JSON response containing the elements for factsheet creation or
                    update.
    """
    scenario_class = oeo_owl.search_one(iri=OEO.OEO_00000364)
    scenario_subclasses = get_all_sub_classes(scenario_class)

    technology_class = oeo_owl.search_one(iri=OEO.OEO_00000407)
    technology_subclasses = get_all_sub_classes(technology_class)

    # energy_carrier_class = oeo_owl.search_one(iri="http://openenergy-platform.org/ontology/oeo/OEO_00020039") # noqa
    # energy_carriers = get_all_sub_classes(energy_carrier_class)

    # energy_transformation_process_class = oeo_owl.search_one(iri="http://openenergy-platform.org/ontology/oeo/OEO_00020003") # noqa
    # energy_transformation_processes = get_all_sub_classes(energy_transformation_process_class) # noqa

    sector_divisions_list, sectors_list = build_sector_dropdowns_from_oeo(oeo)
    elements = {}
    # elements['energy_carriers'] = [energy_carriers]
    # elements['energy_transformation_processes'] = [energy_transformation_processes]
    elements["sector_divisions"] = sector_divisions_list
    elements["sectors"] = sectors_list
    elements["scenario_descriptors"] = scenario_subclasses
    elements["technologies"] = technology_subclasses

    # for s, p, o in oeo.triples(( None, RDFS.subClassOf, OEO.OEO_00020003 )):
    #     sl = oeo.value(s, RDFS.label)
    #     parent = {
    #         'value': str(sl),
    #         'label': sl,
    #         'class': s
    #     }
    #     children = []
    #     for s1, p, o in oeo.triples(( None, RDFS.subClassOf, s )):
    #         sl1 = oeo.value(s1, RDFS.label)
    #         children2 = []
    #         for s2, p, o in oeo.triples(( None, RDFS.subClassOf, s1 )):
    #             sl2 = oeo.value(s2, RDFS.label)
    #             children3 = []
    #             for s3, p, o in oeo.triples(( None, RDFS.subClassOf, s2 )):
    #                 sl3 = oeo.value(s3, RDFS.label)
    #                 children3.append({
    #                     'value': str(sl) + str(sl1) + str(sl2) + str(sl3),
    #                     'label': sl3,
    #                     'class': s3
    #                 })

    #             if children3 != []:
    #                 children2.append({
    #                     'value': str(sl) + str(sl1) + str(sl2),
    #                     'label': sl2,
    #                     'class': s2,
    #                     'children': children3
    #                 })
    #             else:
    #                 children2.append({
    #                     'value': str(sl) + str(sl1) + str(sl2),
    #                     'class': s2,
    #                     'label': sl2,
    #                 })

    #         if children2 != []:
    #             children.append({
    #             'value': str(sl) + str(sl1),
    #             'label': sl1,
    #             'class': s1,
    #             'children': children2
    #             })
    #         else:
    #             children.append({
    #             'value': str(sl) + str(sl1),
    #             'class': s1,
    #             'label': sl1
    #             })

    #     if children != []:
    #         parent['children'] = children

    #     energy_transformation_processes.append(parent)

    # energy_carriers = []
    # for s, p, o in oeo.triples(( None, RDFS.subClassOf, OEO.OEO_00020039 )):
    #     sl = oeo.value(s, RDFS.label)
    #     parent = {
    #         'value': str(sl),
    #         'label': sl,
    #         'class': s
    #     }
    #     children = []
    #     for s1, p, o in oeo.triples(( None, RDFS.subClassOf, s )):
    #         sl1 = oeo.value(s1, RDFS.label)
    #         children2 = []
    #         for s2, p, o in oeo.triples(( None, RDFS.subClassOf, s1 )):
    #             sl2 = oeo.value(s2, RDFS.label)
    #             children3 = []
    #             for s3, p, o in oeo.triples(( None, RDFS.subClassOf, s2 )):
    #                 sl3 = oeo.value(s3, RDFS.label)
    #                 children3.append({
    #                     'value': str(sl) + "^^" + str(sl1) + "^^" + str(sl2) + "^^" + str(sl3), # noqa
    #                     'label': sl3,
    #                     'class': s3
    #                 })

    #             if children3 != []:
    #                 children2.append({
    #                     'value': str(sl) + "^^" + str(sl1) + "^^" + str(sl2),
    #                     'label': sl2,
    #                     'class': s2,
    #                     'children': children3
    #                 })
    #             else:
    #                 children2.append({
    #                     'value': str(sl) + "^^" + str(sl1) + "^^" + str(sl2),
    #                     'label': sl2,
    #                 })

    #         if children2 != []:
    #             children.append({
    #             'value': str(sl) + "^^" + str(sl1),
    #             'label': sl1,
    #             'class': s1,
    #             'children': children2
    #             })
    #         else:
    #             children.append({
    #             'value': str(sl) + "^^" + str(sl1),
    #             'class': s1,
    #             'label': sl1
    #             })

    #     if children != []:
    #         parent['children'] = children

    #     energy_carriers.append(parent)

    response = JsonResponse(elements, safe=False, content_type="application/json")
    patch_response_headers(response, cache_timeout=1)

    return response


@never_cache
def filter_scenario_bundles_view(request):
    # Get the table IRI from the request or any other source
    table_iri = request.GET.get("table_iri", "")
    table_name = table_iri.strip("/").split("/")[-1]

    # Create an instance of OekgQuery
    oekg_query = OekgQuery()

    # Get related scenarios where the table is the input dataset
    input_dataset_bundles = oekg_query.get_scenario_bundles_where_table_is_input(
        table_iri
    )

    # Get related scenarios where the table is the output dataset
    output_dataset_bundles = oekg_query.get_scenario_bundles_where_table_is_output(
        table_iri
    )

    # Get the acronyms for the scenarios
    input_dataset_bundle_acronyms = [
        (
            oekg_query.get_bundle_acronym(bundle_uri),
            oekg_query.get_bundle_uid(oekg_bundle),
        )
        for bundle_uri, oekg_bundle in input_dataset_bundles
    ]

    output_dataset_bundle_acronyms = [
        (
            oekg_query.get_bundle_acronym(bundle_uri),
            oekg_query.get_bundle_uid(oekg_bundle),
        )
        for bundle_uri, oekg_bundle in output_dataset_bundles
    ]

    # Prepare data for rendering in the template
    context = {
        "table_name": table_name,
        "input_dataset_bundles": input_dataset_bundle_acronyms,
        "output_dataset_bundles": output_dataset_bundle_acronyms,
    }
    html_content = render(
        request, "partials/related_oekg_scenarios.html", context
    ).content.decode("utf-8")

    # Render the template with the context
    return HttpResponse(html_content)
