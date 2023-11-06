from SPARQLWrapper import JSON, SPARQLWrapper

from modelview.rdf.namespace import OEO_KG
from oeplatform.settings import RDF_DATABASES


class ConnectionContext:
    def __init__(self):
        c = RDF_DATABASES["knowledge"]

        self.connection = SPARQLWrapper(f"http://{c['host']}:{c['port']}/{c['name']}")
        self.update_connection = SPARQLWrapper(
            f"http://{c['host']}:{c['port']}/{c['name']}/update"
        )
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

    def insert_new_instance(self, subject, property, inverse=False, new_name=""):
        # hash = getattr(OEO_KG, str(uuid.uuid4())) + "/" + new_name.replace(" ", "-")
        hash = getattr(OEO_KG, new_name.replace(" ", "-"))
        s = "DELETE { } INSERT {"
        if inverse:
            s += f" <{hash}> <{property}> {subject}. "
        else:
            s += f"{subject} <{property}> <{hash}>. "
        s += "} WHERE {}"
        self.execute(s)
        return hash

    def insert_new_study(self, study_name):
        s = "INSERT {"
        s += f"<http://openenergy-platform.org/oekg/{study_name}> a <http://openenergy-platform.org/ontology/oeo/OEO_00020011>"  # noqa
        s += "} WHERE {}"
        self.execute(s)
        return {}

    def execute(self, query):
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
            f"""{{ { p.fetch_queries('?s', '?o', options=options+[p._label_option], filter=[f'?s = <{s}>'], where=[f'BIND("{fname}" as ?fname )']) } }}"""  # noqa
            for s in subjects
            for fname, p in predicates
            if p.rdf_name
        )

        query += "}"
        self.connection.setQuery(query)
        return self.connection.query().convert()

    def query_one_object(self, subject, predicate):
        query = "SELECT ?object WHERE { "
        query += f""" <{subject}> {predicate} """
        query += " ?object . } "
        self.connection.setQuery(query)
        return self.connection.query().convert()

    def query_all_factory_instances(self, factory):
        query = (
            "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n"
            "SELECT ?s ?ls WHERE { "
            f"?s a <{factory._direct_parent}>."
        )
        for option in [factory._label_option("?s", "?ls")]:
            query += "OPTIONAL {" + option + "}"

        query += "} ORDER By ASC(?ls)"
        self.connection.setQuery(query)
        return self.connection.query().convert()

    def get_all_instances(self, cls, subclass=False):
        query = (
            "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n"
            + "SELECT ?s ?l WHERE { "
            + f"?s {'rdfs:subClassOf' if subclass else 'a'} <{cls}>. "
            + "OPTIONAL {?s rdfs:label ?l} }"
        )
        self.connection.setQuery(query)
        return self.connection.query().convert()
