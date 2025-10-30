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

from rdflib import Graph, URIRef

from factsheet.models import ScenarioBundleAccessControl
from factsheet.oekg.connection import oekg, oeo, oeo_owl
from factsheet.oekg.namespaces import OBO, OEO, RDFS, SKOS, bind_all_namespaces

# TODO: Refactor code to usage of constants below
# Collection of constants to easy DX:
# used to ease code readability, not used cosistently yet
# OEO classes for parts
OEO_SCENARIO = OEO.OEO_00000365  # scenario factsheet
OEO_PUBLICATION = OEO.OEO_00020012  # study report
OEO_MODEL = OEO.OEO_00000277  # model factsheet
OEO_FRAMEWORK = OEO.OEO_00000172  # framework factsheet

# Common props (you already use these elsewhere)
HAS_PART = OBO.BFO_0000051
PUB_UID = OEO.OEO_00390095
PUB_DATE = OEO.OEO_00390096
PUB_DOI = OEO.OEO_00390098
PUB_LINK = OEO.OEO_00390078
PUB_AUTHOR = OEO.OEO_00000506

SCENARIO_YEAR = OEO.OEO_00020440
SCENARIO_REGION = OEO.OEO_00020220
SCENARIO_INTERREG = OEO.OEO_00020222
SCENARIO_DESCRIPTOR = OEO.OEO_00390073

SECTOR_DIVISION = OEO.OEO_00390079
SECTOR = OEO.OEO_00020439
TECHNOLOGY = OEO.OEO_00020438
INSTITUTION_PROP = OEO.OEO_00000510
FUNDING_PROP = OEO.OEO_00000509

HAS_URL_OR_IRI = (
    OEO.OEO_00390094
)  # landing URL on model/framework/scenario/publication nodes (present in your TTL)


PROP_DEFINED_BY = URIRef(
    "https://openenergyplatform.org/ontology/oeo/OEO_00000504"
)  # "is defined by"
PROP_DEFINITION = URIRef("http://purl.obolibrary.org/obo/IAO_0000115")
SECTOR_DEVISIONS = [OEO.OEO_00010056, OEO.OEO_00000242, OEO.OEO_00010304]
PROP_DEFINITION = URIRef("http://purl.obolibrary.org/obo/IAO_0000115")


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


def set_ownership(bundle_uid, user):
    model = ScenarioBundleAccessControl()
    model.owner_user = user
    model.bundle_id = bundle_uid
    model.save()
    return f"The ownership of bundle {bundle_uid} is now set to User {user.name}"


def is_owner(user, bundle_id):
    return ScenarioBundleAccessControl.user_has_access(user, bundle_id)


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
        iri="https://openenergyplatform.org/ontology/oeo/OEO_00000364"
    )
    scenario_subclasses = get_all_sub_classes(scenario_class)

    result = search_scenario_type_iris_by_label(
        label=scenario_type_label, input=scenario_subclasses["children"]
    )

    return result


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


def _label(g: Graph, node: URIRef):
    lab = g.value(node, RDFS.label)
    return str(lab) if lab else None


def _definition(g: Graph, node: URIRef):
    # Prefer IAO:definition; fall back to SKOS definition or rdfs:comment
    for p in (PROP_DEFINITION, SKOS.definition, RDFS.comment):
        val = g.value(node, p)
        if val:
            return str(val)
    return None


def build_sector_dropdowns_from_oeo(g: Graph):
    sector_divisions_list = []
    sectors_list = []

    for sd in SECTOR_DEVISIONS:
        sd_label = _label(g, sd) or sd.n3(g.namespace_manager)
        sd_def = _definition(g, sd)

        # division dropdown option (+ definition)
        sector_divisions_list.append(
            {
                "class": sd,  # TODO; URIRef; cast to str?
                "label": sd_label,
                "name": sd_label,
                "value": sd_label,
                "sector_division_definition": sd_def,
            }
        )

        # sector individuals: ?sector oeo:is_defined_by ?sd
        for sector in g.subjects(PROP_DEFINED_BY, sd):
            sec_label = _label(g, sector)
            definition = g.value(sector, PROP_DEFINITION)

            sectors_list.append(
                {
                    "iri": sector,
                    "label": sec_label,
                    "value": sec_label,
                    "sector_division": sd,
                    "sector_difinition": (str(definition) if definition else None),
                }
            )

    return sector_divisions_list, sectors_list
