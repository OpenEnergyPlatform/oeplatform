var selectedField;
var selectedFieldValue;
var selectedState;

var current_review = {
  "topic": null,
  "table": null,
  "dateStarted": null,
  "dateFinished": null,
  "metadataVersion": "v1.5.2",
  "reviews": [],
  "reviewFinished": "false",
  "grantedBadge": null,
  "metaMetadata": {
    "reviewVersion": "OEP-0.0.1",
    "metadataLicense": {
      "name": "CC0-1.0",
      "title": "Creative Commons Zero v1.0 Universal",
      "path": "https://creativecommons.org/publicdomain/zero/1.0/",
    },
  },
};

// BINDS

// Submit field review
$('#submit-button').bind('click', saveEntrances);

// Submit review
$('#submit_summary').bind('click', submitPeerReview);
// Cancel review
$('#peer_review-cancel').bind('click', cancelPeerReview);


/**
 * Returns name from cookies
 * @param {string} name Key to look up in cookie
 * @returns {value} Cookie value
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

/**
 * Get CSRF Token
 * @returns {string} CSRF Token
 */
function getCsrfToken() {
  var token1 = getCookie("csrftoken");
  return token1;
}

/**
 * Sends JSON to backend url
 * @param {string} method Get or post request
 * @param {string} url URL to send JSON to
 * @param {json} data Data to send to backend
 * @param {function} success Success function
 * @param {function} error Error function
 * @returns {value} AJAX function return
 */
function sendJson(method, url, data, success, error) {
  var token = getCsrfToken();
  return $.ajax({
    url: url,
    headers: {"X-CSRFToken": token},
    data_type: "json",
    cache: false,
    contentType: "application/json; charset=utf-8",
    processData: false,
    data: data,
    type: method,
    success: success,
    error: error,
  });
}

/**
 * Reads error message from response
 * @param {json} response Get or post request
 * @returns {string} Response error message
 */
function getErrorMsg(response) {
  try {
    var response_msg = (
      'Upload failed: ' + JSON.parse(response.responseJSON).reason
    );
  } catch (e) {
    var response_msg = response.statusText;
  }
  return response_msg;
}

/**
 * Configurates peer review
 * @param {json} config Configuration JSON
 */
function peerReview(config) {
  /*
    TODO: consolidate functions (same as in wizard and other places)
    */

  (function init() {
    $('#peer_review-loading').removeClass('d-none');
    config.form = $('#peer_review-form');
  })();
};

/**
 * Submits peer review to backend
 */
function submitPeerReview() {
  $('#peer_review-submitting').removeClass('d-none');
  json = JSON.stringify(current_review);
  sendJson("POST", config.url_api_meta, json).then(function() {
    window.location = config.url_api_meta;
  }).catch(function(err) {
    // TODO evaluate error, show user message
    $('#peer_review-submitting').addClass('d-none');
    alert(getErrorMsg(err));
  });
}

/**
 * Cancels peer review and forwards to cancel url
 */
function cancelPeerReview() {
  window.location = config.cancel_url;
}

/**
 * Identifies field name and value and refreshs side panel infos
 * @param {string} fieldKey Name of the field
 * @param {string} fieldValue Value of the field
 */
function click_field(fieldKey, fieldValue) { // eslint-disable-line no-unused-vars,max-len
  selectedField = fieldKey;
  selectedFieldValue=fieldValue;
  const selectedName = document.querySelector("#review-field-name");
  selectedName.textContent = fieldKey + ' ' + fieldValue;
};

/**
 * Saves selected state
 * @param {string} state Selected state
 */
function selectState(state) { // eslint-disable-line no-unused-vars
  selectedState = state;
}


/**
  * Saves field review to current review list
 */
function saveEntrances() {
  // Create list for review fields if it doesn't exist yet
  if (Object.keys(current_review["reviews"]).length === 0 &&
                current_review["reviews"].constructor === Object) {
    current_review["reviews"] = [];
  }
  if (selectedField) {
    // TODO check if object with selectedField already exists (using for loop)
    // TODO turn into function updateReviewVariable()
    var element = document.querySelector('[aria-selected="true"]');
    var category = (element.getAttribute("data-bs-target"));
    current_review["reviews"].push(
        {
          "category": category,
          "key": selectedField,
          "fieldReview": {
            "timestamp": null, // TODO put actual timestamp
            "user": "oep_reviewer", // TODO put actual username
            "role": "reviewer",
            "contributorValue": selectedFieldValue,
            "comment": document.getElementById("commentarea").value,
            "reviewerSuggestion": document.getElementById("valuearea").value,
            "state": selectedState,
          },
        },
    );
  }

  // Color ok/suggestion/rejected
  field_id = `#field_${selectedField}`.replaceAll(".", "\\.");
  $(field_id).removeClass('field-ok');
  $(field_id).removeClass('field-suggestion');
  $(field_id).removeClass('field-rejected');
  $(field_id).addClass(`field-${selectedState}`);

  // alert(JSON.stringify(current_review, null, 4));
  document.getElementById("summary").innerHTML = (
    JSON.stringify(current_review, null, 4)
  );
  checkReviewComplete();
};

/**
 * Checks if all fields are reviewed and activates submit button if ready
 */
function checkReviewComplete() {
  var fields_reviewed = {};
  for (const review of current_review.reviews) {
    const category_name = review.category.slice(1);
    if (!(category_name in fields_reviewed)) {
      fields_reviewed[category_name] = [];
    }
    fields_reviewed[category_name].push(review.key);
  }

  const categories = document.querySelectorAll(".tab-pane");
  for (const category of categories) {
    const category_name = category.id;
    // TODO: remove resources, once they are working correct
    if (["resource", "summary"].includes(category_name)) {
      continue;
    }
    if (!(category_name in fields_reviewed)) {
      return;
    }
    const category_fields = category.querySelectorAll(".field");
    for (field of category_fields) {
      const field_name = field.id.slice(6);
      if (!fields_reviewed[category_name].includes(field_name)) {
        return;
      }
    }
  }

  // All fields reviewed!
  $('#submit_summary').removeClass('disabled');
}

peerReview(config);
