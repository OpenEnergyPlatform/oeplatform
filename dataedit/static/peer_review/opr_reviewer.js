// this raises more errors as transition from script to module 
// makes it more complicated to use onclick in html elements
// import { updateClientStateDict } from './frontend/state.js'

var selectedField;
var selectedFieldValue;
var selectedState;

var current_review = {
  "topic": config.topic,
  "table": config.table,
  "dateStarted": null,
  "dateFinished": null,
  "metadataVersion": "v1.6.0",
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
$('#submitButton').bind('click', hideReviewerOptions);
// Submit review (visible to contributor)
$('#submit_summary').bind('click', submitPeerReview);
// save the current review (not visible to contributor)
$('#peer_review-save').bind('click', savePeerReview);
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
 * @param {json} config Configuration JSON from Django backend.
 */
function peerReview(config) {
  /*
    TODO: Show loading icon if peer review page is loaded 
    */

  // (function init() {
  //   $('#peer_review-loading').removeClass('d-none');
  //   config.form = $('#peer_review-form');
  // })();
  
  
  selectNextField();
  renderSummaryPageFields();
  if (state_dict){
    check_if_review_finished();
  }
  
}

/**
 * Save peer review to backend
 */
function savePeerReview() {
  $('#peer_review-save').removeClass('d-none');
  json = JSON.stringify({ reviewType: 'save', reviewData: current_review });
  sendJson("POST", config.url_peer_review, json).then(function() {
    window.location = config.url_table;
  }).catch(function(err) {
    // TODO evaluate error, show user message
    $('#peer_review-save').addClass('d-none');
    alert(getErrorMsg(err));
  });
}

/**
 * Submits peer review to backend
 */
function submitPeerReview() {
  $('#peer_review-submitting').removeClass('d-none');
  json = JSON.stringify({ reviewType: 'submit', reviewData: current_review });
  sendJson("POST", config.url_peer_review, json).then(function() {
    window.location = config.url_table;
  }).catch(function(err) {
    // TODO evaluate error, show user message
    $('#peer_review-submitting').addClass('d-none');
    alert(getErrorMsg(err));
  });
}

/**
 * Finish peer review and save to backend
 */
function finishPeerReview() {
  $('#peer_review-submitting').removeClass('d-none');

  var selectedBadge = $('input[name="reviewer-option"]:checked').val();
  console.log(selectedBadge)
  current_review.badge = selectedBadge
  current_review.reviewFinished = true
  json = JSON.stringify({ reviewType: 'finished', reviewData: current_review, reviewBadge: selectedBadge });
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
 * Identifies field name and value sets selected stlye and refreshes 
 * reviewer box (side panel) infos.
 * @param {string} fieldKey Name of the field
 * @param {string} fieldValue Value of the field
 * @param {string} category Metadata catgeory related to the fieldKey 
 */

function click_field(fieldKey, fieldValue, category) {
    // this seems unused but it is relevant to select next and prev field functions
    selectedField = fieldKey;
    selectedFieldValue = fieldValue;
    selectedCategory = category;
    const cleanedFieldKey = fieldKey.replace(/\.\d+/g, '');
    const selectedName = document.querySelector("#review-field-name");
    selectedName.textContent = cleanedFieldKey + " " + fieldValue;
    const fieldDescriptionsElement = document.getElementById("field-descriptions");
    const reviewItem = document.querySelectorAll('.review__item');

    let selectedDivId = 'field_' + fieldKey;
    let selectedDiv = document.getElementById(selectedDivId);

    // console.log("Field descriptions data:", fieldDescriptionsData);
    // Populate the reviewer box
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
        fieldDescriptionsElement.textContent = "No description found";
    }

  const fieldState = getFieldState(fieldKey);
  if (fieldState) {
    if (fieldState === 'ok') {
        document.getElementById("ok-button").disabled = true;
        document.getElementById("rejected-button").disabled = true;
        document.getElementById("suggestion-button").disabled = true;
    } else if (fieldState === 'rejected') {
        document.getElementById("ok-button").disabled = false;
        document.getElementById("rejected-button").disabled = false;
        document.getElementById("suggestion-button").disabled = false;
    }
  }

  // Set selected / not selected style on metadata fields
  reviewItem.forEach(function(div) {
    div.style.backgroundColor = '';
  });
  if (selectedDiv) {
    selectedDiv.style.backgroundColor = '#F6F9FB';
  }

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
  const reviewControls = document.querySelector('.review__controls');
  if (reviewControls) {
    document.getElementById("valuearea").value = "";
    document.getElementById("commentarea").value = "";
  }
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
  if (field >= 0 && field < fieldList.length){
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
  updateClientStateDict(fieldKey=selectedField, state=state);
  check_if_review_finished();
}

/**
 * Saves selected state the client added. 
 * As the state_dict is generated on page load (in django view) 
 * based on the stored review, these updates will not be sent to the backend.
 * @param {string} fieldKey Identifiere of the field
 * @param {string} state Selected state
 */
function updateClientStateDict(fieldKey, state){
  state_dict = state_dict ?? {};
  if (fieldKey in state_dict) {
    // console.log(`Der Schlüssel '${fieldKey}' ist vorhanden.`);
    state_dict[fieldKey] = state;
  } else {
    // console.log(`Der Schlüssel '${fieldKey}' ist nicht vorhanden.`);
    state_dict[fieldKey] = state;
  }
}

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

  if (state_dict && Object.keys(state_dict).length > 0) {
    const fields = document.querySelectorAll('.field');
    for (let field of fields) {
      let field_id = field.id.slice(6);
      const fieldValue = $(field).text();
      const fieldState = getFieldState(field_id);
      const fieldCategory = field.getAttribute('data-category');  // Получаем категорию поля
      if (fieldState === 'ok') {
        acceptedFields.push({ field_id, fieldValue, fieldCategory });
      } else if (fieldState === 'suggestion' || fieldState === 'rejected') {
        missingFields.push({ field_id, fieldValue, fieldCategory });
      }
    }
  }

  for (const review of current_review.reviews) {
    const field_id = `#field_${review.key}`.replaceAll(".", "\\.");
    const fieldValue = $(field_id).text();
    const fieldState = review.fieldReview.state;
    const fieldCategory = review.category;

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

      if (category_name === "summary") {
        continue;
      }
      const category_fields = category.querySelectorAll(".field");
      for (field of category_fields) {
  const field_id = field.id.slice(6);
  const fieldValue = $(field).text();
  const found = current_review.reviews.some(review => review.key === field_id);
  const fieldState = getFieldState(field_id);
  const fieldCategory = field.getAttribute('data-category');

  if (!found && fieldState !== 'ok') {
    missingFields.push({ field_id, fieldValue, fieldCategory });
  }
}
    }


  // Display fields on the Summary page
  const summaryContainer = document.getElementById("summary");

  function clearSummaryTable() {
    while(summaryContainer.firstChild) {
      summaryContainer.firstChild.remove();
    }
  }
  function generateTable(data) {
    let table = document.createElement('table');
    table.className = 'table review-summary';

    let thead = document.createElement('thead');
    let header = document.createElement('tr');
    header.innerHTML = '<th scope="col">Status</th><th scope="col">Field Category</th><th scope="col">Field Name</th><th scope="col">Field Value</th>';
    thead.appendChild(header);
    table.appendChild(thead);

    let tbody = document.createElement('tbody');

    data.forEach(item => {
        let row = document.createElement('tr');

        let th = document.createElement('th');
        th.scope = "row";
        th.className = "status";
        if (item.fieldStatus === "Missing") {
            th.className = "status missing";
        }
        th.textContent = item.fieldStatus;
        row.appendChild(th);

        let tdFieldCategory = document.createElement('td');
        tdFieldCategory.textContent = item.fieldCategory;
        row.appendChild(tdFieldCategory);

        let tdFieldId = document.createElement('td');
        tdFieldId.textContent = item.field_id;
        row.appendChild(tdFieldId);

        let tdFieldValue = document.createElement('td');
        tdFieldValue.textContent = item.fieldValue;
        row.appendChild(tdFieldValue);

        tbody.appendChild(row);
    });

    table.appendChild(tbody);

    return table;
}


  function updateSummaryTable() {
    clearSummaryTable();
    
    let allData = [];
    allData.push(...missingFields.map(item => ({ ...item, fieldStatus: 'Missing' })));
    allData.push(...acceptedFields.map(item => ({ ...item, fieldStatus: 'Accepted' })));
    allData.push(...suggestingFields.map(item => ({ ...item, fieldStatus: 'Suggested' })));
    allData.push(...rejectedFields.map(item => ({ ...item, fieldStatus: 'Rejected' })));
    
    let table = generateTable(allData);
    summaryContainer.appendChild(table);
  }

  updateSummaryTable();
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
              if (selectedState === "ok") {
                Object.assign(current_review["reviews"][idx],
                    {
                        "category": selectedCategory,
                        "key": selectedField,
                        "fieldReview": {
                            "timestamp": Date.now(),
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
                        "category": selectedCategory,
                        "key": selectedField,
                        "fieldReview": {
                            "timestamp": Date.now(),
                              "user": "oep_reviewer", // TODO put actual username
                              "role": "reviewer",
                              "contributorValue": selectedFieldValue,
                              "comment": document.getElementById("commentarea").value,
                              "reviewerSuggestion": document.getElementById("valuearea").value,
                              "state": selectedState,
                        },
                    },
                )
                // Aktualisiere die HTML-Elemente mit den eingegebenen Werten
                var fieldElement = document.getElementById("field_" + selectedField);
                var suggestionElement = fieldElement.querySelector('.suggestion--highlight');
                var commentElement = fieldElement.querySelector('.suggestion--comment');
                suggestionElement.innerText = document.getElementById("valuearea").value;
                commentElement.innerText = document.getElementById("commentarea").value;
            }
          }
      });
    var element = document.querySelector('[aria-selected="true"]');
    var category = (element.getAttribute("data-bs-target"));
    // if field hasn't been written before, add it
    if (unique_entry){
    current_review["reviews"].push(
        {
          "category": selectedCategory,
          "key": selectedField,
          "fieldReview": {
            "timestamp": Date.now(), // TODO put actual timestamp
            "user": "oep_reviewer", // TODO put actual username
            "role": "reviewer",
            "contributorValue": selectedFieldValue,
            "comment": document.getElementById("commentarea").value,
            "reviewerSuggestion": document.getElementById("valuearea").value,
            "state": selectedState,
          },
        },
      )
      // Aktualisiere die HTML-Elemente mit den eingegebenen Werten
      var fieldElement = document.getElementById("field_" + selectedField);
      var suggestionElement = fieldElement.querySelector('.suggestion--highlight');
      var commentElement = fieldElement.querySelector('.suggestion--comment');
      suggestionElement.innerText = document.getElementById("valuearea").value;
      commentElement.innerText = document.getElementById("commentarea").value;
    }
  }

  // Color ok/suggestion/rejected
  updateFieldColor();
  checkReviewComplete();
  selectNextField();

  
  renderSummaryPageFields();
}
function getFieldState(fieldKey) {
  if (state_dict && state_dict[fieldKey] !== undefined) {
    return state_dict[fieldKey];
  } else {
    // I dont like that this shows as a error in the console
    // console.log(`Cannot get state for fieldKey "${fieldKey}" because it is not found in stateDict or stateDict itself is null.`);
    return null;
  }
}

/**
 * Checks if all fields are reviewed and activates submit button if ready
 */
function checkReviewComplete() {
  const fields = document.querySelectorAll('.field');
  for (let field of fields) {
    let fieldName = field.id.slice(6);
    const fieldState = getFieldState(fieldName);
    let reviewed = current_review["reviews"].find(review => review.key === fieldName);

    if (!reviewed && fieldState !== 'ok') {
      $('#submit_summary').addClass('disabled');
      return;
    }
  }
  $('#submit_summary').removeClass('disabled');
}


function checkFieldStates() {
  var fieldList = makeFieldList();
  for (var i = 0; i < fieldList.length; i++) {
    var fieldName = fieldList[i].replace('field_', '');
    var fieldState = state_dict[fieldName];
    if (fieldState !== 'ok') {
      return false; // Ein Feld hat nicht den Status "ok"
    }
  }
  return true; // Alle Felder haben den Status "ok"
}


/**
 * Checks if all fields are accepted and activates award badge div to finish the review.
 * Also deactivates the submitbutton.
 */
function check_if_review_finished(){
  
  if (checkFieldStates()) {
    // Creating the div with radio buttons
    var reviewerDiv = $('<div class="bg-warning" id="finish-review-div"></div>');
    var bronzeRadio = $('<input type="radio" name="reviewer-option" value="bronze"> Bronze<br>');
    var silverRadio = $('<input type="radio" name="reviewer-option" value="silver"> Silver<br>');
    var goldRadio = $('<input type="radio" name="reviewer-option" value="gold"> Gold<br>');
    var platinRadio = $('<input type="radio" name="reviewer-option" value="platin"> Platin <br>');
    var reviewText = $('<p>The review is complete. Please award a badge and finish the review.</p>');
    var finishButton = $('<button type="button" id="review-finish-button">Finish</button>');
    
    // Adding the radio buttons, text, and button to the div
    reviewerDiv.append(reviewText);
    reviewerDiv.append(bronzeRadio);
    reviewerDiv.append(silverRadio);
    reviewerDiv.append(goldRadio);
    reviewerDiv.append(platinRadio);
    reviewerDiv.append(finishButton);

    finishButton.on('click', finishPeerReview);

    if (config.review_finished !== true){
    // Displaying the div
    reviewerDiv.show();
    $('#submit_summary').prop('disabled', true);
    }
    else{
      reviewerDiv.hide(); // Hiding the div
      $('#submit_summary').hide();
      $('#peer_review-save').hide();
      // $('#review-window').hide();
      $('#review-window').css('visibility', 'hidden');
      
    }


    // Adding the div to the desired location in the document
    $('.content-finish-review').append(reviewerDiv);
  }
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
  // console.log(field_id)
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

/**
 * Hide and show revier controles once the user clicks the summary tab
 */
const summaryTab = document.getElementById('summary-tab');
const otherTabs = [
  document.getElementById('general-tab'),
  document.getElementById('spatiotemporal-tab'),
  document.getElementById('source-tab'),
  document.getElementById('license-tab'),
  document.getElementById('contributor-tab'),
  document.getElementById('resource-tab')
];
const reviewContent = document.querySelector(".review__content");
function updateTabClasses() {
    const tabNames = ['general', 'spatiotemporal', 'source', 'license', 'contributor', 'resource'];
    for (let i = 0; i < tabNames.length; i++) {
        let tabName = tabNames[i];
        let tab = document.getElementById(tabName + '-tab');
        if (!tab) continue;

        let fields = Array.from(document.querySelectorAll('#' + tabName + ' .field'));

        let allOk = true;
        for (let j = 0; j < fields.length; j++) {
            let fieldState = getFieldState(fields[j].id.replace('field_', ''));
            if (fieldState !== 'ok') {
                allOk = false;
                break;
            }
        }
        if (allOk) {
    tab.classList.add('status');
    tab.classList.add('status--done');
        } else {
            tab.classList.add('status');
        }
    }
}
window.addEventListener('DOMContentLoaded', updateTabClasses);


summaryTab.addEventListener('click', function() {
  toggleReviewControls(false);
  reviewContent.classList.toggle("tab-pane--100");
});

// Event listener for clicking the other tabs
otherTabs.forEach(function(tab) {
  tab.addEventListener('click', function() {
    toggleReviewControls(true);
    reviewContent.classList.remove("tab-pane--100");
  });
});

/**
 * Function to toggle the review controls visibility
 */ 
function toggleReviewControls(show) {
  const reviewControls = document.querySelector('.review__controls');
  if (reviewControls) {
    reviewControls.style.display = show ? '' : 'none';
  }
}

peerReview(config);


