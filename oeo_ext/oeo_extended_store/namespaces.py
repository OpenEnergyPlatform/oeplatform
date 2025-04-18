from rdflib.namespace import OWL, RDF, XSD, Namespace

# TODO- Alot of hardcoded URL, transfer to settings or other config
OEO = Namespace("http://openenergy-platform.org/ontology/oeo/")
OEOX = Namespace("http://openenergy-platform.org/ontology/oeox/")
OBO = Namespace("http://purl.obolibrary.org/obo/")
DC = Namespace("http://purl.org/dc/terms/")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
NPG = Namespace("http://ns.nature.com/terms/")
SCHEMA = Namespace("https://schema.org/")
OEKG = Namespace("http://openenergy-platform.org/ontology/oekg/")
DBO = Namespace("http://dbpedia.org/ontology/")
RDF = RDF
OWL = OWL
XSD = XSD


def bind_all_namespaces(graph):
    graph.bind("OEO", OEO)
    graph.bind("OEOX", OEOX)
    graph.bind("OBO", OBO)
    graph.bind("DC", DC)
    graph.bind("RDFS", RDFS)
    graph.bind("NPG", NPG)
    graph.bind("SCHEMA", SCHEMA)
    graph.bind("OEKG", OEKG)
    graph.bind("DBO", DBO)

    return graph
