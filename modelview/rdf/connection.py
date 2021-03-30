from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Graph
import uuid

from oeplatform.settings import RDF_DATABASES


class ConnectionContext:
    def __init__(self):
        c = RDF_DATABASES["knowledge"]

        self.connection = SPARQLWrapper(f"http://{c['host']}:{c['port']}/{c['name']}")
        self.connection.setReturnFormat(JSON)

    def update_property(self, subject, property, old_value, new_value):
        s = "DELETE { "
        if old_value:
            s += f"{subject} {property} {old_value}. "
        s += "} INSERT { "
        if old_value:
            s += f"{subject} {property} {new_value}. "
        s += "} WHERE {}"
        return self.execute(s)

    def insert_new_instance(self, subject, property, factory):
        hash = uuid.uuid4()
        s = "DELETE { } INSERT {"
        s += f"{subject} {property} {hash}. "
        s += f"{hash} a {factory}. "
        s += "} WHERE {}"
        return self.execute(s)

    def execute(self, query):
        print(query)

    def query_all_objects(self, subjects, predicates):
        query = (
            "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n"
            "SELECT ?s ?p ?o ?lo ?lp ?fname WHERE { "
        )
        options = ["?p rdfs:label ?lp .", "?o rdfs:label ?lo"]

        query += " UNION ".join(
            f"""{{ { p.fetch_queries('?s', '?o', options=options, filter=[f'?s = <{s}>'], where=[f'BIND("{fname}" as ?fname )']) } }}"""
            for s in subjects
            for fname, p in predicates
            if p.rdf_name
        )

        query += "}"
        self.connection.setQuery(query)
        return self.connection.query().convert()
