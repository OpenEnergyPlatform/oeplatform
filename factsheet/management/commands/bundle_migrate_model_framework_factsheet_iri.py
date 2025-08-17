# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut # noqa: E501
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from django.core.management.base import BaseCommand
from rdflib import RDF, Literal, URIRef

from factsheet.oekg.connection import oekg_with_namespaces as oekg
from factsheet.oekg.namespaces import OEO, RDFS
from modelview.utils import get_framework_metadata_by_name, get_model_metadata_by_name


class Command(BaseCommand):
    def handle(self, *args, **options):
        for s, p, o in oekg.triples((None, RDF.type, OEO.OEO_00010252)):
            for s, p, o in oekg.triples((s, OEO.BFO_0000051, None)):
                if not str(o).startswith("<http://openenergy-"):
                    framework_meta = get_framework_metadata_by_name(
                        str(o), "energyframework"
                    )

                    if framework_meta:
                        framework_URI = URIRef(
                            "http://openenergy-platform.org/ontology/oekg/frameworks/"
                            + str(framework_meta["id"])
                        )

                        oekg.add((s, p, framework_URI))

                        if framework_meta.get("acronym"):
                            oekg.add(
                                (
                                    framework_URI,
                                    RDFS.label,
                                    Literal(framework_meta["acronym"]),
                                )
                            )
                        else:
                            oekg.add(
                                (
                                    framework_URI,
                                    RDFS.label,
                                    Literal(framework_meta["name"]),
                                )
                            )

                        oekg.add(
                            (
                                framework_URI,
                                OEO.OEO_00390094,
                                Literal(framework_meta["urn"]),
                            )
                        )

                        oekg.remove((s, p, o))
                        print(
                            f"In bundle {s} updated framework {str(o)} with {framework_URI}"  # noqa
                        )

            for s, p, o in oekg.triples((s, OEO.BFO_0000051, None)):
                if not str(o).startswith("<http://openenergy-"):
                    model_meta = get_model_metadata_by_name(str(o), "energymodel")

                    if model_meta:
                        model_URI = URIRef(
                            "http://openenergy-platform.org/ontology/oekg/models/"
                            + str(model_meta["id"])
                        )

                        oekg.add((s, p, model_URI))

                        if model_meta.get("acronym"):
                            oekg.add(
                                (model_URI, RDFS.label, Literal(model_meta["acronym"]))
                            )
                        else:
                            oekg.add(
                                (model_URI, RDFS.label, Literal(model_meta["name"]))
                            )

                        oekg.add(
                            (model_URI, OEO.OEO_00390094, Literal(model_meta["urn"]))
                        )

                        oekg.remove((s, p, o))

                        print(f"In bundle {s} updated model {str(o)} with {model_URI}")
