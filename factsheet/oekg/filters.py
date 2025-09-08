# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut # noqa: E501
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from rdflib import RDF, URIRef

from factsheet.oekg import namespaces
from factsheet.oekg.connection import oekg


class OekgQuery:
    def __init__(self):
        self.oekg = oekg

    def serialize_table_iri(self, table_iri: str):
        """
        The OEKG stores the full iri to link its resources in the OEP.
        External IRI can occur in the OEKG but they are ignored here.

        Note:
            Due to structural changes it also stores the iri:urn instead.
            the serialization will function als a validation preprocessing
            step.

        Supported IRI formats:
            IRI Like 'dataedit/view/scenario/abbb_emob' or '
            https://openenergyplatform.org/dataedit/view/scenario/abbb_emob'
            becomes comparable even with more variation options.


        """

        # Trim down variations of table iri´s down to harmonized part.
        id_from_url = table_iri.split("view/")
        # check if the table_iri contains expected part
        if len(id_from_url) == 2:
            result = id_from_url[1]
        else:
            # return empty string to keep the return value consistent
            result = ""

        return result

    def get_related_scenarios_where_table_is_input_dataset(self, table_iri):
        """
        Query the OEKG to get all scenarios that list the current table as
        input dataset.

        Special OEO classes & and relations:
            OEO_00020227 = Scenario Bundle
            OEO_00000365 = Scenario factsheet type (IS STILL IN USE ???)
            OEO_00020437 = has_input relation in the oekg

        Args:
            table_iri(str): IRI of any table in the scenario topic on the OEP.
                            IRI Like 'dataedit/view/scenario/abbb_emob'
        """
        related_scenarios = set()
        table_iri = self.serialize_table_iri(table_iri)

        for s, _, _ in self.oekg.triples((None, RDF.type, namespaces.OEO.OEO_00020227)):
            # Correct BFO namespace here:
            for _, _, part in self.oekg.triples((s, namespaces.OBO.BFO_0000051, None)):
                # Only scenarios have inputs; cheap pre-check (optional)
                # if (part, RDF.type, namespaces.OEO.OEO_00000365) not in self.oekg:
                #     continue
                for subj, _, ds in self.oekg.triples(
                    (part, namespaces.OEO.OEO_00020437, None)
                ):
                    # ds is the dataset node; compare its IRI/url property
                    for _, _, ds_iri in self.oekg.triples(
                        (ds, namespaces.OEO.OEO_00390094, None)
                    ):
                        if self.serialize_table_iri(str(ds_iri)) == table_iri:
                            related_scenarios.add(subj)

        return related_scenarios

    def get_related_scenarios_where_table_is_output_dataset(self, table_iri):
        """
        Query the OEKG to get all scenarios that list the current table as
        output dataset.

        Special OEO classes & and relations:
            OEO_00000365 = Scenario factsheet type
            OEO_00020436 = has_output relation in the oekg

        Args:
            table_iri(str): IRI of any table in the scenario topic on the OEP.
                            IRI Like 'dataedit/view/scenario/abbb_emob'
        """
        related_scenarios = set()
        table_iri = self.serialize_table_iri(table_iri)

        # Find all scenario bundles
        for s, _, _ in self.oekg.triples((None, RDF.type, namespaces.OEO.OEO_00020227)):
            for _, _, part in self.oekg.triples(
                (s, namespaces.OBO.BFO_0000051, None)
            ):  # FIX
                for subj, _, ds in self.oekg.triples(
                    (part, namespaces.OEO.OEO_00020436, None)
                ):
                    for _, _, ds_iri in self.oekg.triples(
                        (ds, namespaces.OEO.OEO_00390094, None)
                    ):
                        if self.serialize_table_iri(str(ds_iri)) == table_iri:
                            related_scenarios.add(subj)

        return related_scenarios

    def get_scenario_acronym(self, scenario_uri):
        """
        Currently not in use.
        Can be used to get the scenario acronym from scenario
        uid.
        """
        for s, p, o in self.oekg.triples((scenario_uri, namespaces.RDFS.label, None)):
            return o

    def get_scenario_bundles_where_table_is_input(self, table_iri):
        """
        Query the OEKG to get all scenarios that list the current table as
        input dataset.

        Specific OEO classes & and relations:
            OEO_00020227 = Scenario Bundle
            OEO_00000365 = Scenario factsheet type
            OEO_00020437 = has_input relation in the oekg

        Args:
            table_iri(str): IRI of any table in the scenario topic on the OEP.
                            IRI Like 'dataedit/view/scenario/abbb_emob'
        """
        related_scenarios_input = (
            self.get_related_scenarios_where_table_is_input_dataset(table_iri=table_iri)
        )

        scenario_bundles_input = set()

        for bundle, _, _ in self.oekg.triples(
            (None, RDF.type, namespaces.OEO.OEO_00020227)
        ):
            for scen in related_scenarios_input:
                for s1, _, _ in self.oekg.triples(
                    (bundle, namespaces.OBO.BFO_0000051, scen)
                ):
                    if s1:
                        scenario_bundles_input.add((s1, bundle))

        return scenario_bundles_input

    def get_scenario_bundles_where_table_is_output(self, table_iri):
        """
        Query the OEKG to get all scenario bundles that list the current table as
        output dataset.

        Special OEO classes & and relations:
            OEO_00000365 = Scenario factsheet type
            OEO_00020436 = has_output relation in the oekg

        Args:
            table_iri(str): IRI of any table in the scenario topic on the OEP.
                            IRI Like 'dataedit/view/scenario/abbb_emob'
        """

        related_scenarios_output = (
            self.get_related_scenarios_where_table_is_output_dataset(
                table_iri=table_iri
            )
        )
        scenario_bundles_output = set()

        for bundle, _, _ in self.oekg.triples(
            (None, RDF.type, namespaces.OEO.OEO_00020227)
        ):
            for scen in related_scenarios_output:
                for s1, _, _ in self.oekg.triples(
                    (bundle, namespaces.OBO.BFO_0000051, scen)
                ):
                    if s1:
                        scenario_bundles_output.add((s1, bundle))

        return scenario_bundles_output

    def get_bundle_acronym(self, bundle_uri):
        acronym = self.oekg.value(bundle_uri, namespaces.DC.acronym, None)
        return acronym

    def get_bundle_uid(self, bundle):
        """
        Retrieves the uid related to the scenario bundle.

        Note: Currently the OEKG does not contain a relation between uid
        and bundle iri. That is why we have to strip it from the url.
        """

        uid = bundle.split("/")[-1]
        return uid

    def get_bundle_study_descriptors_where_scenario_is_part_of(self, scenario_uid):
        scenario_URI = URIRef(
            "https://openenergyplatform.org/ontology/oekg/scenario/" + scenario_uid
        )
        study_descriptors: list = []

        # find bundle for the current scenario
        for s1, p1, o1 in self.oekg.triples(
            (None, namespaces.OEO.BFO_0000051, scenario_URI)
        ):
            # find all study descriptors for the scenario bundle
            for s2, p2, o2 in oekg.triples((s1, namespaces.OEO.OEO_00390071, None)):
                if o2 != None:  # noqa
                    study_descriptors.append(o2)

        return study_descriptors
