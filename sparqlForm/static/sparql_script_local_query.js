/****************************************************/
// Filename: sparql_script_local_query.js
// Created: Venkatesh Murugadas
// Date : 01/01/2021
// Recent changes : 20/02/2021
/****************************************************/

// Variable for the Datalist HTML elements
var dataList = document.getElementById("datalist_pred");
var dataList_study = document.getElementById("datalist_study_name");

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
$(document).ready(function () {
    //specific URL form of the SPARQL query to get output in JSON
    var endpoint = "http://localhost:3030/ds/sparql";
    var pred_query = "?query=select distinct ?item where {?s ?item ?o}";
    var result_json = "&format=json";

    $.when(
        $.ajax({
            type: 'POST',
            url: endpoint + pred_query + result_json,
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
/*
Ajax call to extract the Study/Scenario names from the Database
*/
$(document).ready(function () {
    $.when(
        $.ajax({
            type: 'GET',
            url: "/studyName",
            success: function (data) {
                var dataList_study = document.getElementById("datalist_study_name");
                var study_str = '';
                Object.values(data).forEach(item => study_str += '<option value="'+ item +'" />')
                dataList_study.innerHTML = study_str;
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

/*
Functions to get the details of the study.
*/
function getStudyReportDetails() {


    var study_report_name = document.querySelector("#ajax_study_name").value;
    if (!study_report_name) {
        document.getElementById("studyStatus").innerHTML = "Enter a study report name"
    }
    else if (study_report_name != "") {
        getStudyReport();
    }

}

function getStudyReport() {
    let study_report_name = document.querySelector("#ajax_study_name").value;
    document.getElementById("studyReportStatus").textContent = study_report_name;
    $.ajax({
        data: {
            'studyReportName': study_report_name
        },
        type: 'GET',
        beforeSend: function(){
            $("#loading_label").show();
          },
        url: "/getStudyReport",
        complete: function(){
            $("#loading_label").hide();
        },
        success: function (results) {
            document.getElementById("reportDetails").innerHTML = ""
            studyReport = JSON.stringify(results,null,2);
            studyReport_JSON = JSON.parse(studyReport)
            document.getElementById("reportDetails").innerHTML += "</br>"
            document.getElementById("reportDetails").innerHTML += "Title: " + JSON.stringify(studyReport_JSON['title'], null, 2)
            document.getElementById("reportDetails").innerHTML += "</br>"
            document.getElementById("reportDetails").innerHTML += "</br>"
            document.getElementById("reportDetails").innerHTML += "Subtitle : " + JSON.stringify(studyReport_JSON['subtitle'], null, 2)
            document.getElementById("reportDetails").innerHTML += "</br>"
            document.getElementById("reportDetails").innerHTML += "</br>"
            document.getElementById("reportDetails").innerHTML += "Type  :  " + JSON.stringify(studyReport_JSON['type'], null, 2)
            document.getElementById("reportDetails").innerHTML += "</br>"
            document.getElementById("reportDetails").innerHTML += "</br>"
            document.getElementById("reportDetails").innerHTML += "Publication Year : " + JSON.stringify(studyReport_JSON['publicationYear'], null, 2)
            document.getElementById("reportDetails").innerHTML += "</br>"
            document.getElementById("reportDetails").innerHTML += "</br>"
            document.getElementById("reportDetails").innerHTML += "Abstract : " + JSON.stringify(studyReport_JSON['abstract'], null, 2)
            document.getElementById("reportDetails").innerHTML += "</br>"
            document.getElementById("reportDetails").innerHTML += "</br>"
            document.getElementById("reportDetails").innerHTML += "About : " + JSON.stringify(studyReport_JSON['IAO_0000136'], null, 2)
            document.getElementById("reportDetails").innerHTML += "</br>"
            document.getElementById("reportDetails").innerHTML += "Authors"
            for (var i = 0; i < studyReport_JSON.has_authors.length; i++) {
                var counter = studyReport_JSON.has_authors[i];
                document.getElementById("reportDetails").innerHTML += "</br>"
                document.getElementById("reportDetails").innerHTML += "Name : " + counter.givenName + " " + counter.familyName;
                document.getElementById("reportDetails").innerHTML += "</br>"
                document.getElementById("reportDetails").innerHTML += "Affiliation : " + counter.affiliation;
                document.getElementById("reportDetails").innerHTML += "</br>"
            }
            document.getElementById("reportDetails").innerHTML += "</br>"
            document.getElementById("reportDetails").innerHTML += "URL Scheme : " + JSON.stringify(studyReport_JSON['url'], null, 2)
            document.getElementById("reportDetails").innerHTML += "</br>"
        },
    })
}

