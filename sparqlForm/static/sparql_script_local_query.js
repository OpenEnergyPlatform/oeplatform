/****************************************************/
// Filename: sparql_script_local_query.js
// Created: Venkatesh Murugadas
// Date : 01/01/2021
// Change history:
//      1.
//      2.
/****************************************************/

// Variable for the Datalist HTML elements
var dataList = document.getElementById("datalist_pred");


function loadOldTriples() {

    document.getElementById("oldPredicate").innerText= document.getElementById("predicate").innerText;
    document.getElementById("oldSubject").innerText = document.getElementById("subject").innerText;
    document.getElementById("oldObject").innerText = document.getElementById("object").innerText;
}

// function to append the result of the queries to the datalist element by iterating over the result json.
function append_datalist(result)
{

    var str='';
    for (var i = 0; i < result['results']['bindings'].length; i++)
    {
        var option = document.createElement("option");
        option.value = result['results']['bindings'][i]['item']['value'];
        // datalist.appendChild(option);
        str += '<option value="'+ option.value +'" />'; // Storing options in variable
    }
    return str
}

/*

Calling the Jena local SPARQL endpoint using JQuery ajax method to run a query and on success appending the
results to a datalist element.

select distinct predicates in the triples
    Query 1 :
        SELECT DISTINCT ?p WHERE
        { ?s ?p ?o }

*/
$(document).ready(function ()
{
    //specific URL form of the SPARQL query to get output in JSON
    var endpoint = "http://localhost:3030/ds/sparql";
    var pred_query = "?query=select distinct ?item where {?s ?item ?o}";
    var result_json = "&format=json";

    $.when(
    $.ajax({
        type: 'POST',
        url: endpoint+pred_query+result_json,
        dataType: 'json',
        success: function (result) {

            var dataList = document.getElementById("datalist_pred");
            dataList.innerHTML = "";
            console.log(result['results']['bindings'].length);
            // Variable for the Datalist HTML elements
            dataList.innerHTML = append_datalist(result);
        }
    })
    )
})

// Function to get the object value chosen by the user.
function setValue()
{
    let inputObjVal = document.getElementById("ajax_obj").value;
    let typeVal = document.getElementsByName('type');

    if (typeVal[0].checked) {
        document.getElementById("object").innerText = "<" + inputObjVal + ">";
    }
    else if (typeVal[1].checked) {
        document.getElementById("object").innerText = '"' + inputObjVal + '"';
    }

}

/*

Calling the Jena local SPARQL endpoint using JQuery ajax method to run a query and on success appending the
results to a datalist element.

select distinct "Subjects" based on the chosen "Predicates" in the triples
    Query 2 :
        SELECT DISTINCT ?s WHERE
        { ?s [p] ?o }

*/
function getSubjectValue()
{
    let inputVal = document.getElementById("ajax").value;
    let numSub = document.getElementById("num_subject");

    if (inputVal !== null)
    {
        // Selecting the input element and get the Predicate value
        document.getElementById("predicate").innerText = '<'+inputVal+'>';
        chosenPredVal = document.getElementById("predicate").innerText;

        if (chosenPredVal !== null)
        {
            console.log(chosenPredVal)
            $(document).ready(function ()
            {
                //specific URL form of the SPARQL query to get output in JSON
                var sub_endpoint = "http://localhost:3030/ds/sparql";
                var sub_query = "?query=select ?item where { ?item "+ chosenPredVal + " ?o }";
                var sub_result_json = "&format=json";

                $.when(
                $.ajax({
                    type: 'POST',
                    url: sub_endpoint + sub_query+ sub_result_json,
                    dataType: 'json',
                    success: function (result) {
                        var dataList_sub = document.getElementById("datalist_sub");
                        dataList_sub.innerHTML = "";
                        numSub.innerText = result['results']['bindings'].length;
                        console.log(result['results']['bindings'].length);
                        dataList_sub.innerHTML = append_datalist(result);

                    }
                })
                )
            })
        }
    }
}

/*
After the user chooses the Predicate from the Query 1 results, using the chosen predicate
another query is run on the DBpedia SPARQL endpoint to collect the objects which is a type
of the subjects in the range of the chosen predicate.

select distinct "Objects" based on the chosen "Predicate" and "Subject" in the triples
    Query 3 :
        SELECT DISTINCT ?o WHERE
        { [p] [p] ?o }

*/
function getObjectValue()
{
    let inputObjVal = document.getElementById("ajax").value;
    let inputSubVal = document.getElementById("ajax_sub").value;
    let numObj = document.getElementById("num_object");

    if (inputObjVal !== null)
    {
        // Selecting the input element and get the Predicate value
        document.getElementById("predicate").innerText = '<' + inputObjVal + '>';
        document.getElementById('subject').innerText = '<' + inputSubVal + '>'
        chosenPredVal = document.getElementById("predicate").innerText;
        chosenSubVal = document.getElementById("subject").innerText;

        if (chosenPredVal !== null)
        {
            console.log(chosenPredVal)
            $(document).ready(function ()
            {
                //specific URL form of the SPARQL query to get output in JSON
                var obj_endpoint = "http://localhost:3030/ds/sparql";
                var obj_query =  "?query=select ?item where { " + chosenSubVal +" "+ chosenPredVal + " ?item }";
                var obj_result_json = "&format=json";

                $.when(
                $.ajax({
                    type: 'POST',
                    url: obj_endpoint + obj_query+ obj_result_json,
                    dataType: 'json',
                    success: function (result) {
                        var dataList_obj = document.getElementById("datalist_obj");
                        dataList_obj.innerHTML = "";
                        numObj.innerText = result['results']['bindings'].length;
                        console.log(result['results']['bindings'].length);
                        dataList_obj.innerHTML = append_datalist(result)
                    }
                })
                )
            })
        }
    }
}

/*
Using regex identify whether the input consists of a URI or just a string
function parseInput(input) {

}
*/
function askTriple() {

    let inputPredVal = document.getElementById("predicate").innerText;
    let inputSubVal = document.getElementById("subject").innerText;
    let inputObjVal = document.getElementById("object").innerText;


    triple = inputSubVal + "  " + inputPredVal + "  " + inputObjVal
    /* create a function to parse the input to identify the input whether it
    is an URI or a string. */

    $(document).ready(function ()
            {
                //specific URL form of the SPARQL query to get output in JSON
                var obj_endpoint = "http://localhost:3030/ds/sparql";
                var obj_query =  "?query=ask { "+triple+"} ";
                var obj_result_json = "&format=json";

                $.when(
                $.ajax({
                    type: 'POST',
                    url: obj_endpoint + obj_query+ obj_result_json,
                    dataType: 'json',
                    success: function (result) {
                        document.getElementById("result").innerText = result['boolean'];
                    }
                })
                )
            })
}


function insertTriple() {

    let inputPredVal = document.getElementById("predicate").innerText;
    let inputSubVal = document.getElementById("subject").innerText;
    let inputObjVal = document.getElementById("object").innerText;

    /* create a function to parse the input to identify the input whether it
    is an URI or a string. */

    $(document).ready(function ()
            {
                $.when(
                $.ajax({
                    data: {
                        'inputSubVal': inputSubVal,
                        'inputPredVal': inputPredVal,
                        'inputObjVal': inputObjVal,
                    },
                    type: 'POST',
                    url: "/insertTriple",
                    success: function (data) {
                        document.getElementById("result").innerHTML = data.output;
                    }
                })
                )
            })
}


function deleteTriple() {

    let inputPredVal = document.getElementById("predicate").innerText;
    let inputSubVal = document.getElementById("subject").innerText;
    let inputObjVal = document.getElementById("object").innerText;

    /* create a function to parse the input to identify the input whether it
    is an URI or a string. */

    $(document).ready(function ()
            {
                $.when(
                $.ajax({
                    data: {
                        'inputSubVal': inputSubVal,
                        'inputPredVal': inputPredVal,
                        'inputObjVal': inputObjVal,
                    },
                    type: 'POST',
                    url: "/deleteTriple",
                    success: function (data) {
                        document.getElementById("result").innerHTML = data.output;
                    }
                })
                )
            })
}

function updateTriple() {

    let inputPredVal = document.getElementById("predicate").innerText;
    let inputSubVal = document.getElementById("subject").innerText;
    let inputObjVal = document.getElementById("object").innerText;
    let updateSubject = document.getElementById("newSubject").value;
    let updatePredicate =document.getElementById("newPredicate").value;
    let updateObject = document.getElementById("newObject").value;
    /* create a function to parse the input to identify the input whether it
    is an URI or a string. */

    $(document).ready(function ()
            {
                $.when(
                $.ajax({
                    data: {
                        'inputSubVal': inputSubVal,
                        'inputPredVal': inputPredVal,
                        'inputObjVal': inputObjVal,
                        'updateSubject': updateSubject,
                        'updatePredicate': updatePredicate,
                        'updateObject' : updateObject,
                    },
                    type: 'POST',
                    url: "/updateTriple",
                    success: function (data) {
                        document.getElementById("update_result").innerHTML = data.output;
                    }
                })
                )
            })
}