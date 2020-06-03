from django.shortcuts import render
from django.views import View
from SPARQLWrapper import SPARQLWrapper, JSON

# Create your views here.

s = SPARQLWrapper("http://localhost:3030/oeo/sparql", "utf-8", "GET")
s.setReturnFormat(JSON)

def _query(q):
    fullquery = """
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX obo: <http://purl.obolibrary.org/obo/>
    
    SELECT ?subject ?label ?def
    WHERE {{ """ + q + """ 
    } OPTIONAL { ?subject rdfs:label ?label } OPTIONAL { ?subject obo:IAO_0000115 ?def }
    FILTER (strstarts(str(?subject),
          "http://openenergy-platform.org/ontology/oeo")) }
    """
    print(fullquery)
    s.setQuery(fullquery)
    result = s.query().convert()
    return result["results"]["bindings"]


class OntologyOverview(View):
    def get(self, request):
        classes = _query("?subject a owl:Class .")
        object_properties = _query("?subject a owl:ObjectProperty .")
        return render(request, "ontology/oeo.html", dict(
            classes=classes,
            object_properties=object_properties
        ))
