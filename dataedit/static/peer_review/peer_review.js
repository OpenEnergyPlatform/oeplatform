
var peerReview = function (config) {
    var state = {
        "topic": null,
        "table": config.table,
        "reviewList": [],
        "metaMetadata": {
            "reviewVersion": "OEP-0.0.1",
            "metadataLicense": {
                "name": "CC0-1.0",
                "title": "Creative Commons Zero v1.0 Universal",
                "path": "https://creativecommons.org/publicdomain/zero/1.0/"
            }
        }
    }

    /*
    TODO: consolidate functions (same as in wizard and other places)
    */

    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== "") {
            var cookies = document.cookie.split(";");
            for (var i = 0; i < cookies.length; i++) {
                var cookie = $.trim(cookies[i]);
                if (cookie.substring(0, name.length + 1) === name + "=") {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function getCsrfToken() {
        var token1 = getCookie("csrftoken");
        return token1;
    }

    function sendJson(method, url, data, success, error) {
        var token = getCsrfToken();
        return $.ajax({
            url: url,
            headers: { "X-CSRFToken": token },
            data_type: "json",
            cache: false,
            contentType: "application/json; charset=utf-8",
            processData: false,
            data: data,
            type: method,
            success: success,
            error: error
        });
    }

    function getErrorMsg(x) {
        try {
            x = 'Upload failed: ' + JSON.parse(x.responseJSON).reason;
        } catch (e) {
            x = x.statusText;
        }
        return x;
    }

    function bindButtons() {
        // submit
        $('#peer_review-submit').bind('click', function submitPeerReview() {
            $('#peer_review-submitting').removeClass('d-none');
            var json = config.editor.getValue();
            json = fixData(json);
            json = JSON.stringify(json);
            sendJson("POST", config.url_api_meta, json).then(function () {
                window.location = config.url_view_table;
            }).catch(function (err) {
                // TODO evaluate error, show user message
                $('#peer_review-submitting').addClass('d-none');
                alert(getErrorMsg(err))
            });
        });

        // Cancel
        $('#peer_review-cancel').bind('click', function cancel() {
            window.location = config.cancle_url;
        })
    }

    (function init() {

        $('#peer_review-loading').removeClass('d-none');

        config.form = $('#peer_review-form');

        bindButtons();




    })();

    return config;

}

        // 1 Identify Category from tab
        var selectedCategory;
        document.getElementById('general').addEventListener('click', category_identifier);
        var category_identifier = function (inhtml) {

            // const selectedCategory = document.querySelector("#general-tab").innerHTML;
            const x = inhtml;
            console.log(x)
            const y = document.querySelector(inhtml).innerHTML;
            selectedCategory = x;



            return selectedCategory;
        }


        // 1 Identify field name
        var selectedField;
        var selectedFieldValue;
        //document.getElementById('field_name').addEventListener('click', click_field);
        var click_field = function (fieldKey, fieldValue) {
            const x = fieldKey;
            selectedField = x;
            selectedFieldValue=fieldValue;
            const selectedName = document.querySelector("#review-field-name");
            selectedName.textContent = fieldKey + ' ' + fieldValue;

            return x
        }


        // 2 Identify selected button
        var selectedState;
document.getElementById('ok-button').addEventListener('click', function(){
            selectedState = "ok";
            selectedButton();
        });
document.getElementById('suggestion-button').addEventListener('click', function(){
            selectedState = "suggestion";
            selectedButton();
        });
document.getElementById('rejected-button').addEventListener('click', function(){
            selectedState = "rejected";
            selectedButton();
        });


function selectedButton() {
    console.log(selectedState);
}

        // 3 Save added comment for corresponding field
        // document.getElementById('commentarea').addEventListener('change', saveComment);
        var saveComment = function() {
            var z = document.getElementById('commentarea');
            return z.value
        }


        // 3 Save added value suggestion for corresponding field
        // document.getElementById('valuearea').addEventListener('change', saveValue);
        var saveValue = function() {
            var selectedValue = document.querySelector("#valuearea");

            return selectedValue.value
        }


        // Function to save all values
        document.getElementById('submit-button').addEventListener('click', saveEntrances);
          var saveEntrances = function(button) {
            const state = button;
            //selectedState = state;
	        // Fill local Storage variable with content of user input upon Button click
            // Create list for review fields if it doesn't exist yet
            if(Object.keys(current_review["reviews"]).length === 0
                && current_review["reviews"].constructor === Object){
                    current_review["reviews"] = [];
            }
            if(selectedField){
                //TODO check if object with selectedField already exists (using for loop)
                //TODO turn into function updateReviewVariable()
                var element = document.querySelector('[aria-selected="true"]');
                var category = (element.getAttribute("data-bs-target"));
                current_review["reviews"].push(
                    {
                        "category": category,
                        "key": selectedField,
                        "fieldReview": {
                            "timestamp": null, //TODO put actual timestamp
                            "user": "oep_reviewer", //TODO put actual username
                            "role": "reviewer",
                            "contributorValue": selectedFieldValue,
                            "comment": document.getElementById("commentarea").value,
                            "reviewerSuggestion": document.getElementById("valuearea").value,
                            "state": selectedState,
                        }
                    }
                );
            }
            //alert(JSON.stringify(current_review, null, 4));
            document.getElementById("summary").innerHTML = (JSON.stringify(current_review, null, 4))

          }

/*        var saveEntrances = function() {
            var category = category_identifier();
            var fieldName = selectedField;
            var state = selectedState;
            let date = new Date();
            var comment = saveComment();
            var value_suggestion = saveValue();


            if (selectedState == "ok") {
                var review_result = {
                    "category": category,
                    "key": fieldName,
                    "state": state,
                    "entry":null,
                    "loop": null
                }
            }
            else {var review_result = {
                    "category": category,
                    "key": fieldName,
                    "state": state,
                    "fieldReview": [
                        {
                            "timestamp": date,
                            "reviewer": "oep_user",
                            "comment": comment,
                            "value_suggestion": value_suggestion,
                            "accepted": null
                        }
                    ]
                }
            }
            document.getElementById("commentarea").value = "";
            document.getElementById("valuearea").value = "";


            console.log(review_result)
            return review_result
        }
*/










        // ----------------------------------------------------------------------


        // Function for OK-Button
        document.getElementById('ok-button').addEventListener('click', okFunction)
        var okFunction = function(fieldKey, fieldValue) {
            var category = category_identifier();

            var review_result = {
                "category": category,
                "key": fieldKey,
                "state": "ok",
                "loop": null
            }

            return review_result
        }


        // Function for SUGGESTION-Button
        document.getElementById('suggestion-button').addEventListener('click', suggestionFunction)
        var suggestionFunction = function(fieldKey, fieldValue) {
            let date = new Date();
            var category = category_identifier();
            var comment = saveComment();
            var value_suggestion = saveValue();


            var review_result = {
                "category": category,
                "key": fieldKey,
                "state": "suggestion",
                "loop": [
                    {
                        "timestamp": date,
                        "reviewer": "oep_user",
                        "comment": comment,
                        "value_suggestion": value_suggestion,
                        "accepted": null
                    }
                ]
            }

            return review_result
        }


        // Function for REJECTED-Button
        document.getElementById('rejected-button').addEventListener('click', rejectedFunction)
        var rejectedFunction = function(fieldKey, fieldValue) {
            var fieldKey = fieldKey;
            let date = new Date();
            var category = category_identifier();
            var comment = saveComment();
            var value_suggestion = saveValue();

            var review_result = {
                "category": category,
                "key": fieldKey,
                "state": "rejected",
                "loop": [
                    {
                        "timestamp": date,
                        "reviewer": "oep_user",
                        "comment": comment,
                        "value_suggestion": value_suggestion,
                        "accepted": null
                    }
                ]
            }

            return review_result
        }


peerReview(config);