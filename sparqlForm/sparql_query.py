from SPARQLWrapper import SPARQLWrapper, JSON, POST, GET
from flask import Flask, request, render_template, jsonify
import os
import urllib.request


app = Flask(__name__, template_folder="templates")


@app.route("/")
@app.route("/index.html")
def index():
    return render_template("index.html")


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

