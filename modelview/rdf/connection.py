from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Graph
from modelview.rdf.namespace import OEO_KG
import uuid

from oeplatform.settings import RDF_DATABASES


class ConnectionContext:
    def __init__(self):
        c = RDF_DATABASES["knowledge"]

        self.connection = SPARQLWrapper(f"http://{c['host']}:{c['port']}/{c['name']}")
        self.update_connection = SPARQLWrapper(f"http://{c['host']}:{c['port']}/{c['name']}/update")
        self.connection.setReturnFormat(JSON)

    def update_property(self, subject, property, old_value, new_value, inverse=False):
        s = "DELETE { "
        if old_value:
            if inverse:
                s += f"{old_value} <{property}> {subject}. "
            else:
                s += f"{subject} <{property}> {old_value}. "
        s += "} INSERT { "
        if new_value:
            if inverse:
                s += f"{new_value} <{property}> {subject}. "
            else:
                s += f"{subject} <{property}> {new_value}. "
        s += "} WHERE {}"
        self.execute(s)

    def insert_new_instance(self, subject, property, inverse=False):
        hash = getattr(OEO_KG, str(uuid.uuid4()))
        s = "DELETE { } INSERT {"
        if inverse:
            s += f" <{hash}> <{property}> {subject}. "
        else:
            s += f"{subject} <{property}> <{hash}>. "
        s += "} WHERE {}"
        self.execute(s)
        return hash

    def execute(self, query):
        print(query)
        self.update_connection.setQuery(query)
        response = self.update_connection.query()
        return response

    def query_all_objects(self, subjects, predicates):
        query = (
            "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n"
            "SELECT ?s ?p ?o ?lo ?lp ?fname WHERE { "
        )
        options = ["?p rdfs:label ?lp ."]

        query += " UNION ".join(
            f"""{{ { p.fetch_queries('?s', '?o', options=options+[p._label_option], filter=[f'?s = <{s}>'], where=[f'BIND("{fname}" as ?fname )']) } }}"""
            for s in subjects
            for fname, p in predicates
            if p.rdf_name
        )

        query += "}"
        print(query)
        self.connection.setQuery(query)
        return self.connection.query().convert()

    def get_all_instances(self, cls, subclass=False):
        query = (
            "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n" +
            "SELECT ?s ?l WHERE { " +
            f"?s {'rdfs:subClassOf' if subclass else 'a'} <{cls}>. " +
            "OPTIONAL {?s rdfs:label ?l} }"
        )
        self.connection.setQuery(query)
        return self.connection.query().convert()