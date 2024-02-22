from rdflib import RDF, URIRef, Literal


from factsheet.oekg.connection import oekg
from factsheet.oekg import namespaces


class OekgQuery:
    def __init__(self):
        self.oekg = oekg

    def get_related_scenarios_where_table_is_input_dataset(self, table_iri):
        """
        Query the OEKG to get all scenarios that list the current table as
        input dataset.

        Special OEO classes & and relations:
            OEO_00000365 = Scenario factsheet type
            RO_0002233 = has_input relation in the oekg

        Args:
            table_iri(str): IRI of any table in the scenario topic on the OEP.
                            IRI Like 'dataedit/view/scenario/abbb_emob'
        """
        related_scenarios = set()

        # Find scenarios where the given table is the input dataset
        for s, p, o in self.oekg.triples((None, RDF.type, namespaces.OEO.OEO_00000365)):
            for s1, p1, o1_input_ds_uid in self.oekg.triples(
                (s, namespaces.OEO.RO_0002233, None)
            ):
                if o1_input_ds_uid is not None:
                    for s2, p2, o2_input_ds_iri in oekg.triples(
                        (o1_input_ds_uid, namespaces.OEO["has_iri"], Literal(table_iri))
                    ):
                        # if (
                        #     o2_input_ds_iri is not None
                        #     and str(o2_input_ds_iri) == table_iri
                        # ):
                        related_scenarios.add(s)

        return related_scenarios

    def get_related_scenarios_where_table_is_output_dataset(self, table_iri):
        """
        Query the OEKG to get all scenarios that list the current table as
        output dataset.

        Special OEO classes & and relations:
            OEO_00000365 = Scenario factsheet type
            RO_0002234 = has_output relation in the oekg

        Args:
            table_iri(str): IRI of any table in the scenario topic on the OEP.
                            IRI Like 'dataedit/view/scenario/abbb_emob'
        """
        related_scenarios = set()

        # Find scenarios where the given table is the out dataset
        for s, p, o in self.oekg.triples((None, RDF.type, namespaces.OEO.OEO_00000365)):
            for s1, p1, o1_output_ds_uid in self.oekg.triples(
                (s, namespaces.OEO.RO_0002234, None)
            ):
                if o1_output_ds_uid is not None:
                    for s2, p2, o2_input_ds_iri in oekg.triples(
                        (
                            o1_output_ds_uid,
                            namespaces.OEO["has_iri"],
                            Literal(table_iri),
                        )
                    ):
                        # if (
                        #     o2_input_ds_iri is not None
                        #     and str(o2_input_ds_iri) == table_iri
                        # ):
                        related_scenarios.add(s)

        return related_scenarios

    def get_scenario_acronym(self, scenario_uri):
        for s, p, o in self.oekg.triples(
            (scenario_uri, namespaces.RDFS.label, None)
        ):
            return o
