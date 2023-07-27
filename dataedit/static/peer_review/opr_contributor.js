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
// Submit review (not visible to reviewer)
$('#submit_summary').bind('click', submitPeerReview);
// save the current review (not visible to reviewer)
$('#peer_review-save').bind('click', savePeerReview);
// Cancel review
$('#peer_review-cancel').bind('click', cancelPeerReview);
// OK Field View Change
$('#button').bind('click', hideReviewerOptions);

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
    headers: { "X-CSRFToken": token },
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

  //   (function init() {
  //     $('#peer_review-loading').removeClass('d-none');
  //     config.form = $('#peer_review-form');
  //   })();
  selectNextField();
  renderSummaryPageFields();
}

/**
 * Save peer review to backend
 */
function savePeerReview() {
  $('#peer_review-save').removeClass('d-none');
  json = JSON.stringify({ reviewType: 'save', reviewData: current_review });
  sendJson("POST", config.url_peer_review, json).then(function () {
    window.location = config.url_table;
  }).catch(function (err) {
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
  sendJson("POST", config.url_peer_review, json).then(function () {
    window.location = config.url_table;
  }).catch(function (err) {
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

function getFieldState(fieldKey) {
  // This function gets the state of a field
  return state_dict[fieldKey];
}

function click_field(fieldKey, fieldValue, category) {
  const cleanedFieldKey = fieldKey.replace(/\.\d+/g, '');
  selectedField = fieldKey;
  selectedFieldValue = fieldValue;
  selectedCategory = category;
  const selectedName = document.querySelector("#review-field-name");
  selectedName.textContent = cleanedFieldKey + " " + fieldValue;
  const fieldDescriptionsElement = document.getElementById("field-descriptions");
  const reviewItem = document.querySelectorAll('.review__item');
  let selectedDivId = 'field_' + fieldKey;
  let selectedDiv = document.getElementById(selectedDivId);
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
    fieldInfoText += '<div class="reviewer-item__row">Does it comply with the required ' + fieldInfo.title + ' description convention?</div></div>';
    fieldDescriptionsElement.innerHTML = fieldInfoText;
  } else {
    fieldDescriptionsElement.textContent = "No description found";
  }
  // console.log("Category:", category, "Field key:", cleanedFieldKey, "Data:", fieldDescriptionsData[cleanedFieldKey]);
  const fieldState = getFieldState(fieldKey);

  if (fieldState === 'ok' || !fieldState) {
    document.getElementById("ok-button").disabled = true;
    document.getElementById("rejected-button").disabled = true;
  } else if (fieldState === 'suggestion' || fieldState === 'rejected') {
    document.getElementById("ok-button").disabled = false;
    document.getElementById("rejected-button").disabled = false;
  }

  // Set selected / not selected style on metadata fields
  reviewItem.forEach(function (div) {
    div.style.backgroundColor = '';
  });
  if (selectedDiv) {
    if (!selectedDiv.classList.contains('field-ok')) {
      selectedDiv.style.backgroundColor = '#F6F9FB';
    }
  }

  clearInputFields();

}

function clearInputFields() {
  document.getElementById("valuearea").value = "";
  document.getElementById("commentarea").value = "";
}



/**
 * Creates List of all fields from html elements
 */
function makeFieldList() {
  var fieldElements = [];
  $(".field").each(function () { fieldElements.push(this.id) });
  //alert(fieldElements[14]);
  return fieldElements;
}

/**
 * Clears User Input fields
 */


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
function selectPreviousField() {
  var fieldList = makeFieldList();
  var prev = fieldList.indexOf('field_' + selectedField) - 1
  selectField(fieldList, prev);
}

/**
 * Clicks a Field after checking it exists
 */
function selectField(fieldList, field) {
  if (field >= 0 && field < fieldList.length) {
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
 * Displays fields based on selected category
 */
function renderSummaryPageFields() {
  const acceptedFields = [];
  const rejectedFields = [];
  const missingFields = [];

  if (state_dict && Object.keys(state_dict).length > 0) {
    const fields = document.querySelectorAll('.field');
    for (let field of fields) {
      let field_id = field.id.slice(6);
      const fieldValue = $(field).text();
      const fieldState = getFieldState(field_id);
      console.log(field_id + fieldState)
      const fieldCategory = field.getAttribute('data-category');  // Получаем категорию поля
      if (fieldState === 'ok') {
        acceptedFields.push({ field_id, fieldValue, fieldCategory });
      }
      // TODO: The following line duplicates enties in the summary tab
      // else if (fieldState === 'suggestion' || fieldState === 'rejected') {
      // missingFields.push({ field_id, fieldValue, fieldCategory });
      // console.log("Hello", missingFields)
      // }
    }
  }

  for (const review of current_review.reviews) {
    const field_id = `#field_${review.key}`.replaceAll(".", "\\.");
    const fieldValue = $(field_id).text();
    const isAccepted = review.fieldReview.some(fieldReview => fieldReview.state === 'ok');
    const isRejected = review.fieldReview.some(fieldReview => fieldReview.state === 'rejected');

    const fieldCategory = review.category;

    if (isAccepted) {
      acceptedFields.push({ field_id, fieldValue, fieldCategory });
    } else if (isRejected) {
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
    while (summaryContainer.firstChild) {
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

// Function to show the error toast
function showErrorToast(liveToast) {
  liveToast.show();
}


/**
 * Saves field review to current review list
 */
function saveEntrances() {
  if (selectedState !== "ok") {
    const valuearea = document.getElementById('valuearea');
    const liveToastBtn = document.getElementById('liveToastBtn');
    const liveToast = new bootstrap.Toast(document.getElementById('liveToast'));
    if (valuearea.value.trim() === '') {
      valuearea.setCustomValidity('Value suggestion is required');
      showErrorToast(liveToast);
      return; // Stop execution if validation fails
    } else {
      valuearea.setCustomValidity('');
    }
    valuearea.reportValidity();
  }

  if (Object.keys(current_review["reviews"]).length === 0 &&
    current_review["reviews"].constructor === Object) {
    current_review["reviews"] = [];
  }

  if (selectedField) {
    var reviewFound = false;
    for (let i = 0; i < current_review["reviews"].length; i++) {
      if (current_review["reviews"][i]["key"] === selectedField) {
        reviewFound = true;
        if (!Array.isArray(current_review["reviews"][i]["fieldReview"])) {
          current_review["reviews"][i]["fieldReview"] = [current_review["reviews"][i]["fieldReview"]];
        }
        var element = document.querySelector('[aria-selected="true"]');
        var category = element.getAttribute("data-bs-target");
        current_review["reviews"][i]["fieldReview"].push({
          "timestamp": Date.now(),
          "user": "oep_contributor", // TODO put actual username
          "role": "contributor",
          "contributorValue": selectedFieldValue,
          "newValue": selectedState === "ok" ? initialReviewerSuggestion : "",
          "comment": document.getElementById("commentarea").value,
          "reviewerSuggestion": document.getElementById("valuearea").value,
          "state": selectedState,
        });

        // Update HTML elements with entered values
        var fieldElement = document.getElementById("field_" + selectedField);
        var suggestionElement = fieldElement.querySelector('.suggestion--highlight');
        var commentElement = fieldElement.querySelector('.suggestion--comment');
        suggestionElement.innerText = document.getElementById("valuearea").value;
        commentElement.innerText = document.getElementById("commentarea").value;
        break;
      }
    }

    if (!reviewFound) {
      var element = document.querySelector('[aria-selected="true"]');
      var category = element.getAttribute("data-bs-target");
      current_review["reviews"].push({
        "category": selectedCategory,
        "key": selectedField,
        "fieldReview": [
          {
            "timestamp": Date.now(),
            "user": "oep_contributor", // TODO put actual username
            "role": "contributor",
            "contributorValue": selectedFieldValue,
            "newValue": selectedState === "ok" ? initialReviewerSuggestion : "",
            "comment": document.getElementById("commentarea").value,
            "reviewerSuggestion": document.getElementById("valuearea").value,
            "state": selectedState,
          }
        ]
      });
      // Update HTML elements with entered values
      var fieldElement = document.getElementById("field_" + selectedField);
      var suggestionElement = fieldElement.querySelector('.suggestion--highlight');
      var commentElement = fieldElement.querySelector('.suggestion--comment');
      suggestionElement.innerText = document.getElementById("valuearea").value;
      commentElement.innerText = document.getElementById("commentarea").value;
    }
  }

  updateFieldColor();
  checkReviewComplete();
  selectNextField();
  renderSummaryPageFields();
}


/**
 *
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




/**
 * Shows reviewer Comment and Suggestion Input options
 */
function showReviewerOptions() {
  $("#reviewer_remarks").removeClass('d-none');
}

/**
 * Hides reviewer Comment and Suggestion Input options
 */
function hideReviewerOptions() {
  $("#reviewer_remarks").addClass('d-none');
}

/**
 * Colors Field based on Reviewer input
 */
function updateFieldColor() {
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
function updateSubmitButtonColor() {
  // Color Save comment / new value
  $(submitButton).removeClass('btn-warning');
  $(submitButton).removeClass('btn-danger');
  if (selectedState == "suggestion") {
    $(submitButton).addClass('btn-warning');
  }
  else {
    $(submitButton).addClass('btn-danger');
  }
}

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

// Event listener for clicking the "Summary" tab button
summaryTab.addEventListener('click', function () {
  toggleReviewControls(false);
  reviewContent.classList.toggle("tab-pane--100");
});

// Event listener for clicking the other tabs
otherTabs.forEach(function (tab) {
  tab.addEventListener('click', function () {
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
