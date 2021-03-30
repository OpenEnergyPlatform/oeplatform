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
        result = None
        s = "DELETE {{ "
        if old_value:
            s += f"{subject} {property} {old_value} "
        s += "}} "
        s += f"INSERT {{ "
        if new_value:
            s += f"{subject} {property} {new_value} "
        elif not old_value:
            hash = uuid.uuid4()
            s += f"{subject} {property} {hash} "
            result = hash
        s += "}} "
        s += "WHERE {}"
        print(s)
        return result

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

    def describe(self, entities):
        s = (
            "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n"
            f"DESCRIBE <{' '.join(entities)}>"
        )
        self.connection.setQuery(s)
        res = self.connection.query().convert()
        return res

    def labels(self, entities):
        s = "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n SELECT ?o WHERE "
        s += " UNION ".join(
            f"{{ ?s rdfs:label ?o. OPTIONAL {{ ?p rdfs:label ?lp . }} . OPTIONAL {{ ?o rdfs:label ?lo . }} . FILTER ( ?s = <{e}> )}}"
            for e in entities
        )
        self.connection.setQuery(s)
        return self.connection.query().convert()

    def apply_diff(self, inserts: Graph, deletes: Graph):
        s = f"DELETE {{ {'. '.join(f'{s} {p} {o}' for s, p, o in deletes) } }} "
        s += f"INSERT {{ {'. '.join(f'{s} {p} {o}' for s, p, o in inserts) } }} "
        s += "WHERE {}"
        print(s)

    def load_all(self, filter, subclass=False, inverse=False):
        q = ". ".join(f"?iri {f}" for f in filter)
        s = "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n"
        s += f"SELECT ?iri ?l WHERE {{ {q} .  OPTIONAL {{ ?iri rdfs:label ?l . }} }}"
        self.connection.setQuery(s)
        return self.connection.query().convert()
