from SPARQLWrapper import SPARQLWrapper, JSON, POST, GET
from flask import Flask, request, render_template, jsonify
import os
import urllib.request
import re
import rdflib


ontology_file_path = (
    "/Users/venkateshmurugadas/oeplatform/sparqlForm/kg_files/oeoMerged.ttl"
)
concept_pattern = "OEO\_[0-9]*"

app = Flask(__name__, template_folder="templates")


@app.route("/")
@app.route("/index.html")
def index():
    return render_template("index.html")


@app.route("/studyName", methods=["GET", "POST"])
def studyName():
    proxy_support = urllib.request.ProxyHandler({})
    opener = urllib.request.build_opener(proxy_support)
    urllib.request.install_opener(opener)
    sparql_query_endpoint = SPARQLWrapper("http://localhost:3030/ds/sparql")
    sparql_query_endpoint.setMethod(GET)
    sparql_query_endpoint.setQuery(
        """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        prefix dc: <http://purl.org/dc/elements/1.1/>
        prefix dbo: <http://dbpedia.org/ontology/>
        prefix OEO_KG: <https://openenergy-platform.org/thing/>
        prefix OEO: <https://openenergy-platform.org/ontology/oeo/>

        SELECT ?subject ?item
        WHERE {
        ?subject a OEO:OEO_00020012.
        ?subject dc:title ?item
        }
        """
    )
    sparql_query_endpoint.setReturnFormat(JSON)
    result = sparql_query_endpoint.query().convert()

    study_names_list = []
    study_name_uri_dict = {}
    for i in range(len(result["results"]["bindings"])):
        study_name_uri_dict[
            result["results"]["bindings"][i]["subject"]["value"]
        ] = result["results"]["bindings"][i]["item"]["value"]
        study_names_list.append(result["results"]["bindings"][i]["item"]["value"])

    return jsonify(study_name_uri_dict)


def findConceptName(ontologyPath, term):
    g = rdflib.Graph()
    g.parse(ontologyPath, format="turtle")
    variable1 = "".join(["<http://openenergy-platform.org/ontology/oeo/", term, ">"])
    query = " ".join(
        ["select distinct ?o where {", variable1, " rdfs:label ?o }  LIMIT 1 "]
    )
    result = g.query(query)
    for row in result:
        return str(row[0])


@app.route("/getStudyReport", methods=["GET", "POST"])
def getStudyReport():
    """
    Function to extract the details of the study.
    """
    studyReportName = request.values.get("studyReportName")
    proxy_support = urllib.request.ProxyHandler({})
    opener = urllib.request.build_opener(proxy_support)
    urllib.request.install_opener(opener)
    sparql_query_endpoint = SPARQLWrapper("http://localhost:3030/ds/sparql")
    sparql_query_endpoint.setMethod(GET)
    # Query to get the URI of the Study/Scenario
    sparql_query_endpoint.setQuery(
        """
        SELECT ?subject
        WHERE { ?subject ?predicate '"""
        + studyReportName
        + """'}"""
    )
    sparql_query_endpoint.setReturnFormat(JSON)
    result = sparql_query_endpoint.query().convert()
    studyReportUri = result["results"]["bindings"][0]["subject"]["value"]
    # Query to get the Details of the Study/Scenario
    sparql_query_endpoint.setQuery(
        """
        SELECT ?predicate ?object
        WHERE {
        <"""
        + studyReportUri
        + """>  ?predicate ?object}"""
    )
    sparql_query_endpoint.setReturnFormat(JSON)
    result = sparql_query_endpoint.query().convert()

    study_report_dict = {}
    study_report_dict["has_authors"] = []
    for i in range(len(result["results"]["bindings"])):
        v = result["results"]["bindings"][i]["predicate"]["value"]
        k = result["results"]["bindings"][i]["object"]["value"]
        if result["results"]["bindings"][i]["object"]["type"] == "literal":
            v = re.split("\/|#", v)[-1]
            if re.match(concept_pattern, v):
                v = findConceptName(ontology_file_path, v)
            if v != "url":
                k = re.split("\/", k)[-1]
                if re.match(concept_pattern, k):
                    k = findConceptName(ontology_file_path, k)
            study_report_dict[v] = k

        elif result["results"]["bindings"][i]["object"]["type"] == "uri":
            if (
                result["results"]["bindings"][i]["object"]["value"]
                == "https://openenergy-platform.org/ontology/oeo/OEO_00020012"
            ):
                v = re.split("\/|#", v)[-1]
                k = re.split("\/", k)[-1]
                if re.match(concept_pattern, k):
                    k = findConceptName(ontology_file_path, k)
                if re.match(concept_pattern, v):
                    v = findConceptName(ontology_file_path, v)

                study_report_dict[v] = k

            else:
                if v == "https://openenergy-platform.org/ontology/oeo/OEO_00000506":
                    details = create_query(
                        result["results"]["bindings"][i]["object"]["value"]
                    )
                    study_report_dict["has_authors"].append(details)
                else:
                    details = create_query(
                        result["results"]["bindings"][i]["object"]["value"]
                    )
                    v = re.split("\/|#", v)[-1]
                    study_report_dict[v] = details

    return jsonify(study_report_dict)


def create_query(Uri):
    value_dict = {}
    proxy_support = urllib.request.ProxyHandler({})
    opener = urllib.request.build_opener(proxy_support)
    urllib.request.install_opener(opener)
    sparql_query_endpoint = SPARQLWrapper("http://localhost:3030/ds/sparql")
    sparql_query_endpoint.setMethod(GET)
    # Query to get the details of the URI present in the Object
    sparql_query_endpoint.setQuery(
        """
        SELECT ?predicate ?object
        WHERE {
        <"""
        + Uri
        + """>  ?predicate ?object}"""
    )
    sparql_query_endpoint.setReturnFormat(JSON)
    result = sparql_query_endpoint.query().convert()
    for i in range(len(result["results"]["bindings"])):
        k = result["results"]["bindings"][i]["object"]["value"]
        v = result["results"]["bindings"][i]["predicate"]["value"]
        v = re.split("\/|#", v)[-1]
        if re.match(concept_pattern, v):
            v = findConceptName(ontology_file_path, v)
        k = re.split("\/", k)[-1]
        if re.match(concept_pattern, k):
            k = findConceptName(ontology_file_path, k)

        value_dict[v] = k
    return value_dict


@app.route("/insertTriple", methods=["POST"])
def insertTriple():

    inputSubject = request.form["inputSubVal"]
    inputPredicate = request.form["inputPredVal"]
    inputObject = request.form["inputObjVal"]

    sparql_update_endpoint = SPARQLWrapper("http://localhost:3030/ds/update")
    sparql_update_endpoint.setMethod(POST)
    triple = inputSubject + " " + inputPredicate + " " + inputObject
    print(triple)

    sparql_update_endpoint.setQuery(
        """
        INSERT { """
        + triple
        + """} WHERE { ?s ?p ?o }
        """
    )
    results = sparql_update_endpoint.query()

    output = results.response.read()
    outputs = {"output": output}
    return jsonify(outputs)


@app.route("/deleteTriple", methods=["POST"])
def deleteTriple():

    inputSubject = request.form["inputSubVal"]
    inputPredicate = request.form["inputPredVal"]
    inputObject = request.form["inputObjVal"]

    sparql_update_endpoint = SPARQLWrapper("http://localhost:3030/ds/update")
    sparql_update_endpoint.setMethod(POST)
    triple = inputSubject + " " + inputPredicate + " " + inputObject
    print(triple)
    sparql_update_endpoint.setQuery(
        """
        DELETE { """
        + triple
        + """} WHERE { ?s ?p ?o }
        """
    )
    results = sparql_update_endpoint.query()
    output = results.response.read()
    print(output)
    outputs = {"output": output}
    return jsonify(outputs)


@app.route("/updateTriple", methods=["POST"])
def updateTriple():

    inputSubject = request.form["inputSubVal"]
    inputPredicate = request.form["inputPredVal"]
    inputObject = request.form["inputObjVal"]
    updateSubject = request.form["updateSubject"]
    updatePredicate = request.form["updatePredicate"]
    updateObject = request.form["updateObject"]

    sparql_update_endpoint = SPARQLWrapper("http://localhost:3030/ds/update")
    sparql_update_endpoint.setMethod(POST)
    oldTriple = inputSubject + " " + inputPredicate + " " + inputObject
    newTriple = updateSubject + " " + updatePredicate + " " + updateObject
    print(oldTriple)
    print(newTriple)
    sparql_update_endpoint.setQuery(
        """
        DELETE { """
        + oldTriple
        + """
        }INSERT {"""
        + newTriple
        + """}WHERE { """
        + oldTriple
        + """}
        """
    )
    results = sparql_update_endpoint.query()
    output = results.response.read()
    print(output)
    outputs = {"output": output}
    return jsonify(outputs)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

