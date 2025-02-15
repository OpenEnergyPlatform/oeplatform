import json
import logging

from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import render
from django.utils.cache import patch_response_headers
from django.views.decorators.cache import never_cache
from rdflib import RDF, Graph, Literal, URIRef
from rdflib.compare import graph_diff, to_isomorphic
from SPARQLWrapper import JSON

from factsheet.oekg.connection import oekg, oeo, oeo_owl, sparql
from factsheet.oekg.filters import OekgQuery
from factsheet.oekg.namespaces import DC, OBO, OEKG, OEO, RDFS, bind_all_namespaces
from factsheet.permission_decorator import only_if_user_is_owner_of_scenario_bundle
from factsheet.utils import serialize_publication_date
from factsheet.utils import remove_non_printable
from login import models as login_models
from modelview.utils import get_framework_metadata_by_id, get_model_metadata_by_id

from .models import OEKG_Modifications, ScenarioBundleAccessControl

oekg = bind_all_namespaces(graph=oekg)


def clean_name(name):
    return (
        name.rstrip()
        .lstrip()
        .replace("-", "_")
        .replace(" ", "_")
        .replace("%", "")
        .replace("Ö", "Oe")
        .replace("ö", "oe")
        .replace("/", "_")
        .replace(":", "_")
        .replace("(", "_")
        .replace(")", "_")
        .replace("ü", "ue")
    )


def undo_clean_name(name):
    return name.rstrip().lstrip().replace("_", " ")


def factsheets_index(request, *args, **kwargs):
    # userLoggedIn = False
    # if request.user.is_authenticated:
    #     userLoggedIn = True

    # context_data = {
    #     "userLoggedIn": userLoggedIn,
    # }

    return render(request, "factsheet/index.html")


def set_ownership(bundle_uid, user):
    model = ScenarioBundleAccessControl()
    model.owner_user = user
    model.bundle_id = bundle_uid
    model.save()
    return f"The ownership of bundle {bundle_uid} is now set to User {user.name}"


def is_owner(user, bundle_id):
    bundle = ScenarioBundleAccessControl.load_by_uid(uid=bundle_id)
    if bundle is not None:
        eval = user == bundle.owner_user.id
    else:
        eval = False

    return eval


def check_ownership(request, bundle_id):
    if bundle_id != "new":
        if is_owner(request.user.id, bundle_id):
            return JsonResponse(
                {"isOwner": True}, safe=False, content_type="application/json"
            )
        else:
            return JsonResponse(
                {"isOwner": False}, safe=False, content_type="application/json"
            )
    else:
        return JsonResponse(
            {"isOwner": True}, safe=False, content_type="application/json"
        )


def add_history(triple_subject, triple_predicate, triple_object, type_of_action, user):
    histroy_instance = HistoryOfOEKG(  # noqa: F821
        triple_subject=triple_subject,
        triple_predicate=triple_predicate,
        triple_object=triple_object,
        type_of_action=type_of_action,
        user=user,
    )
    histroy_instance.save()
    return "saved"


def get_history(request, *args, **kwargs):
    histroy = HistoryOfOEKG.objects.all()  # noqa: F821
    histroy_json = serializers.serialize("json", histroy)
    response = JsonResponse(histroy_json, safe=False, content_type="application/json")
    patch_response_headers(response, cache_timeout=1)
    return response


def get_oekg_modifications(request, *args, **kwargs):
    histroy = OEKG_Modifications.objects.all()
    histroy_json = serializers.serialize("json", histroy)
    response = JsonResponse(histroy_json, safe=False, content_type="application/json")
    patch_response_headers(response, cache_timeout=1)
    return response
    

def filter_oekg_modifications(request,*args,**kwargs):
    field_name = input("Input the Field you want to filter by: ")
    field_value = input("Input the field value: ")
    if (str(field_name) in ("bundle_id","id","timestamp","user","user_id")):
         kwargs = {field_name:field_value}
         histroy = OEKG_Modifications.objects.all().filter(**kwargs)
    else: #search jsons
         matching_entries = []
         i = 0
         for entry in OEKG_Modifications.objects.all():
              if filter_by(i, field_name, field_value):
                   matching_entries.append(entry.id)
              i += 1
         history = OEKG_Modifications.objects.filter(id__in=matching_entries)
    histroy_json = serializers.serialize("json", OEKG_Modifications.objects.filter(id__in=matching_entries))
    response = JsonResponse(histroy_json, safe=False, content_type="application/json")
    patch_response_headers(response, cache_timeout=1)
    
    
def filter_state(d, filter_field, filter_val):
    if not d:
         return False
    elif not filter_field in d[0]:
         return False
    else:
         if isinstance(d[0][filter_field], list):   #if the value is a list     #add for loop to interate over d[0][filter_field][i]
              for i in range (len(d[0][filter_field])):
                    if filter_val in (d[0][filter_field][i]).values():
                        return True
              return False
         else:
              if d[0][filter_field] == filter_val:
                   return True
              return False
              
def filter_by(nmbr, filter_field, filter_val):
    old_state = json.loads((OEKG_Modifications.objects.values('old_state')[nmbr]).get("old_state", "not found"))
    new_state = json.loads((OEKG_Modifications.objects.values('new_state')[nmbr]).get("new_state", "not found"))
    if filter_state(old_state, filter_field, filter_val):
         return True
    if filter_state(new_state, filter_field, filter_val):
         return True
    return False
    

# @login_required
def create_factsheet(request, *args, **kwargs):
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
    acronym = (request_body["acronym"])
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

    for s, p, o in oekg.triples((None, RDF.type, OEO.OEO_00010252)):
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

        study_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + uid)
        bundle.add((study_URI, RDF.type, OEO.OEO_00010252))

        if acronym != "":
            bundle.add((study_URI, DC.acronym, Literal(remove_non_printable(acronym))))
        if study_name != "":
            bundle.add((study_URI, OEKG["has_full_name"], Literal(remove_non_printable(study_name))))
        if abstract != "":
            bundle.add((study_URI, DC.abstract, Literal(remove_non_printable(abstract))))

        _publications = json.loads(publications) if publications is not None else []
        for item in _publications:
            publications_URI = URIRef(
                "http://openenergy-platform.org/ontology/oekg/publication/" + item["id"]
            )
            bundle.add(
                (publications_URI, OEKG["publication_uuid"], Literal(item["id"]))
            )

            bundle.add((study_URI, OEKG["has_publication"], publications_URI))
            if item["report_title"] != "":
                bundle.add(
                    (publications_URI, RDFS.label, Literal(remove_non_printable(item["report_title"])))
                )

            _authors = item["authors"]
            for author in _authors:
                author_URI = URIRef(
                    "http://openenergy-platform.org/ontology/oekg/" + author["iri"]
                )
                bundle.add((publications_URI, OEO.OEO_00000506, author_URI))

            if item["doi"] != "":
                bundle.add((publications_URI, OEKG["doi"], Literal(item["doi"])))

            if (
                item["date_of_publication"] != "01-01-1900"
                and item["date_of_publication"] != ""
            ):
                bundle.add(
                    (
                        publications_URI,
                        OEKG["date_of_publication"],
                        Literal(item["date_of_publication"]),
                    )
                )

            if item["link_to_study_report"] != "":
                bundle.add(
                    (
                        publications_URI,
                        OEKG["link_to_study_report"],
                        Literal(item["link_to_study_report"]),
                    )
                )

            bundle.add((study_URI, OEKG["has_publication"], publications_URI))

        _scenarios = json.loads(scenarios) if scenarios is not None else []
        for item in _scenarios:
            if item["acronym"] != "":
                # TODO- set in settings
                scenario_URI = URIRef(
                    "http://openenergy-platform.org/ontology/oekg/scenario/"
                    + item["id"]
                )
                bundle.add((study_URI, OEKG["has_scenario"], scenario_URI))
                bundle.add((scenario_URI, RDFS.label, Literal(remove_non_printable(item["acronym"]))))
                if item["name"] != "":
                    bundle.add(
                        (scenario_URI, OEKG["has_full_name"], Literal(remove_non_printable(item["name"])))
                    )
                    bundle.add((scenario_URI, RDF.type, OEO.OEO_00000365))
                if item["abstract"] != "":
                    bundle.add((scenario_URI, DC.abstract, Literal(remove_non_printable(item["abstract"]))))

                bundle.add((scenario_URI, OEKG["scenario_uuid"], Literal(item["id"])))

                if "regions" in item:
                    for region in item["regions"]:
                        region_URI = URIRef(region["iri"])
                        scenario_region = URIRef(
                            "http://openenergy-platform.org/ontology/oekg/region/"
                            + region["iri"].rsplit("/", 1)[1]
                        )
                        bundle.add((scenario_region, RDF.type, OEO.OEO_00020032))
                        bundle.add(
                            (scenario_region, RDFS.label, Literal(region["name"]))
                        )
                        bundle.add((scenario_region, OEKG["reference"], region_URI))
                        bundle.add((scenario_URI, OEO.OEO_00020220, scenario_region))

                if "interacting_regions" in item:
                    for interacting_region in item["interacting_regions"]:
                        interacting_region_URI = URIRef(interacting_region["iri"])
                        scenario_interacting_region = URIRef(
                            "http://openenergy-platform.org/ontology/oekg/"
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
                                OEKG["reference"],
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
                                OEO.OEO_00020224,
                                Literal(scenario_year["name"]),
                            )
                        )

                if "descriptors" in item:
                    for descriptor in item["descriptors"]:
                        descriptor = URIRef(descriptor["class"])
                        bundle.add(
                            (scenario_URI, OEO["has_scenario_descriptor"], descriptor)
                        )

                # TODO: jh-RLI: Update to avoid duplicated table name entries
                if "input_datasets" in item:
                    for input_dataset in item["input_datasets"]:
                        # TODO- set in settings
                        input_dataset_URI = URIRef(
                            "http://openenergy-platform.org/ontology/oekg/input_datasets/"  # noqa
                            + input_dataset["key"]
                        )
                        bundle.add((input_dataset_URI, RDF.type, OEO.OEO_00030030))
                        bundle.add(
                            (
                                input_dataset_URI,
                                RDFS.label,
                                Literal(remove_non_printable(input_dataset["value"]["label"])),
                            )
                        )
                        bundle.add(
                            (
                                input_dataset_URI,
                                OEO["has_iri"],
                                Literal(input_dataset["value"]["url"]),
                            )
                        )
                        bundle.add(
                            (
                                input_dataset_URI,
                                OEO["has_id"],
                                Literal(input_dataset["idx"]),
                            )
                        )
                        bundle.add(
                            (
                                input_dataset_URI,
                                OEO["has_key"],
                                Literal(input_dataset["key"]),
                            )
                        )
                        bundle.add((scenario_URI, OEO.RO_0002233, input_dataset_URI))

                # TODO: jh-RLI: Update to avoid duplicated table name entries
                if "output_datasets" in item:
                    for output_dataset in item["output_datasets"]:
                        # TODO- set in settings
                        output_dataset_URI = URIRef(
                            "http://openenergy-platform.org/ontology/oekg/output_datasets/"  # noqa
                            + output_dataset["key"]
                        )
                        bundle.add((output_dataset_URI, RDF.type, OEO.OEO_00030029))
                        bundle.add(
                            (
                                output_dataset_URI,
                                RDFS.label,
                                Literal(remove_non_printable(output_dataset["value"]["label"])),
                            )
                        )
                        bundle.add(
                            (
                                output_dataset_URI,
                                OEO["has_iri"],
                                Literal(output_dataset["value"]["url"]),
                            )
                        )
                        bundle.add(
                            (
                                output_dataset_URI,
                                OEO["has_id"],
                                Literal(output_dataset["idx"]),
                            )
                        )
                        bundle.add(
                            (
                                output_dataset_URI,
                                OEO["has_key"],
                                Literal(output_dataset["key"]),
                            )
                        )
                        bundle.add((scenario_URI, OEO.RO_0002234, output_dataset_URI))

        institutions = json.loads(institution) if institution is not None else []
        for item in institutions:
            institution_URI = URIRef(
                "http://openenergy-platform.org/ontology/oekg/" + item["iri"]
            )
            bundle.add((study_URI, OEO.OEO_00000510, institution_URI))

        funding_sources = (
            json.loads(funding_source) if funding_source is not None else []
        )
        for item in funding_sources:
            funding_source_URI = URIRef(
                "http://openenergy-platform.org/ontology/oekg/" + item["iri"]
            )
            bundle.add((study_URI, OEO.OEO_00000509, funding_source_URI))
        contact_persons = (
            json.loads(contact_person) if contact_person is not None else []
        )
        for item in contact_persons:
            contact_person_URI = URIRef(
                "http://openenergy-platform.org/ontology/oekg/" + item["iri"]
            )
            bundle.add((study_URI, OEO.OEO_00000508, contact_person_URI))

        _sector_divisions = (
            json.loads(sector_divisions) if sector_divisions is not None else []
        )
        for item in _sector_divisions:
            sector_divisions_URI = URIRef(item["class"])
            bundle.add(
                (study_URI, OEO["based_on_sector_division"], sector_divisions_URI)
            )

        _sectors = json.loads(sectors) if sectors is not None else []
        for item in _sectors:
            sector_URI = URIRef(item["class"])
            bundle.add((study_URI, OEO.OEO_00000505, sector_URI))

        _technologies = json.loads(technologies) if technologies is not None else []
        for item in _technologies:
            technology_URI = URIRef(item["class"])
            bundle.add((study_URI, OEO.OEO_00000522, technology_URI))

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
                "http://openenergy-platform.org/ontology/oekg/models/" + str(model_id)
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
                    OEO["has_iri"],
                    Literal(model_url),
                )
            )
            bundle.add((study_URI, OEO["has_model"], model_URI))

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
                "http://openenergy-platform.org/ontology/oekg/frameworks/"
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
                        OEO["has_iri"],
                        Literal(framework_url),
                    )
                )

            bundle.add((study_URI, OEO["has_framework"], framework_URI))

        _study_keywords = (
            json.loads(study_keywords) if study_keywords is not None else []
        )
        if _study_keywords != []:
            for keyword in _study_keywords:
                bundle.add((study_URI, OEO["has_study_keyword"], Literal(keyword)))

        for s, p, o in bundle.triples((None, None, None)):
            oekg.add((s, p, o))

        response = JsonResponse(
            "Factsheet saved", safe=False, content_type="application/json"
        )
        result = set_ownership(bundle_uid=uid, user=request.user)
        logging.info(result)
        patch_response_headers(response, cache_timeout=1)

        return response


@login_required
@only_if_user_is_owner_of_scenario_bundle
def update_factsheet(request, *args, **kwargs):
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
    id = request_body["id"]  # noqa
    uid = request_body["uid"]
    name = request_body["name"]  # noqa
    studyName = request_body["study_name"]
    acronym = request_body["acronym"]
    abstract = request_body["abstract"]
    institution = request_body["institution"]
    funding_source = request_body["funding_source"]
    contact_person = request_body["contact_person"]
    sector_divisions = request_body["sector_divisions"]
    sectors = request_body["sectors"]
    expanded_sectors = request_body["expanded_sectors"]  # noqa
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

    for s, p, o in oekg.triples((None, RDF.type, OEO.OEO_00010252)):
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
        study_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + uid)

        old_bundle = Graph()
        for s, p, o in oekg.triples((study_URI, None, None)):
            old_bundle.add((s, p, o))
        for s, p, o in oekg.triples((study_URI, OEKG["has_scenario"], None)):
            for s1, p1, o1 in oekg.triples((o, None, None)):
                old_bundle.add((s1, p1, o1))

        new_bundle = Graph()
        new_bundle.add((study_URI, RDF.type, OEO.OEO_00010252))

        _publications = json.loads(publications) if publications is not None else []
        for item in _publications:
            publications_URI = URIRef(
                "http://openenergy-platform.org/ontology/oekg/publication/" + item["id"]
            )
            new_bundle.add(
                (publications_URI, OEKG["publication_uuid"], Literal(item["id"]))
            )
            new_bundle.add((study_URI, OEKG["has_publication"], publications_URI))
            if item["report_title"] != "":
                new_bundle.add(
                    (publications_URI, RDFS.label, Literal(item["report_title"]))
                )

            _authors = item["authors"]
            # Check if list is empty to avoid adding empty elements to the OEKG
            if _authors:
                for author in _authors:
                    # TODO: (@adel please check):
                    # Workaround below to avoid adding empty new
                    # autors every time a new publication is added
                    if author["name"]:
                        author_URI = URIRef(
                            "http://openenergy-platform.org/ontology/oekg/"
                            + author["iri"]
                        )
                        new_bundle.add((publications_URI, OEO.OEO_00000506, author_URI))

            if item["doi"] != "":
                new_bundle.add((publications_URI, OEKG["doi"], Literal(item["doi"])))

            if (
                item["date_of_publication"] != "1900"
                and item["date_of_publication"] != ""
            ):
                new_bundle.add(
                    (
                        publications_URI,
                        OEKG["date_of_publication"],
                        Literal(item["date_of_publication"]),
                    )
                )

            if item["link_to_study_report"] != "":
                new_bundle.add(
                    (
                        publications_URI,
                        OEKG["link_to_study_report"],
                        Literal(item["link_to_study_report"]),
                    )
                )

            new_bundle.add((study_URI, OEKG["has_publication"], publications_URI))

            # remove old date in publication
            # iterate to make sure it can only have unique publication date
            for _s, _p, _o in oekg.triples(
                (publications_URI, OEKG["date_of_publication"], None)
            ):
                oekg.remove((_s, _p, _o))

        _scenarios = json.loads(scenarios) if scenarios is not None else []
        for item in _scenarios:
            if item["acronym"] != "":
                scenario_URI = URIRef(
                    "http://openenergy-platform.org/ontology/oekg/scenario/"
                    + item["id"]
                )

                for s, p, o in oekg.triples((scenario_URI, None, None)):
                    oekg.remove((o, p, o))

                new_bundle.add(
                    (scenario_URI, OEKG["scenario_uuid"], Literal(item["id"]))
                )
                new_bundle.add((scenario_URI, RDF.type, OEO.OEO_00000365))
                new_bundle.add((scenario_URI, RDFS.label, Literal((item["acronym"]))))
                if item["name"] != "":
                    new_bundle.add(
                        (scenario_URI, OEKG["has_full_name"], Literal(remove_non_printable(item["name"])))
                    )
                if item["abstract"] != "" and item["abstract"] != None:  # noqa
                    new_bundle.add(
                        (scenario_URI, DC.abstract, Literal(remove_non_printable(item["abstract"])))
                    )
                if "regions" in item:
                    for region in item["regions"]:
                        region_URI = URIRef(region["iri"])
                        scenario_region = URIRef(
                            "http://openenergy-platform.org/ontology/oekg/region/"
                            + region["iri"].rsplit("/", 1)[1]
                        )
                        new_bundle.add((scenario_region, RDF.type, OEO.OEO_00020032))
                        new_bundle.add(
                            (scenario_region, RDFS.label, Literal(remove_non_printable(region["name"])))
                        )
                        new_bundle.add(
                            (
                                scenario_region,
                                OEKG["reference"],
                                region_URI,
                            )
                        )
                        new_bundle.add(
                            (scenario_URI, OEO.OEO_00020220, scenario_region)
                        )

                if "interacting_regions" in item:
                    for interacting_region in item["interacting_regions"]:
                        interacting_region_URI = URIRef(interacting_region["iri"])
                        scenario_interacting_region = URIRef(
                            "http://openenergy-platform.org/ontology/oekg/"
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
                                OEKG["reference"],
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

                if "scenario_years" in item:
                    for scenario_year in item["scenario_years"]:
                        new_bundle.add(
                            (
                                scenario_URI,
                                OEO.OEO_00020224,
                                Literal(scenario_year["name"]),
                            )
                        )

                if "descriptors" in item:
                    for descriptor in item["descriptors"]:
                        descriptor = URIRef(descriptor["class"])
                        new_bundle.add(
                            (scenario_URI, OEO["has_scenario_descriptor"], descriptor)
                        )

                # TODO: jh-RLI: Update to avoid duplicated table name entries
                if "input_datasets" in item:
                    for input_dataset in item["input_datasets"]:
                        input_dataset_URI = URIRef(
                            "http://openenergy-platform.org/ontology/oekg/input_datasets/"  # noqa
                            + input_dataset["key"]
                        )

                        for s, p, o in oekg.triples((input_dataset_URI, None, None)):
                            oekg.remove((o, p, o))

                        new_bundle.add((input_dataset_URI, RDF.type, OEO.OEO_00030030))
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
                                OEO["has_iri"],
                                Literal(input_dataset["value"]["url"]),
                            )
                        )
                        new_bundle.add(
                            (
                                input_dataset_URI,
                                OEO["has_id"],
                                Literal(input_dataset["idx"]),
                            )
                        )
                        new_bundle.add(
                            (
                                input_dataset_URI,
                                OEO["has_key"],
                                Literal(input_dataset["key"]),
                            )
                        )
                        new_bundle.add(
                            (scenario_URI, OEO.RO_0002233, input_dataset_URI)
                        )

                # TODO: jh-RLI: Update to avoid duplicated table name entries
                if "output_datasets" in item:
                    for output_dataset in item["output_datasets"]:
                        output_dataset_URI = URIRef(
                            "http://openenergy-platform.org/ontology/oekg/output_datasets/"  # noqa: E501
                            + output_dataset["key"]
                        )
                        new_bundle.add((output_dataset_URI, RDF.type, OEO.OEO_00030029))
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
                                OEO["has_iri"],
                                Literal(output_dataset["value"]["url"]),
                            )
                        )
                        new_bundle.add(
                            (
                                output_dataset_URI,
                                OEO["has_id"],
                                Literal(output_dataset["idx"]),
                            )
                        )
                        new_bundle.add(
                            (
                                output_dataset_URI,
                                OEO["has_key"],
                                Literal(output_dataset["key"]),
                            )
                        )
                        new_bundle.add(
                            (scenario_URI, OEO.RO_0002234, output_dataset_URI)
                        )

                new_bundle.add((study_URI, OEKG["has_scenario"], scenario_URI))

        if acronym != "":
            new_bundle.add((study_URI, DC.acronym, Literal(remove_non_printable(acronym))))

        new_bundle.add((study_URI, OEKG["has_full_name"], Literal(remove_non_printable(studyName))))

        institutions = json.loads(institution) if institution is not None else []
        for item in institutions:
            institution_URI = URIRef(
                "http://openenergy-platform.org/ontology/oekg/" + item["iri"]
            )
            new_bundle.add((study_URI, OEO.OEO_00000510, institution_URI))

        funding_sources = (
            json.loads(funding_source) if funding_source is not None else []
        )
        for item in funding_sources:
            funding_source_URI = URIRef(
                "http://openenergy-platform.org/ontology/oekg/" + item["iri"]
            )
            new_bundle.add((study_URI, OEO.OEO_00000509, funding_source_URI))

        if abstract != "":
            new_bundle.add((study_URI, DC.abstract, Literal(remove_non_printable(abstract))))

        contact_persons = (
            json.loads(contact_person) if contact_person is not None else []
        )
        for item in contact_persons:
            contact_person_URI = URIRef(
                "http://openenergy-platform.org/ontology/oekg/" + item["iri"]
            )
            new_bundle.add((study_URI, OEO.OEO_00000508, contact_person_URI))

        _sector_divisions = (
            json.loads(sector_divisions) if sector_divisions is not None else []
        )
        for item in _sector_divisions:
            sector_divisions_URI = URIRef(item["class"])
            new_bundle.add(
                (study_URI, OEO["based_on_sector_division"], sector_divisions_URI)
            )

        _sectors = json.loads(sectors) if sectors is not None else []
        for item in _sectors:
            sector_URI = URIRef(item["class"])
            new_bundle.add((study_URI, OEO.OEO_00000505, sector_URI))

        _technologies = json.loads(technologies) if technologies is not None else []
        for item in _technologies:
            technology_URI = URIRef(item["class"])
            new_bundle.add((study_URI, OEO.OEO_00000522, technology_URI))

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
                "http://openenergy-platform.org/ontology/oekg/models/" + str(model_id)
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
                    OEO["has_iri"],
                    Literal(model_url),
                )
            )

            new_bundle.add((study_URI, OEO["has_model"], model_URI))

            # remove old labels
            # iterate to make sure only current selection is available
            for _s, _p, _o in oekg.triples((model_URI, RDFS.label, None)):
                oekg.remove((_s, _p, _o))

            # remove old iri´s
            # iterate to make sure only current selection is available
            for _s, _p, _o in oekg.triples((model_URI, OEO["has_iri,"], None)):
                oekg.remove((_s, _p, _o))

        # TODO: Fix
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
                "http://openenergy-platform.org/ontology/oekg/frameworks/"
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
                        OEO["has_iri"],
                        Literal(framework_url),
                    )
                )

            new_bundle.add((study_URI, OEO["has_framework"], framework_URI))

            # remove old labels
            # iterate to make sure only current selection is available
            for _s, _p, _o in oekg.triples((framework_URI, RDFS.label, None)):
                oekg.remove((_s, _p, _o))

            # remove old iri´s
            # iterate to make sure only current selection is available
            for _s, _p, _o in oekg.triples((framework_URI, OEO["has_iri,"], None)):
                oekg.remove((_s, _p, _o))

        _study_keywords = (
            json.loads(study_keywords) if study_keywords is not None else []
        )
        for keyword in _study_keywords:
            new_bundle.add((study_URI, OEO["has_study_keyword"], Literal(keyword)))

        iso_old_bundle = to_isomorphic(old_bundle)
        iso_new_bundle = to_isomorphic(new_bundle)

        in_both, in_first, in_second = graph_diff(iso_old_bundle, iso_new_bundle)

        in_first_json = str(in_first.serialize(format="json-ld"))  # noqa
        in_second_json = str(in_second.serialize(format="json-ld"))  # noqa

        # remove old bundle from oekg
        for s, p, o in oekg.triples((study_URI, OEKG["has_scenario"], None)):
            oekg.remove((o, None, None))
        oekg.remove((study_URI, None, None))

        for s, p, o in oekg.triples((study_URI, OEKG["has_scenario"], None)):
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
        # OEKG_Modifications_instance.save()

        response = JsonResponse(
            "factsheet updated!", safe=False, content_type="application/json"
        )
        patch_response_headers(response, cache_timeout=1)
        return response


def is_logged_in(request, *args, **kwargs):
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


def factsheet_by_name(request, *args, **kwargs):
    name = request.GET.get("name")
    factsheet = Factsheet.objects.get(name=name)  # noqa
    factsheet_json = serializers.serialize("json", factsheet)
    response = JsonResponse(factsheet_json, safe=False, content_type="application/json")
    patch_response_headers(response, cache_timeout=1)
    return response


def factsheet_by_id(request, *args, **kwargs):
    """
    Returns a scenario bundle based based on the provided ID.

    Args:
        request (HttpRequest): The incoming HTTP GET request.
        id (str): The unique ID for the bundle.
    """

    uid = request.GET.get("id")
    study_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + uid)
    factsheet = {}

    acronym = ""
    study_name = ""
    abstract = ""

    for s, p, o in oekg.triples((study_URI, DC.acronym, None)):
        acronym = o

    for s, p, o in oekg.triples((study_URI, OEKG["has_full_name"], None)):
        study_name = o

    for s, p, o in oekg.triples((study_URI, DC.abstract, None)):
        abstract = o

    factsheet["acronym"] = acronym
    factsheet["uid"] = uid
    factsheet["study_name"] = study_name
    factsheet["abstract"] = abstract
    factsheet["publications"] = []

    factsheet["funding_sources"] = []
    for s, p, o in oekg.triples((study_URI, OEO.OEO_00000509, None)):
        label = oekg.value(o, RDFS.label)
        if label != None:  # noqa
            factsheet["funding_sources"].append(
                {"iri": str(o).split("/")[-1], "id": label, "name": label}
            )

    factsheet["institution"] = []
    for s, p, o in oekg.triples((study_URI, OEO.OEO_00000510, None)):
        label = oekg.value(o, RDFS.label)
        if label != None:  # noqa
            factsheet["institution"].append(
                {"iri": str(o).split("/")[-1], "id": label, "name": label}
            )

    factsheet["contact_person"] = []
    for s, p, o in oekg.triples((study_URI, OEO.OEO_00000508, None)):
        label = oekg.value(o, RDFS.label)
        if label != None:  # noqa
            factsheet["contact_person"].append(
                {"iri": str(o).split("/")[-1], "id": label, "name": label}
            )

    factsheet["sector_divisions"] = []
    for s, p, o in oekg.triples((study_URI, OEO["based_on_sector_division"], None)):
        label = oeo.value(o, RDFS.label)
        class_iri = o
        if label != None:  # noqa
            factsheet["sector_divisions"].append(
                {"value": label, "name": label, "class": class_iri}
            )

    factsheet["sectors"] = []
    for s, p, o in oekg.triples((study_URI, OEO.OEO_00000505, None)):
        label = oeo.value(o, RDFS.label)
        class_iri = o
        if label != None:  # noqa
            factsheet["sectors"].append(
                {"value": label, "label": label, "class": class_iri}
            )

    # factsheet['energy_carriers'] = []
    # for s, p, o in oekg.triples(( study_URI, OEO["covers_energy_carrier"], None )):
    #     label = oeo.value(o, RDFS.label)
    #     class_label = oeo.value(o, RDFS.label)
    #     if label != None:
    #         factsheet['energy_carriers'].append({ "value": label, "label":label, "class": o }) # noqa: E501

    # factsheet['energy_transformation_processes'] = []
    # for s, p, o in oekg.triples(( study_URI, OEO["covers_transformation_processes"], None )): # noqa: E501
    #     label = oeo.value(o, RDFS.label)
    #     if label != None:
    #         factsheet['energy_transformation_processes'].append({ "value": label, "label":label, "class": o }) # noqa: E501

    factsheet["technologies"] = []
    for s, p, o in oekg.triples((study_URI, OEO.OEO_00000522, None)):
        label = oeo.value(o, RDFS.label)
        if label != None:  # noqa
            factsheet["technologies"].append(
                {"value": label, "label": label, "class": o}
            )

    factsheet["study_keywords"] = []
    for s, p, o in oekg.triples((study_URI, OEO["has_study_keyword"], None)):
        if o != None:  # noqa
            factsheet["study_keywords"].append(o)

    factsheet["models"] = []
    factsheet["frameworks"] = []

    for _, _, o in oekg.triples((study_URI, OEO["has_framework"], None)):
        for _, _, o1 in oekg.triples((o, OEO["has_iri"], None)):
            framework_id = int(str(o).split("/")[-1])
            framework_metadata = get_framework_metadata_by_id(
                framework_id, "energyframework"
            )

            if framework_metadata:
                framework_metadata["url"] = str(o1)
                factsheet["frameworks"].append(framework_metadata)

    for _, _, o in oekg.triples((study_URI, OEO["has_model"], None)):
        for _, _, o1 in oekg.triples((o, OEO["has_iri"], None)):
            model_id = int(str(o).split("/")[-1])
            model_metadata = get_model_metadata_by_id(model_id, "energymodel")

            if model_metadata:
                model_metadata["url"] = str(o1)
                factsheet["models"].append(model_metadata)

    temp = set()
    factsheet["publications"] = []
    for s, p, o in oekg.triples((study_URI, OEKG["has_publication"], None)):
        publication = {}

        publication["report_title"] = ""
        label = oekg.value(o, RDFS.label)
        if label is not None:
            publication["report_title"] = label

        publication_uuid = oekg.value(o, OEKG["publication_uuid"])
        publication["id"] = publication_uuid

        publication["authors"] = []
        for s1, p1, o1 in oekg.triples((o, OEO.OEO_00000506, None)):
            o1_label = oekg.value(o1, RDFS.label)
            publication["authors"].append({"iri": o1, "name": o1_label})

        publication["doi"] = ""
        for s2, p2, o2 in oekg.triples((o, OEKG["doi"], None)):
            publication["doi"] = o2

        publication["date_of_publication"] = ""
        for s3, p3, o3 in oekg.triples((o, OEKG["date_of_publication"], None)):
            publication["date_of_publication"] = serialize_publication_date(str(o3))
            temp.update(serialize_publication_date(str(o3)))

        # Convert set to list before creating the JSON response
        factsheet["collected_scenario_publication_dates"] = list(temp)

        publication["link_to_study_report"] = ""
        for s4, p4, o4 in oekg.triples((o, OEKG["link_to_study_report"], None)):
            publication["link_to_study_report"] = o4

        factsheet["publications"].append(publication)

    factsheet["scenarios"] = []
    for s, p, o in oekg.triples((study_URI, OEKG["has_scenario"], None)):
        scenario = {}
        label = oekg.value(o, RDFS.label)
        scenario_uuid = oekg.value(o, OEKG["scenario_uuid"])

        if label != None:  # noqa
            scenario["acronym"] = label

        scenario["id"] = scenario_uuid
        scenario["scenario_years"] = []
        scenario["regions"] = []
        scenario["interacting_regions"] = []
        scenario["descriptors"] = []
        scenario["input_datasets"] = []
        scenario["output_datasets"] = []

        abstract = oekg.value(o, DC.abstract)
        name = oekg.value(o, OEKG["has_full_name"])
        scenario["name"] = name
        scenario["abstract"] = abstract

        for s1, p1, o1 in oekg.triples((o, OEO.OEO_00020220, None)):
            o1_type = oekg.value(o1, RDF.type)
            o1_label = oekg.value(o1, RDFS.label)
            scenario["regions"].append({"iri": o1, "name": o1_label})

        for s1, p1, o1 in oekg.triples((o, OEO.OEO_00020222, None)):
            o1_type = oekg.value(o1, RDF.type)  # noqa
            o1_label = oekg.value(o1, RDFS.label)
            scenario["interacting_regions"].append(
                {"iri": str(o1).split("/")[-1], "id": o1_label, "name": o1_label}
            )

        for s11, p11, o11 in oekg.triples((o, OEO["has_scenario_descriptor"], None)):
            label = oeo.value(o11, RDFS.label)
            scenario["descriptors"].append(
                {"value": label, "label": label, "class": o11}
            )

        for s2, p2, o2 in oekg.triples((o, OEO.RO_0002233, None)):
            o2_iri = oekg.value(o2, OEO["has_iri"])
            o2_label = oekg.value(o2, RDFS.label)
            o2_key = oekg.value(o2, OEO["has_key"])
            o2_idx = oekg.value(o2, OEO["has_id"])

            scenario["input_datasets"].append(
                {
                    "key": o2_key,
                    "idx": o2_idx,
                    "value": {"label": o2_label, "url": o2_iri},
                }
            )

        for s3, p3, o3 in oekg.triples((o, OEO.RO_0002234, None)):
            o3_iri = oekg.value(o3, OEO["has_iri"])
            o3_label = oekg.value(o3, RDFS.label)
            o3_key = oekg.value(o3, OEO["has_key"])
            o3_idx = oekg.value(o3, OEO["has_id"])

            scenario["output_datasets"].append(
                {
                    "key": o3_key,
                    "idx": o3_idx,
                    "value": {"label": o3_label, "url": o3_iri},
                }
            )

        for s4, p4, o4 in oekg.triples((o, OEO.OEO_00020224, None)):
            scenario["scenario_years"].append({"id": o4, "name": o4})

        factsheet["scenarios"].append(scenario)

    response = JsonResponse(factsheet, safe=False, content_type="application/json")
    patch_response_headers(response, cache_timeout=1)

    scenario_region = URIRef(
        "http://openenergy-platform.org/ontology/oekg/region/Germany"
    )
    for s, p, o in oekg.triples((scenario_region, RDFS.label, None)):
        if str(o) == "None":
            oekg.remove((s, p, o))
            oekg.add((s, p, Literal("Germany")))

    return response


#@login_required
def query_oekg(request, *args, **kwargs):
    """
    This function takes filter objects provided by the user and utilises
    them to construct a SPARQL query.

    Args:
        request (HttpRequest): The incoming HTTP GET request.
        criteria (str): An object that contains institutions, authors,
        funding sources, start date of the publications, end date of publications
        study descriptors, and a range for scenario years. All of these fields
        are utilised to construct a SPARQL query for execution on the OEKG.

    """
    request_body = json.loads(request.body)
    criteria = request_body["criteria"]

    institutes_list = criteria["institutions"]
    authors_list = criteria["authors"]
    funding_sources_list = criteria["fundingSource"]
    publication_date_start_value = criteria["startDateOfPublication"]
    publication_date_end_value = criteria["endDateOfPublication"]
    study_keywords_list = criteria["studyKewords"]
    scenario_year_start_value = criteria["scenarioYearValue"][0]
    scenario_year_end_value = criteria["scenarioYearValue"][1]

    query_structure = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX RDFS: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX OEO: <http://openenergy-platform.org/ontology/oeo/>
        PREFIX OEKG: <http://openenergy-platform.org/ontology/oekg/>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        PREFIX DC: <http://purl.org/dc/terms/>

        SELECT DISTINCT ?study_acronym
        WHERE
        {{
        ?s  DC:acronym ?study_acronym .
        
        {funding_sources_exp}
        {study_descriptors_exp}
        {institutes_exp}

        ?s OEKG:has_publication ?publication .
        ?publication OEKG:date_of_publication ?publication_date .

        {authors_exp}

        FILTER ((?institutes IN ({institutes}) )
        || (?authors IN ({authors}) )
        || (?funding_sources IN ({funding_sources}) )
        || (?publication_date >= "{publication_date_start}" && ?publication_date <= "{publication_date_end}")
        || (?study_keywords IN ({study_keywords}) ) )

        }}"""  # noqa: E501
    
    authors_exp = '?publication OEO:OEO_00000506 ?authors .' if authors_list != [] else ''
    funding_sources_exp = '?s OEO:OEO_00000509 ?funding_sources .' if funding_sources_list != [] else ''
    study_descriptors_exp = '?s OEO:has_study_keyword ?study_keywords .' if study_keywords_list != [] else ''
    institutes_exp = '?s OEO:OEO_00000510 ?institutes .' if institutes_list != [] else ''

    final_query = query_structure.format(
        institutes=str(institutes_list)
        .replace("[", "")
        .replace("]", "")
        .replace("'", ""),
        authors=str(authors_list).replace("[", "").replace("]", "").replace("'", ""),
        funding_sources=str(funding_sources_list)
        .replace("[", "")
        .replace("]", "")
        .replace("'", ""),
        publication_date_start=publication_date_start_value,
        publication_date_end=publication_date_end_value,
        study_keywords=str(study_keywords_list).replace("[", "").replace("]", ""),
        scenario_year_start=scenario_year_start_value,
        scenario_year_end=scenario_year_end_value,
        funding_sources_exp= funding_sources_exp,
        study_descriptors_exp=study_descriptors_exp,
        institutes_exp=institutes_exp,
        authors_exp=authors_exp,
    )

    print(final_query)
    sparql.setReturnFormat(JSON)
    sparql.setQuery(final_query)
    results = sparql.query().convert()

    response = JsonResponse(
        results["results"]["bindings"],
        safe=False,
        content_type="application/json",
    )
    return response


@only_if_user_is_owner_of_scenario_bundle
@login_required
def delete_factsheet_by_id(request, *args, **kwargs):
    """
    Removes a scenario bundle based on the provided ID.

    Args:
        request (HttpRequest): The incoming HTTP GET request.
        id (str): The unique ID for the bundle.

    """
    id = request.GET.get("id")
    study_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + id)

    for s, p, o in oekg.triples((study_URI, OEKG["has_scenario"], None)):
        oekg.remove((o, None, None))
    oekg.remove((study_URI, None, None))

    response = JsonResponse(
        "factsheet removed!", safe=False, content_type="application/json"
    )
    patch_response_headers(response, cache_timeout=1)
    return response


def test_query(request, *args, **kwargs):
    scenario_region = URIRef(
        "http://openenergy-platform.org/ontology/oekg/region/UnitedKingdomOfGreatBritainAndNorthernIreland"  # noqa: E501
    )
    for s, p, o in oekg.triples((scenario_region, RDFS.label, None)):
        if str(o) == "None":
            oekg.remove((s, p, o))
    response = JsonResponse("Done!", safe=False, content_type="application/json")
    patch_response_headers(response, cache_timeout=1)
    return response


def get_entities_by_type(request, *args, **kwargs):
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
        prefix = "http://openenergy-platform.org/ontology/oeo/"
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
def add_entities(request, *args, **kwargs):
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
        prefix = "http://openenergy-platform.org/ontology/oeo/"
    if vocab == "OBO":
        prefix = "http://purl.obolibrary.org/obo/"

    entity_type_URI = URIRef(prefix + classId)

    entity_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + entity_iri)

    oekg.add((entity_URI, RDF.type, entity_type_URI))
    oekg.add((entity_URI, RDFS.label, Literal(entity_label)))

    response = JsonResponse(
        "A new entity added!", safe=False, content_type="application/json"
    )
    patch_response_headers(response, cache_timeout=1)
    return response


@login_required
def add_a_fact(request, *args, **kwargs):
    request_body = json.loads(request.body)
    _subject = request_body["subject"]
    _predicate = request_body["predicate"]
    _object = request_body["object"]

    _subject_URI = URIRef(
        "http://openenergy-platform.org/ontology/oekg/" + clean_name(_subject)
    )
    _predicate_URI = URIRef(
        "http://openenergy-platform.org/ontology/oeo/" + clean_name(_predicate)
    )
    _object_URI = URIRef(
        "http://openenergy-platform.org/ontology/oekg/" + clean_name(_object)
    )

    oekg.add((_subject_URI, _predicate_URI, _object_URI))

    response = JsonResponse(
        "A new fact added!", safe=False, content_type="application/json"
    )
    patch_response_headers(response, cache_timeout=1)
    return response


@login_required
def delete_entities(request, *args, **kwargs):
    """
    Removes an entity from OEKG. The minimum requirements for
    removing an entity are the type and label.

    Args:
        request (HttpRequest): The incoming HTTP GET request.
        entity_type (str): The type(OEO class) of the entity.
        entity_label (str): The label of the entity.
    """
    entity_type = request.GET.get("entity_type")
    entity_label = request.GET.get("entity_label")

    entity_URI = URIRef(  # noqa
        "http://openenergy-platform.org/ontology/oekg/" + entity_type
    )
    entity_Label = URIRef(
        "http://openenergy-platform.org/ontology/oekg/" + (entity_label)
    )

    oekg.remove((entity_Label, None, None))
    oekg.remove((None, None, entity_Label))
    response = JsonResponse(
        "entity removed!", safe=False, content_type="application/json"
    )
    patch_response_headers(response, cache_timeout=1)
    return response


@login_required
def update_an_entity(request, *args, **kwargs):
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
        prefix = "http://openenergy-platform.org/ontology/oeo/"
    if vocab == "OBO":
        prefix = "http://purl.obolibrary.org/obo/"

    entity_type_URI = URIRef(prefix + classId)  # noqa
    entity_IRI = URIRef("http://openenergy-platform.org/ontology/oekg/" + (entity_id))

    oekg.add((entity_IRI, RDFS.label, Literal(new_entity_label)))
    oekg.remove((entity_IRI, RDFS.label, Literal(entity_label)))

    response = JsonResponse(
        "entity updated!", safe=False, content_type="application/json"
    )
    patch_response_headers(response, cache_timeout=1)
    return response


def get_all_factsheets(request, *args, **kwargs):
    all_factsheets = []
    for s, p, o in oekg.triples((None, RDF.type, OEO.OEO_00010252)):
        uid = str(s).split("/")[-1]
        element = {}
        acronym = remove_non_printable(oekg.value(s, DC.acronym))
        study_name = remove_non_printable(oekg.value(s, OEKG["has_full_name"]))
        abstract = oekg.value(s, DC.abstract)
        element["uid"] = uid
        element["acronym"] = remove_non_printable(acronym) if acronym != None else ""  # noqa
        element["study_name"] = remove_non_printable(study_name) if study_name != None else ""  # noqa
        element["abstract"] = remove_non_printable(abstract) if abstract != None else ""  # noqa
        study_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + uid)
        element["institutions"] = []
        for s, p, o in oekg.triples((study_URI, OEO.OEO_00000510, None)):
            label = oekg.value(o, RDFS.label)
            if label != None:  # noqa
                element["institutions"].append(remove_non_printable(label))

        element["funding_sources"] = []
        for s, p, o in oekg.triples((study_URI, OEO.OEO_00000509, None)):
            label = oekg.value(o, RDFS.label)
            if label != None:  # noqa
                element["funding_sources"].append(remove_non_printable(label))

        element["models"] = []
        for s, p, o in oekg.triples((study_URI, OEO["has_model"], None)):
            if o != None:  # noqa
                label = oekg.value(o, RDFS.label)
                if label:
                    element["models"].append(remove_non_printable(label))

        element["frameworks"] = []
        for s, p, o in oekg.triples((study_URI, OEO["has_framework"], None)):
            if o != None:  # noqa
                label = oekg.value(o, RDFS.label)
                if label is not None:
                    element["frameworks"].append(remove_non_printable(label))
                else:
                    pass

        temp = set()
        for s, p, o in oekg.triples((s, OEKG["has_publication"], None)):
            pubs_per_bundle = []
            for s1, p1, o1 in oekg.triples((o, OEKG["date_of_publication"], None)):
                if o1:
                    pubs_per_bundle.append(serialize_publication_date(str(remove_non_printable(o1))))

            if pubs_per_bundle:
                temp.update(pubs_per_bundle)

        # Convert set to list before creating the JSON response
        element["collected_scenario_publication_dates"] = list(temp)

        element["scenarios"] = []
        for s, p, o in oekg.triples((study_URI, OEKG["has_scenario"], None)):
            label = oekg.value(o, RDFS.label)
            abstract = oekg.value(o, DC.abstract)
            full_name = oekg.value(o, OEKG.has_full_name)
            uid = oekg.value(o, OEKG.scenario_uuid)

            if label != None:  # noqa
                element["scenarios"].append(
                    {
                        "label": remove_non_printable(label),
                        "abstract": remove_non_printable(abstract),
                        "full_name": remove_non_printable(full_name),
                        "uid": uid,
                    }
                )

        all_factsheets.append(element)

    response = JsonResponse(all_factsheets, safe=False, content_type="application/json")
    patch_response_headers(response, cache_timeout=1)
    return response


def search_scenario_type_iris_by_label(label, input):
    for child in input:
        result = None

        if str(child["label"]) == label:
            result = str(child["iri"])
            return result

        elif child.get("children"):
            result = search_scenario_type_iris_by_label(label, child["children"])
            if result:
                return result
    return result


def get_scenario_type_iri(scenario_type_label: str):
    scenario_class = oeo_owl.search_one(
        iri="http://openenergy-platform.org/ontology/oeo/OEO_00000364"
    )
    scenario_subclasses = get_all_sub_classes(scenario_class)

    result = search_scenario_type_iris_by_label(
        label=scenario_type_label, input=scenario_subclasses["children"]
    )

    return result


def get_scenarios(request, *args, **kwargs):
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

            for s1, p1, o1 in oekg.triples((s, OEO["has_scenario_descriptor"], None)):
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

            for s4, p4, o4 in oekg.triples((s, OEO.OEO_00020224, None)):
                scenario_years.append(o4)
            for s5, p5, o5 in oekg.triples((s, OEO.RO_0002233, None)):
                oekg_value = oekg.value(o5, OEO["has_iri"])
                comparable = str(oekg_value).split("scenario/")
                input_datasets.append(
                    (
                        oekg.value(o5, RDFS.label),
                        oekg.value(o5, OEO["has_iri"]),
                        comparable[1],
                    )
                )
            for s6, p6, o6 in oekg.triples((s, OEO.RO_0002234, None)):
                oekg_value = oekg.value(o6, OEO["has_iri"])
                comparable = str(oekg_value).split("scenario/")

                output_datasets.append(
                    (
                        oekg.value(o6, RDFS.label),
                        oekg.value(o6, OEO["has_iri"]),
                        comparable[1],
                    )
                )

            for s1, p1, o1 in oekg.triples((None, OEKG["has_scenario"], s)):
                study_label = oekg.value(s1, OEKG["has_full_name"])
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
def get_all_factsheets_as_turtle(request, *args, **kwargs):
    all_factsheets_as_turtle = oekg.serialize(format="ttl")

    response = HttpResponse(all_factsheets_as_turtle, content_type="text/turtle")
    response["Content-Disposition"] = 'attachment; filename="oekg.ttl"'
    return response


def get_all_factsheets_as_json_ld(request, *args, **kwargs):
    all_factsheets_as_json_ld = oekg.serialize(format="json-ld")

    response = HttpResponse(
        all_factsheets_as_json_ld, content_type="application/ld+json"
    )
    response["Content-Disposition"] = 'attachment; filename="oekg.jsonld"'

    return response


def get_all_sub_classes(cls, visited=None):
    if visited is None:
        visited = set()

    visited.add(cls.label.first())
    # "value": cls.label.first(),  "label": cls.label.first(), , "iri": cls.iri

    childCount = len(list(cls.subclasses()))
    subclasses = cls.subclasses()

    dict = {
        "name": cls.label.first(),
        "label": cls.label.first(),
        "value": cls.label.first(),
        "iri": cls.iri,
        "definition": oeo.value(OEO[str(cls).split(".")[1]], OBO.IAO_0000115),
    }

    if childCount > 0:
        dict["children"] = [
            get_all_sub_classes(subclass, visited)
            for subclass in subclasses
            if subclass.label.first() not in visited
        ]
    return dict


# @login_required
def populate_factsheets_elements(request, *args, **kwargs):
    scenario_class = oeo_owl.search_one(
        iri="http://openenergy-platform.org/ontology/oeo/OEO_00000364"
    )
    scenario_subclasses = get_all_sub_classes(scenario_class)

    technology_class = oeo_owl.search_one(
        iri="http://openenergy-platform.org/ontology/oeo/OEO_00000407"
    )
    technology_subclasses = get_all_sub_classes(technology_class)

    # energy_carrier_class = oeo_owl.search_one(iri="http://openenergy-platform.org/ontology/oeo/OEO_00020039") # noqa
    # energy_carriers = get_all_sub_classes(energy_carrier_class)

    # energy_transformation_process_class = oeo_owl.search_one(iri="http://openenergy-platform.org/ontology/oeo/OEO_00020003") # noqa
    # energy_transformation_processes = get_all_sub_classes(energy_transformation_process_class) # noqa

    sector_divisions = ["OEO_00010056", "OEO_00000242", "OEO_00010304"]

    sector_divisions_list = []
    sectors_list = []
    for sd in sector_divisions:
        sector_division_URI = URIRef(
            "http://openenergy-platform.org/ontology/oeo/" + sd
        )
        sector_division_label = oeo.value(sector_division_URI, RDFS.label)
        sector_divisions_list.append(
            {
                "class": sector_division_URI,
                "label": sector_division_label,
                "name": sector_division_label,
                "value": sector_division_label,
            }
        )
        for s, p, o in oeo.triples((None, OEO.OEO_00000504, OEO[sd])):
            sector_label = oeo.value(s, RDFS.label)
            sector_difinition = oeo.value(s, OBO.IAO_0000115)
            sectors_list.append(
                {
                    "iri": s,
                    "label": sector_label,
                    "value": sector_label,
                    "sector_division": sector_division_URI,
                    "sector_difinition": sector_difinition,
                }
            )

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
    # table_iri = "dataedit/view/scenario/abbb_emob"

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
        "input_dataset_bundles": input_dataset_bundle_acronyms,
        "output_dataset_bundles": output_dataset_bundle_acronyms,
    }
    html_content = render(
        request, "partials/related_oekg_scenarios.html", context
    ).content.decode("utf-8")

    # Render the template with the context
    return HttpResponse(html_content)
