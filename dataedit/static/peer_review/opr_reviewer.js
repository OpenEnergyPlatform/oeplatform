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
  "reviewFinished": false,
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
$('#submitButton').bind('click', saveEntrances);
// Submit review
$('#submit_summary').bind('click', submitPeerReview);
// Cancel review
$('#peer_review-cancel').bind('click', cancelPeerReview);
// OK Field View Change
$('#ok-button').bind('click', hideReviewerOptions);
$('#ok-button').bind('click', saveEntrances);
// Suggestion Field View Change
$('#suggestion-button').bind('click', showReviewerOptions);
$('#suggestion-button').bind('click', updateSubmitButtonColor);
// Reject Field View Change
$('#rejected-button').bind('click', showReviewerOptions);
$('#rejected-button').bind('click', updateSubmitButtonColor);
// Clear Input fields when new tab is selected
// nav items are selected via their class
$('.nav-link').click(clearInputFields);
// field items selector

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
      'Upload failed: ' + JSON.parse(response.responseJSON).error
    );
  } catch (e) {
    console.log(response)
    var response_msg = response.responseText;
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
}

/**
 * Submits peer review to backend
 */
function submitPeerReview() {
  $('#peer_review-submitting').removeClass('d-none');
  json = JSON.stringify(current_review);
  sendJson("POST", config.url_peer_review, json).then(function() {
    window.location = config.url_table;
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
  window.location = config.url_table;
}

/**
 * Identifies field name and value and refreshs side panel infos
 * @param {string} fieldKey Name of the field
 * @param {string} fieldValue Value of the field
 * @param category
 */
function click_field(fieldKey, fieldValue, category) {
    const cleanedFieldKey = fieldKey.replace(/\.\d+/g, '');
    selectedField = cleanedFieldKey;
    selectedFieldValue = fieldValue;
    selectedCategory = category;
    const selectedName = document.querySelector("#review-field-name");
    selectedName.textContent = cleanedFieldKey + " " + fieldValue;
    const fieldDescriptionsElement = document.getElementById("field-descriptions");
    const reviewItem = document.querySelectorAll('.review__item');
    let selectedDivId = 'field_' + cleanedFieldKey;
    let selectedDiv = document.getElementById(selectedDivId);
    console.log("Field descriptions data:", fieldDescriptionsData);
    if (fieldDescriptionsData[cleanedFieldKey]) {
        let fieldInfo = fieldDescriptionsData[cleanedFieldKey];
        let fieldInfoText = '<div class="reviewer-item">';
        if (fieldInfo.title) {
          fieldInfoText += '<div class="reviewer-item__row"><h2 class="reviewer-item__title">' + fieldInfo.title + '</h2></div>';
        }
        if (fieldInfo.description) {
            fieldInfoText += '<div class="reviewer-item__row"><div class="reviewer-item__key">Description:</div><div class="reviewer-item__value">' + fieldInfo.description + '</div></div>';
        }
        if (fieldInfo.example) {
            fieldInfoText += '<div class="reviewer-item__row"><div class="reviewer-item__key">Example:</div><div class="reviewer-item__value">' + fieldInfo.example + '</div></div>';
        }
        if (fieldInfo.badge) {
            fieldInfoText += '<div class="reviewer-item__row"><div class="reviewer-item__key">Badge:</div><div class="reviewer-item__value">' + fieldInfo.badge + '</div></div>';
        }
        fieldInfoText += '<div class="reviewer-item__row reviewer-item__row--border">Does it comply with the required ' + fieldInfo.title + ' description convention?</div></div>';
        fieldDescriptionsElement.innerHTML = fieldInfoText;
    } else {
        fieldDescriptionsElement.textContent = "Описание не найдено";
    }
    reviewItem.forEach(function(div) {
      div.style.backgroundColor = '';
    });
    if (selectedDiv) {
      selectedDiv.style.backgroundColor = '#F6F9FB';
    }
    console.log("Category:", category, "Field key:", cleanedFieldKey, "Data:", fieldDescriptionsData[cleanedFieldKey]);
    clearInputFields();
}



/**
 * Creates List of all fields from html elements
 */
function makeFieldList(){
  var fieldElements = [];
  $( ".field" ).each(function() { fieldElements.push(this.id) } ) ;
  //alert(fieldElements[14]);
  return fieldElements;
}

/**
 * Clears User Input fields
 */
function clearInputFields(){
  document.getElementById("valuearea").value = "";
  document.getElementById("commentarea").value = "";
}

/**
 * Selects the HTML field element after the current one and clicks it
 */
function selectNextField() {
  var fieldList = makeFieldList();
  var next = fieldList.indexOf('field_' + selectedField) + 1
  selectField(fieldList, next);
}

/**
 * Selects the HTML field element previous to the current one and clicks it
 */
function selectPreviousField(){
  var fieldList = makeFieldList();
  var prev = fieldList.indexOf('field_' + selectedField) - 1
  selectField(fieldList, prev);
}

/**
 * Clicks a Field after checking it exists
 */
function selectField(fieldList, field){
  if (field >= 0 && field <= fieldList.length){
    var element = fieldList[field];
    document.getElementById(element).click();
  }
}

/**
 * Saves selected state
 * @param {string} state Selected state
 */
function selectState(state) { // eslint-disable-line no-unused-vars
  selectedState = state;
}

/**
 * Renders fields on the Summary page, sorted by review state
 */
/**
 * Renders fields on the Summary page, sorted by review state
 */
/**
 * Displays fields based on selected category
 */
function renderSummaryPageFields() {
  const acceptedFields = [];
  const suggestingFields = [];
  const rejectedFields = [];
  const missingFields = [];

  for (const review of current_review.reviews) {
    const field_id = `#field_${review.key}`.replaceAll(".", "\\.");
    const fieldValue = $(field_id).text();
    const fieldState = review.fieldReview.state;
    const fieldCategory = review.category.slice(1);

    if (fieldState === 'ok') {
      acceptedFields.push({ field_id, fieldValue, fieldCategory });
    } else if (fieldState === 'suggestion') {
      suggestingFields.push({ field_id, fieldValue, fieldCategory });
    } else if (fieldState === 'rejected') {
      rejectedFields.push({ field_id, fieldValue, fieldCategory });
    }
  }

  const categories = document.querySelectorAll(".tab-pane");
  for (const category of categories) {
    const category_name = category.id.slice(0);
    if (["resource", "summary"].includes(category_name)) {
      continue;
    }
    const category_fields = category.querySelectorAll(".field");
    for (field of category_fields) {
      const field_name = field.id.slice(6);
      const field_id = `#field_${field_name}`.replaceAll(".", "\\.");
      const fieldValue = $(field_id).text();
      const found = current_review.reviews.some(review => review.key === field_name);
      if (!found) {
    missingFields.push({ field_id, fieldValue, fieldCategory: category_name });
      }
    }
  }

  // Display fields on the Summary page
  const summaryContainer = document.getElementById("summary");
  summaryContainer.innerHTML = `
    <h4>Accepted:</h4>
    ${createFieldList(acceptedFields)}
    <h4>Suggesting:</h4>
    ${createFieldList(suggestingFields)}
    <h4>Rejected:</h4>
    ${createFieldList(rejectedFields)}
    <h4>Missing:</h4>
    ${createFieldList(missingFields)}
  `;
}

/**
 * Creates an HTML list of fields with their categories
 * @param {Array} fields Array of field objects
 * @returns {string} HTML list of fields
 */
function createFieldList(fields) {
  return `
    <ul>
      ${fields.map(field => `<li>${field.fieldCategory}: ${field.fieldValue}</li>`).join('')}
    </ul>
  `;
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
      var unique_entry = true;
      var dummy_review = current_review;
      dummy_review["reviews"].forEach(function ( value, idx ){
          // if field is present already, update field
          if (value["key"] === selectedField){
              unique_entry = false;
              var element = document.querySelector('[aria-selected="true"]');
              var category = (element.getAttribute("data-bs-target"));
              if (selectedState == "ok") {
              Object.assign(current_review["reviews"][idx],
                  {
                      "category": category,
                      "key": selectedField,
                      "fieldReview": {
                          "timestamp": null, // TODO put actual timestamp
                            "user": "oep_reviewer", // TODO put actual username
                            "role": "reviewer",
                            "contributorValue": selectedFieldValue,
                            "comment": "",
                            "reviewerSuggestion": "",
                            "state": selectedState,
                      },
                  },
              )
              } else {
              Object.assign(current_review["reviews"][idx],
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
              )
            }
          }
      });
    var element = document.querySelector('[aria-selected="true"]');
    var category = (element.getAttribute("data-bs-target"));
    // if field hasn't been written before, add it
    if (unique_entry){
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
    )}
  }

  // Color ok/suggestion/rejected
  updateFieldColor();
  selectNextField();

  // alert(JSON.stringify(current_review, null, 4));
  document.getElementById("summary").innerHTML = (
    JSON.stringify(current_review, null, 4)
  );
  renderSummaryPageFields();
  checkReviewComplete();
}

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

/**
 * Shows reviewer Comment and Suggestion Input options
 */
function showReviewerOptions(){
    $("#reviewer_remarks").removeClass('d-none');
}

/**
 * Hides reviewer Comment and Suggestion Input options
 */
function hideReviewerOptions(){
    $("#reviewer_remarks").addClass('d-none');
}

/**
 * Colors Field based on Reviewer input
 */
function updateFieldColor(){
  // Color ok/suggestion/rejected
  field_id = `#field_${selectedField}`.replaceAll(".", "\\.");
  $(field_id).removeClass('field-ok');
  $(field_id).removeClass('field-suggestion');
  $(field_id).removeClass('field-rejected');
  $(field_id).addClass(`field-${selectedState}`);
}

/**
 * Colors Field based on Reviewer input
 */
function updateSubmitButtonColor(){
  // Color Save comment / new value
  $(submitButton).removeClass('btn-warning');
  $(submitButton).removeClass('btn-danger');
  if (selectedState == "suggestion"){
    $(submitButton).addClass('btn-warning');
  }
  else {
    $(submitButton).addClass('btn-danger');
  }
}

peerReview(config);
