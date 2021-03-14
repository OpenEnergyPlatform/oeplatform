from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Graph

from oeplatform.settings import RDF_DATABASES


class ConnectionContext:
    def __init__(self):
        c = RDF_DATABASES["knowledge"]

        self.connection = SPARQLWrapper(f"http://{c['host']}:{c['port']}/{c['name']}")
        self.connection.setReturnFormat(JSON)

    def query_all_objects(self, subjects, predicates):
        query = (
            "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n"
            "SELECT ?s ?p ?o ?lo ?lp WHERE { "
        )
        options = ["?p rdfs:label ?lp .", "?o rdfs:label ?lo"]
        for s in subjects:
            filter = [f"?s = <{s}>"]
            query += " UNION ".join(f"{{ { p.fetch_query('?s', '?o', options=options, filter=filter) } }}" for p in predicates)

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
        p = "a" if not subclass else "rdfs:subClassOf"
        if inverse:
            q = f"<{filter}> {p} ?iri "
        else:
            q = f"?iri {p} <{filter}>"
        s = "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n"
        s += f"SELECT ?iri ?l WHERE {{ {q} .  OPTIONAL {{ ?iri rdfs:label ?l . }} }}"
        self.connection.setQuery(s)
        return self.connection.query().convert()