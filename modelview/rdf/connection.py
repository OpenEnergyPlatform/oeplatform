from SPARQLWrapper import SPARQLWrapper, JSON

from rdflib.serializer import Serializer

from oeplatform.settings import RDF_DATABASES
from django.utils.html import conditional_escape, format_html, format_html_join, mark_safe

from typing import Type

class ConnectionContext:
    def __init__(self):
        c = RDF_DATABASES["knowledge"]

        self.connection = SPARQLWrapper(f"http://{c['host']}:{c['port']}/{c['name']}")
        self.connection.setReturnFormat(JSON)

    def execute(self, entities):
        s = "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n" \
            "SELECT ?s ?p ?o ?lo ?lp WHERE "
        s += " UNION ".join(f"{{ ?s ?p ?o. OPTIONAL {{ ?p rdfs:label ?lp . }} . OPTIONAL {{ ?o rdfs:label ?lo . }} . FILTER ( ?s = <{e}> )}}" for e in entities)
        self.connection.setQuery(s)
        return self.connection.query().convert()

    def describe(self, entities):
        s = "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n" \
            f"DESCRIBE <{' '.join(entities)}>"
        self.connection.setQuery(s)
        res = self.connection.query().convert()
        return res

    def labels(self, entities):
        s = "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n" \
          "SELECT ?o WHERE "
        s += " UNION ".join(
            f"{{ ?s rdfs:label ?o. OPTIONAL {{ ?p rdfs:label ?lp . }} . OPTIONAL {{ ?o rdfs:label ?lo . }} . FILTER ( ?s = <{e}> )}}"
            for e in entities)
        self.connection.setQuery(s)
        return self.connection.query().convert()



