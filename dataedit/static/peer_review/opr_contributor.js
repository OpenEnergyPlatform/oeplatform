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
  updateFieldDescription,
  highlightSelectedField,
  initializeEventBindings,
  selectState,
} from './peer_review.js';

// expose selectState for any legacy inline handlers
window.selectState = selectState;
import {selectNextField, switchCategoryTab} from "./navigation.js";
import {getFieldState, setGetFieldState} from "./state_current_review.js";
import {isEmptyValue, updateFieldColor} from "./utilities.js";
import {updateTabProgressIndicatorClasses} from "./summary.js";

let selectedField = null;
let actionsEnabled = false;

// Track whether the contributor has already interacted with a field (local UI state)
const fieldEvaluations = {};


// OK Field View Change
$('#button').bind('click', hideReviewerOptions);

// Resolve the reviewer decision for a field (independent from later contributor actions)
function getReviewerState(fieldKey) {
  // Prefer the backend-computed state dict (represents reviewer outcome)
  if (window.state_dict && Object.prototype.hasOwnProperty.call(window.state_dict, fieldKey)) {
    return window.state_dict[fieldKey];
  }

  // Fallback: derive from current_review by picking the latest entry with role === 'reviewer'
  try {
    const reviews = current_review?.reviews;
    if (!Array.isArray(reviews)) return undefined;

    const review = reviews.find((r) => r && r.key === fieldKey);
    if (!review || !review.fieldReview) return undefined;

    const frArr = Array.isArray(review.fieldReview) ? review.fieldReview : [review.fieldReview];
    const reviewerEntries = frArr.filter((x) => x && x.role === 'reviewer');
    const pickFrom = reviewerEntries.length ? reviewerEntries : frArr;

    const latest = pickFrom
      .slice()
      .sort((a, b) => (b?.timestamp ?? 0) - (a?.timestamp ?? 0))[0];

    return latest?.state;
  } catch (_e) {
    return undefined;
  }
}

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
  // Keep the original value (may be null/undefined if the template does not provide it)
  const rawFieldValue = fieldValue;

  // Ensure we always work with a string value for the UI
  const fieldValueStr = (fieldValue ?? '').toString();

  // Reset UI first; some helpers may toggle/disable controls
  clearInputFields();
  hideReviewerOptions();

  const cleanedFieldKey = fieldKey.replace(/\.\d+/g, '');

  switchCategoryTab(category);

  setSelectedField(fieldKey);

  // Keep a local copy for this module (peer_review.js stores the canonical value on window.selectedField)
  selectedField = fieldKey;

  setselectedFieldValue(fieldValueStr);
  setSelectedCategory(category);

  updateFieldDescription(cleanedFieldKey, fieldValueStr);
  highlightSelectedField(fieldKey);

  const fieldState = getReviewerState(fieldKey);
  const fieldWasEvaluated = !!fieldEvaluations[fieldKey];

  // IMPORTANT: Do NOT disable buttons just because we couldn't read the value from the DOM.
  // Some fields don't have `.value` / `data-fieldvalue` in the list, but are still reviewable.
  const isEmpty = (rawFieldValue !== null && rawFieldValue !== undefined)
    ? isEmptyValue(fieldValueStr)
    : false;

  const okBtn = document.getElementById('ok-button');
  const suggestionBtn = document.getElementById('suggestion-button');
  const rejectedBtn = document.getElementById('rejected-button');

  let enableActions = false;

  if (fieldState) {
    // Contributor rule: buttons active ONLY for reviewer suggestion fields.
    if (fieldState === 'suggestion' || fieldState === 'suggest') {
      enableActions = !isEmpty;
    } else if (fieldState === 'ok' && !fieldWasEvaluated) {
      enableActions = false;
    } else {
      enableActions = false;
    }
  } else {
    // If there is no reviewer state, keep buttons disabled.
    enableActions = false;
  }

  actionsEnabled = enableActions;

  [okBtn, suggestionBtn, rejectedBtn].forEach((btn) => {
    const buttonEl = btn;
    if (buttonEl) {
      buttonEl.disabled = !enableActions;
    }
  });
}

document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.field').forEach((field) => {
    const fieldKey = field.getAttribute('data-fieldkey');
    const reviewerState = getReviewerState(fieldKey);

    // Optional visual hint (still clickable)
    if (reviewerState !== 'suggestion') {
      field.classList.add('field-locked');
      field.setAttribute('aria-disabled', 'true');
      // DO NOT disable pointer events; contributors should be able to open/view all fields.
    }

    field.addEventListener('click', () => {
      // Some templates do not provide data-fieldvalue; fall back to rendered DOM text
      const fieldValueAttr = field.getAttribute('data-fieldvalue');
      const fieldValueDom =
        field.querySelector('.value, .field-value, .field__value, .field__content, .field-content')?.textContent;

      // Allow null if we can't reliably extract a value from the field list DOM
      const fieldValue = fieldValueAttr ?? (fieldValueDom != null ? fieldValueDom.trim() : null);

      // category is usually present; fall back to the parent tab pane id
      const categoryAttr = field.getAttribute('data-category');
      const categoryDom = field.closest('.tab-pane')?.id;
      const category = (categoryAttr ?? categoryDom ?? 'general').toString();

      
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

  // Bind action buttons once. They are enabled/disabled per-field via `actionsEnabled`.
  const okBtn = document.getElementById('ok-button');
  const suggestionBtn = document.getElementById('suggestion-button');
  const rejectedBtn = document.getElementById('rejected-button');

  const bindAction = (btn, state) => {
    if (!btn) return;
    btn.addEventListener(
      'click',
      (e) => {
        if (!actionsEnabled) {
          // Keep UI inert for non-suggestion fields
          e.preventDefault();
          e.stopPropagation();
          return;
        }

        const selectedKey = window.selectedField || selectedField;
        if (selectedKey) {
          fieldEvaluations[selectedKey] = state;
        }

        if (typeof selectState === 'function') {
          selectState(state);
        } else if (typeof window.selectState === 'function') {
          window.selectState(state);
        }
      },
      true
    );
  };

  bindAction(okBtn, 'ok');
  bindAction(rejectedBtn, 'rejected');
  bindAction(suggestionBtn, 'suggestion');
});
/**
 * Saves selected state
 * @param fieldKey
 */

export function getFieldStateForContributor(fieldKey) {
  // 1) Preferred: server-provided state_dict (if attached to window)
  if (window.state_dict && Object.prototype.hasOwnProperty.call(window.state_dict, fieldKey)) {
    return window.state_dict[fieldKey];
  }

  // 2) Fallback: derive from current_review (works even if state_dict is not on window)
  try {
    const reviews = current_review?.reviews;
    if (!Array.isArray(reviews)) return undefined;

    const review = reviews.find((r) => r && r.key === fieldKey);
    if (!review || !review.fieldReview) return undefined;

    // fieldReview can be an object or a list of objects
    const fr = review.fieldReview;
    const latest = Array.isArray(fr)
      ? fr
          .slice()
          .sort((a, b) => (b?.timestamp ?? 0) - (a?.timestamp ?? 0))[0]
      : fr;

    return latest?.state;
  } catch (_e) {
    return undefined;
  }
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
  const selectedKey = window.selectedField || selectedField;

  if (selectedState !== "ok" && selectedState !== "rejected") {
    // Get the valuearea element
    const valuearea = document.getElementById('valuearea');

    // Validate the valuearea before proceeding
    if (valuearea.value.trim() === '') {
      valuearea.setCustomValidity('Value suggestion is required');
      showToast("Error", "The value suggestion text field is required to save the field review!", "error");
      return; // Stop execution if validation fails
    } else {
      valuearea.setCustomValidity('');
    }

    valuearea.reportValidity();
  } else if (initialReviewerSuggestions[selectedKey]) { // Check if the state is "ok" and if there's a valid suggestion
    var fieldElement = document.getElementById("field_" + selectedKey);
    if (fieldElement) {
      var valueElement = fieldElement.querySelector('.value');
      if (valueElement) {
        valueElement.innerText = initialReviewerSuggestions[selectedKey];
      }
    }
  }

  if (Object.keys(current_review["reviews"]).length === 0 &&
    current_review["reviews"].constructor === Object) {
    current_review["reviews"] = [];
  }

  if (selectedKey) {
    var reviewFound = false;

    for (let i = 0; i < current_review["reviews"].length; i++) {
      if (current_review["reviews"][i]["key"] === selectedKey) {
        reviewFound = true;
        console.log("review" + current_review["reviews"][i]["fieldReview"]);
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
          "newValue": selectedState === "ok" ? initialReviewerSuggestions[selectedKey] : "",
          "comment": document.getElementById("commentarea").value,
          "additionalComment": document.getElementById("comments").value,
          "reviewerSuggestion": document.getElementById("valuearea").value,
          "state": selectedState,
        });
        // Aktualisiere die HTML-Elemente mit den eingegebenen Werten
        var fieldElement = document.getElementById("field_" + selectedKey);
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
        "key": selectedKey,
        "fieldReview": [
          {
            "timestamp": Date.now(),
            "user": "oep_contributor", // TODO put actual username
            "role": "contributor",
            "contributorValue": selectedFieldValue,
            "newValue": selectedState === "ok" ? initialReviewerSuggestions[selectedKey] : "",
            "comment": document.getElementById("commentarea").value,
            "additionalComment": document.getElementById("comments").value,
            "reviewerSuggestion": document.getElementById("valuearea").value,
            "state": selectedState,
          },
        ],
      });
      // Aktualisiere die HTML-Elemente mit den eingegebenen Werten
      var fieldElement = document.getElementById("field_" + selectedKey);
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



/**
 * Shows reviewer Comment and Suggestion Input options
 */
function showReviewerOptions() {
  $("#reviewer_remarks").removeClass('d-none');
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

  if (!stateDict) {
    return "0.00";
  }

  for (let key in stateDict) {
    const fieldElement = document.getElementById(`field_${key}`);
    if (!fieldElement) continue;

    const fieldValue = $(fieldElement).find('.value').text().replace(/\s+/g, ' ').trim();
    if (!isEmptyValue(fieldValue)) {
      totalCount++;
      if (stateDict[key] === "ok") {
        okCount++;
      }
    }
  }

  const percentage = totalCount === 0 ? 0 : (okCount / totalCount) * 100;
  return percentage.toFixed(2);
}

function updatePercentageDisplay() {
  if (!window.state_dict) return;

  const percentage = parseFloat(calculateOkPercentage(window.state_dict));

  // Circle elements
  const circle = document.getElementById("okProgressCircle");
  const textEl =
    document.getElementById("okPercentageText") ||
    document.getElementById("percentageDisplay");

  if (circle) {
    // radius must match the SVG circle (r="52" in CSS)
    const radius = 52;
    const circumference = 2 * Math.PI * radius;

    // ensure dasharray is set
    circle.style.strokeDasharray = `${circumference}`;

    const offset = circumference - (percentage / 100) * circumference;
    circle.style.strokeDashoffset = `${offset}`;
  }

  if (textEl) {
    textEl.textContent = `${percentage.toFixed(2)}%`;
  }
}

// Expose for other modules (e.g. summary.js)
window.updatePercentageDisplay = updatePercentageDisplay;
