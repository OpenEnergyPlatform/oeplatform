/****************************************************/
// Filename: sparql_script.js
// Created: Venkatesh Murugadas
// Date : 08/11/2020
// Change history:
//      1. change 1 : Formatting the Query URL to output the result in the format of JSON
//      2.
/****************************************************/

// Variable for the Datalist HTML elements
var dataList = document.getElementById("datalist_pred");
var datalist_obj = document.getElementById("datalist_obj");

// function to append the result of the queries to the datalist element by iterating over the result json.
function append_datalist(result,datalist)
{
    for(var i = 0;i < result['results']['bindings'].length ; i++)
    {
        var option = document.createElement("option");
        option.value = result['results']['bindings'][i]['p']['value'];
        datalist.appendChild(option);
    }
    return datalist
}

/*

Calling the DBpedia SPARQL endpoint using JQuery ajax method to run a query and on success appending the
results to a datalist element.

    Query 1 :
        SELECT ?p WHERE
        {
            ?p a rdf:Property.
        }

*/
$(document).ready(function ()
{
    //specific URL form of the SPARQL query to get output in JSON
    var endpoint = "http://dbpedia.org/sparql/?query=";
    var result_json = "&format=json"; //change 1
    var pred_query = "SELECT ?p WHERE { ?p rdf:type rdf:Property.}";

    $.when(
    $.ajax({
        type: 'POST',
        url: endpoint+pred_query+result_json,
        dataType: 'json',
        success: function(result){
            //console.log(result['results']['bindings'].length);
            dataList = append_datalist(result,dataList);
        }
    })
    )
})

// Function to get the object value chosen by the user.
function setValue()
{
    let inputObjVal = document.getElementById("ajax_obj").value;
    document.getElementById("object").innerText = "<"+inputObjVal+">"
}

/*
After the user chooses the Predicate from the Query 1 results, using the chosen predicate
another query is run on the DBpedia SPARQL endpoint to collect the objects which is a type
of the subjects in the range of the chosen predicate.

Query 2 :
    It depends on selection [p] from Query 1:

    SELECT ?o WHERE
    {
        ?p rdfs:range ?s.
        ?o a ?s.
    }
*/
function getObjectValue()
{
    let inputVal = document.getElementById("ajax").value;
    let numObj = document.getElementById("num_object");

    if (inputVal !== null)
    {
        // Selecting the input element and get the Predicate value
        document.getElementById("predicate").innerText = '<'+inputVal+'>';
        chosenPredVal = document.getElementById("predicate").innerText;

        if (chosenPredVal !== null)
        {
            //console.log(chosenPredVal)
            $(document).ready(function ()
            {
                //specific URL form of the SPARQL query to get output in JSON
                var obj_endpoint = "http://dbpedia.org/sparql/?query=";
                var obj_result_json = "&format=json"; //change 1
                var obj_query = "SELECT ?p WHERE { " + chosenPredVal + " rdfs:range ?s. ?p a ?s.}";

                $.when(
                $.ajax({
                    type: 'POST',
                    url: obj_endpoint + obj_query+ obj_result_json,
                    dataType: 'json',
                    success: function (result) {
                        numObj.innerText = result['results']['bindings'].length;
                        //console.log(result['results']['bindings'].length);
                        dataList_obj = append_datalist(result,datalist_obj);
                    }
                })
                )
            })
        }
    }
}