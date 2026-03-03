// SPDX-FileCopyrightText: 2025 Bryan Lancien <https://github.com/bmlancien> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Daryna Barabanova <https://github.com/Darynarli> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Stephan Uller <https://github.com/steull> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 user <https://github.com/Darynarli> © Reiner Lemoine Institut
//
// SPDX-License-Identifier: AGPL-3.0-or-later


import * as common from './peer_review.js';
import {
  hideReviewerOptions,
  setSelectedField,
  setselectedFieldValue,
  clearInputFields,
  selectedState,
  selectedFieldValue,
  current_review,
  selectedCategory,
  setSelectedCategory,
  checkReviewComplete,
  showToast,
  updateFieldDescription,
  highlightSelectedField, initializeEventBindings,
} from './peer_review.js';
import {selectNextField, switchCategoryTab} from "./navigation.js";
import {getFieldState, setGetFieldState} from "./state_current_review.js";
import {updateFieldColor} from "./utilities.js";
import {renderSummaryPageFields, updateTabProgressIndicatorClasses} from "./summary.js";
window.selectState = common.selectState;
var selectedField;

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
  updateTabProgressIndicatorClasses();
  updatePercentageDisplay();
}

/**
 * Save peer review to backend
 */
function savePeerReview() {
  $('#peer_review-save').removeClass('d-none');
  json = JSON.stringify({reviewType: 'save', reviewData: current_review});
  sendJson("POST", config.url_peer_review, json).then(function() {
    window.location = config.url_table;
  }).catch(function(err) {
    // TODO evaluate error, show user message
    $('#peer_review-save').addClass('d-none');
    alert(getErrorMsg(err));
  });
}

function click_field(fieldKey, fieldValue, category) {

  const cleanedFieldKey = fieldKey.replace(/\.\d+/g, '');

  switchCategoryTab(category);

  setSelectedField(fieldKey);

  setselectedFieldValue(fieldValue);
  setSelectedCategory(category);

  updateFieldDescription(cleanedFieldKey, fieldValue);
  highlightSelectedField(fieldKey);

  const fieldState = getFieldState(fieldKey);

  if (fieldState === 'ok' || !fieldState || fieldState === 'rejected') {
    ["ok-button", "rejected-button"].forEach(btn => {
      document.getElementById(btn).disabled = true;
    });
  } else if (fieldState === 'suggestion') {
    ["ok-button", "rejected-button"].forEach(btn => {
      document.getElementById(btn).disabled = false;
    });
  } else {
    ["ok-button", "rejected-button", "suggestion-button"].forEach(btn => {
      document.getElementById(btn).disabled = false;
    });
  }

  clearInputFields();
  hideReviewerOptions();
}

function clearInputFields() {
  document.getElementById("valuearea").value = "";
  document.getElementById("commentarea").value = "";
}

/**
 * Switch to the category tab if needed
 */
function switchCategoryTab(category) {
  const currentTab = document.querySelector('.tab-pane.active'); // Get the currently active tab
  const tabIdForCategory = getCategoryToTabIdMapping()[category];
  if (currentTab.getAttribute('id') !== tabIdForCategory) {
    // The clicked field does not belong to the current tab, switch to the next tab
    const targetTab = document.getElementById(tabIdForCategory);
    if (targetTab) {
      // The target tab exists, click the tab link to switch to it
      targetTab.click();
    }
  }
}

/**
 * Function to provide the mapping of category to the correct tab ID
 */
function getCategoryToTabIdMapping() {
  // Define the mapping of category to tab ID
  const mapping = {
    'general': 'general-tab',
    'spatial': 'spatiotemporal-tab',
    'temporal': 'spatiotemporal-tab',
    'source': 'source-tab',
    'license': 'license-tab',
  };
  return mapping;
}

      click_field(fieldKey, fieldValue, category);
    });
  });
});
/**
 * Saves selected state
 * @param fieldKey
 */

export function getFieldStateForContributor(fieldKey) {
  // This function gets the state of a field
  return state_dict[fieldKey];

  function selectState(state) { // eslint-disable-line no-unused-vars
  selectedState = state;
  updateClientStateDict(fieldKey = selectedField, state = state);
}

function updateClientStateDict(fieldKey, state) {
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
  const categoriesMap = {};

  function addFieldToCategory(category, field) {
    if (!categoriesMap[category]) categoriesMap[category] = [];
    categoriesMap[category].push(field);

    // Removed incorrect use of 'continue' and refactored loop variable declaration
    const category_fields = category.querySelectorAll(".field");
    for (const field of category_fields) {
      const field_id = field.id.slice(6);
      const fieldValue = $(field).find('.value').text().replace(/\s+/g, ' ').trim();
      const found = current_review.reviews.some((review) => review.key === field_id);
      const fieldState = getFieldState(field_id);
      const fieldCategory = field.getAttribute('data-category');
      let fieldName = field_id.replace(/\./g, ' ');
      const uniqueFieldIdentifier = `${fieldName}-${fieldCategory}`;

      if (isEmptyValue(fieldValue) && !processedFields.has(uniqueFieldIdentifier)) {
        emptyFields.push({ fieldName, fieldValue, fieldCategory: "emptyFields", fieldSuggestion });
      } else if (!found && fieldState !== 'ok' && fieldState !== 'rejected' && !isEmptyValue(fieldValue)) {
        missingFields.push({ fieldName, fieldValue, fieldCategory });
        processedFields.add(uniqueFieldIdentifier);
      }
    }
  }

  const fields = document.querySelectorAll('.field');
  fields.forEach(field => {
    const field_id = field.id.slice(6);
    const fieldValue = $(field).find('.value').text().trim();
    const fieldState = getFieldState(field_id);
    const fieldCategory = field.getAttribute('data-category');
    let fieldName = field_id.replace(/\./g, ' ');
    if (fieldCategory !== "general") {
      fieldName = fieldName.split(' ').slice(1).join(' ');
    }

    let fieldStatus = isEmptyValue(fieldValue) ? 'Empty' :
                      fieldState === 'ok' ? 'Accepted' :
                      fieldState === 'rejected' ? 'Rejected' : 'Missing';

    addFieldToCategory(fieldCategory, { fieldName, fieldValue, fieldStatus });
  });

  const summaryContainer = document.getElementById("summary");
  summaryContainer.innerHTML = '';

  const tabsNav = document.createElement('ul');
  tabsNav.className = 'nav nav-tabs';

  const tabsContent = document.createElement('div');
  tabsContent.className = 'tab-content';

  let firstTab = true;

  for (const category in categoriesMap) {
    const tabId = `tab-${category}`;

    const navItem = document.createElement('li');
    navItem.className = 'nav-item';
    navItem.innerHTML = `<button class="nav-link${firstTab ? ' active' : ''}" data-bs-toggle="tab" data-bs-target="#${tabId}">${category}</button>`;
    tabsNav.appendChild(navItem);

    const tabPane = document.createElement('div');
    tabPane.className = `tab-pane fade${firstTab ? ' show active' : ''}`;
    tabPane.id = tabId;

    const fields = categoriesMap[category];
    const singleFields = [];
    const groupedFields = {};

    fields.forEach(field => {
      const words = field.fieldName.split(' ');
      if (words.length === 1) {
        singleFields.push(field);
      } else {
        const prefix = words[0];
        const rest = words.slice(1);
        const indices = rest.filter(word => !isNaN(word));
        const nameWithoutIndices = rest.filter(word => isNaN(word)).join(' ');

        if (!groupedFields[prefix]) groupedFields[prefix] = { indexed: {}, noIndex: [] };

        if (indices.length > 0) {
          const indexKey = indices.map(num => (parseInt(num, 10) + 1)).join('.');
          if (!groupedFields[prefix].indexed[indexKey]) groupedFields[prefix].indexed[indexKey] = [];
          groupedFields[prefix].indexed[indexKey].push({ ...field, fieldName: nameWithoutIndices });
        } else {
          groupedFields[prefix].noIndex.push({ ...field, fieldName: nameWithoutIndices });
        }

        let th = document.createElement('th');
        th.scope = "row";
        th.className = "status";
        if (item.fieldStatus === "Pending") {
          th.className = "status missing";
        }
      } // <-- Add closing brace here for else block
    }); // <-- Closing fields.forEach

    if (singleFields.length > 0) {
      const table = document.createElement('table');
      table.className = 'table review-summary';
      table.innerHTML = `
        <thead><tr><th>Status</th><th>Field Name</th><th>Field Value</th></tr></thead>
        <tbody>${singleFields.map(f => `
          <tr>
            <td class="status ${f.fieldStatus.toLowerCase()}">${f.fieldStatus}</td>
            <td>${f.fieldName}</td>
            <td>${f.fieldValue}</td>
          </tr>`).join('')}
        </tbody>`;
      tabPane.appendChild(table);
    }

    if (Object.keys(groupedFields).length > 0) {
      const accordionContainer = document.createElement('div');
      accordionContainer.className = 'accordion';
      accordionContainer.id = `accordion-${category}`;

      let accordionIndex = 0;
      for (const prefix in groupedFields) {
        const accordionItem = document.createElement('div');
        accordionItem.className = 'accordion-item';
        const headingId = `heading-${category}-${accordionIndex}`;
        const collapseId = `collapse-${category}-${accordionIndex}`;

        const { noIndex, indexed } = groupedFields[prefix];

        let innerHTML = '';

        if (noIndex.length > 0) {
          innerHTML += `
            <table class="table table-sm table-bordered">
              <thead><tr><th>Status</th><th>Field Name</th><th>Field Value</th></tr></thead>
              <tbody>${noIndex.map(f => `
                <tr>
                  <td class="status ${f.fieldStatus.toLowerCase()}">${f.fieldStatus}</td>
                  <td>${f.fieldName}</td>
                  <td>${f.fieldValue}</td>
                </tr>`).join('')}
              </tbody>
            </table>`;
        }

        if (Object.keys(indexed).length > 0) {
          const subAccordionId = `subAccordion-${category}-${accordionIndex}`;
          innerHTML += `<div class="accordion" id="${subAccordionId}">`;

          Object.entries(indexed).forEach(([idx, idxFields], idxAccordionIndex) => {
            const idxHeadingId = `idxHeading-${category}-${accordionIndex}-${idxAccordionIndex}`;
            const idxCollapseId = `idxCollapse-${category}-${accordionIndex}-${idxAccordionIndex}`;

            const tabLabel = ['source', 'license'].includes(category) ? 'fields' : `${prefix} ${idx}`;

            innerHTML += `
              <div class="accordion-item">
                <h2 class="accordion-header" id="${idxHeadingId}">
                  <button class="accordion-button collapsed" data-bs-toggle="collapse" data-bs-target="#${idxCollapseId}">
                    ${tabLabel}
                  </button>
                </h2>
                <div id="${idxCollapseId}" class="accordion-collapse collapse" data-bs-parent="#${subAccordionId}">
                  <div class="accordion-body">
                    <table class="table table-sm table-bordered">
                      <thead><tr><th>Status</th><th>Field Name</th><th>Field Value</th></tr></thead>
                      <tbody>${idxFields.map(f => `
                        <tr>
                          <td class="status ${f.fieldStatus.toLowerCase()}">${f.fieldStatus}</td>
                          <td>${f.fieldName}</td>
                          <td>${f.fieldValue}</td>
                        </tr>`).join('')}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>`;
          });

          innerHTML += `</div>`;
        }

    tabsContent.appendChild(tabPane);
    firstTab = false;
  }
  const viewsNavItem = document.createElement('li');
  viewsNavItem.className = 'nav-item';
  viewsNavItem.innerHTML = '<button class="nav-link" data-bs-toggle="tab" data-bs-target="#tab-views">views</button>';


  tabsNav.appendChild(viewsNavItem);

  const viewsPane = document.createElement('div');
  viewsPane.className = 'tab-pane fade';
  viewsPane.id = 'tab-views';

  const allFields = Object.entries(categoriesMap).flatMap(([category, fields]) =>
    fields.map(f => ({...f, category}))
  );

  viewsPane.innerHTML =
    <table class="table review-summary">
      <thead>
        <tr><th>Status</th><th>Category</th><th>Field Name</th><th>Field Value</th></tr>
      </thead>
      <tbody>${allFields.map(f =>
        <tr>
          <td class="status ${f.fieldStatus.toLowerCase()}">${f.fieldStatus}</td>
          <td>${f.category}</td>
          <td>${f.fieldName}</td>
          <td>${f.fieldValue}</td>
        </tr>).join('')}
      </tbody>
    </table>;

  tabsContent.appendChild(viewsPane);
  summaryContainer.appendChild(tabsNav);
  summaryContainer.appendChild(tabsContent);
  updateTabProgressIndicatorClasses();
}

/**
 * Creates an HTML list of fields with their categories
 * @param {Array} fields Array of field objects
 * @returns {string} HTML list of fields
 */
function createFieldList(fields) {
  return `
    <ul>
      ${fields.map((field) => `<li>${field.fieldCategory}: ${field.fieldValue}</li>`).join('')}
    </ul>
  `;
}

// // Function to show the error toast
// function showErrorToast(liveToast) {
//   liveToast.show();
// }

function showToast(title, message, type) {
  var toast = document.getElementById('liveToast');
  var toastTitle = document.getElementById('toastTitle');
  var toastBody = document.getElementById('toastBody');

  // Update the toast's header and body based on the type
  if (type === 'error') {
    toast.classList.remove('bg-success');
    toast.classList.add('bg-danger');
  } else if (type === 'success') {
    toast.classList.remove('bg-danger');
    toast.classList.add('bg-success');
  }

  // Set the title and body text
  toastTitle.textContent = title;
  toastBody.textContent = message;

  var bsToast = new bootstrap.Toast(toast);
  bsToast.show();
}

setGetFieldState(getFieldStateForContributor);

function saveEntrancesForContributor() {

  if (selectedState !== "ok" && selectedState !== "rejected") {
    // Get the valuearea element
    const valuearea = document.getElementById('valuearea');

    // const validityState = valuearea.validity;

    // Validate the valuearea before proceeding
    if (valuearea.value.trim() === '') {
      valuearea.setCustomValidity('Value suggestion is required');
      showToast("Error", "The value suggestion text field is required to save the field review!", "error");
      return; // Stop execution if validation fails
    } else {
      valuearea.setCustomValidity('');
    }

    valuearea.reportValidity();
  } else if (initialReviewerSuggestions[selectedField]) { // Check if the state is "ok" and if there's a valid suggestion
    var fieldElement = document.getElementById("field_" + selectedField);
    if (fieldElement) {
      var valueElement = fieldElement.querySelector('.value');
      if (valueElement) {
        valueElement.innerText = initialReviewerSuggestions[selectedField];
      }
    }
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
        // console.log("review" + current_review.reviews["reviews"][i]["fieldReview"]) //undefined "reviews"
        console.log("review" + current_review["reviews"][i]["fieldReview"]) //undefined "reviews"
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
          "newValue": selectedState === "ok" ? initialReviewerSuggestions[selectedField] : "",
          "comment": document.getElementById("commentarea").value,
          "additionalComment": document.getElementById("comments").value,
          "reviewerSuggestion": document.getElementById("valuearea").value,
          "state": selectedState,
        });
        // Aktualisiere die HTML-Elemente mit den eingegebenen Werten
        var fieldElement = document.getElementById("field_" + selectedField);
        var suggestionElement = fieldElement.querySelector('.suggestion--highlight');
        var commentElement = fieldElement.querySelector('.suggestion--comment');
        // var additionalCommentElement = fieldElement.querySelector('.suggestion--additional-comment');
        suggestionElement.innerText = document.getElementById("valuearea").value;
        commentElement.innerText = document.getElementById("commentarea").value;
        // additionalCommentElement.innerText = document.getElementById("comments").value;
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
            "newValue": selectedState === "ok" ? initialReviewerSuggestions[selectedField] : "",
            "comment": document.getElementById("commentarea").value,
            "additionalComment": document.getElementById("comments").value,
            "reviewerSuggestion": document.getElementById("valuearea").value,
            "state": selectedState,
          },
        ],
      });
      // Aktualisiere die HTML-Elemente mit den eingegebenen Werten
      var fieldElement = document.getElementById("field_" + selectedField);
      var suggestionElement = fieldElement.querySelector('.suggestion--highlight');
      var commentElement = fieldElement.querySelector('.suggestion--comment');
      var additionalCommentElement = fieldElement.querySelector('.suggestion--additional-comment'); // For new comment

      suggestionElement.innerText = document.getElementById("valuearea").value;
      commentElement.innerText = document.getElementById("commentarea").value;
      additionalCommentElement.innerText = document.getElementById("comments").value; // Update new comment

    }
  }
    document.getElementById("comments").value = "";
  updateFieldColor();
  checkReviewComplete();
  selectNextField();
  renderSummaryPageFields();
  updateTabProgressIndicatorClasses();
  updatePercentageDisplay() ;
}
initializeEventBindings(saveEntrancesForContributor);
}}}

/**
 *
 * Checks if all fields are reviewed and activates submit button if ready
 */
function checkReviewComplete() {
  const fields = document.querySelectorAll('.field');
  for (let field of fields) {
    let fieldName = field.id.slice(6);
    const fieldValue = $(field).find('.value').text().replace(/\s+/g, ' ').trim();
    const fieldState = getFieldState(fieldName);
    let reviewed = current_review["reviews"].find((review) => review.key === fieldName);

    if (!reviewed && fieldState !== 'ok' && !isEmptyValue(fieldValue)) {
      $('#submit_summary').addClass('disabled');
      return;
    }
  }
  $('#submit_summary').removeClass('disabled');
  showToast("Success", "You have reviewed all fields and can submit the review to get feedback!", 'success');
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
  } else {
    $(submitButton).addClass('btn-danger');
  }
}


function updateTabProgressIndicatorClasses() {
  const tabNames = ['general', 'spatiotemporal', 'source', 'license'];

  for (let i = 0; i < tabNames.length; i++) {
    let tabName = tabNames[i];
    let tab = document.getElementById(tabName + '-tab');
    if (!tab) continue;

    let fieldsInTab = Array.from(document.querySelectorAll('#' + tabName + ' .field'));

    let allOk = fieldsInTab.every((field) => {
      const fieldValue = $(field).find('.value').text().replace(/\s+/g, ' ').trim();
      return isEmptyValue(fieldValue) || field.classList.contains('field-ok');
    });

    if (allOk) {
      tab.classList.add('status--done');
    } else {
      tab.classList.add('status');
    }
  }
}

function updateTabClasses() {
  const tabNames = ['general', 'spatiotemporal', 'source', 'license'];
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
window.addEventListener('DOMContentLoaded', function() {
    updateTabClasses();
    updatePercentageDisplay() ;
});

function calculateOkPercentage(stateDict) {
  let totalCount = 0;
  let okCount = 0;

  for (let key in stateDict) {
    let fieldValue = $(document.getElementById(`field_${key}`)).find('.value').text().replace(/\s+/g, ' ').trim();
    if (!isEmptyValue(fieldValue)) {
      totalCount++;
      if (stateDict[key] === "ok") {
        okCount++;
      }
    }
  }

  return totalCount === 0 ? 0 : (okCount / totalCount) * 100;
}

function updatePercentageDisplay() {
  const percentage = calculateOkPercentage(state_dict);
  document.getElementById("percentageDisplay").textContent = percentage.toFixed(2);
}


/**
 * Hide and show revier controles once the user clicks the summary tab
 */
console.log('Script is running...');

document.addEventListener('DOMContentLoaded', function() {
  // console.log('DOM fully loaded and parsed');

  const summaryTab = document.getElementById('summary-tab');
  const otherTabs = [
    document.getElementById('general-tab'),
    document.getElementById('spatiotemporal-tab'),
    document.getElementById('source-tab'),
    document.getElementById('license-tab'),
  ];
  const reviewContent = document.querySelector(".review__content");

  console.log('Summary Tab:', summaryTab);
  console.log('Other Tabs:', otherTabs);
  console.log('Review Content:', reviewContent);

  if (summaryTab && reviewContent) {
    summaryTab.addEventListener('click', function() {
      toggleReviewControls(false);
      reviewContent.classList.toggle("tab-pane--100");
    });
  } else {
    console.error('Summary tab or review content not found');
  }

  otherTabs.forEach(function(tab, index) {
    if (tab) {
      tab.addEventListener('click', function() {
        toggleReviewControls(true);
        reviewContent.classList.remove("tab-pane--100");
      });
    } else {
      console.error('Tab at index ' + index + ' not found');
    }
  });

  function toggleReviewControls(show) {
    const reviewControls = document.querySelector('.review__controls');
    console.log('Review Controls:', reviewControls);
    if (reviewControls) {
      reviewControls.style.display = show ? '' : 'none';
    }
  }
});


peerReview(config);
