// SPDX-FileCopyrightText: 2025 Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

import {
  checkFieldStates,
  check_if_review_finished
} from './opr_reviewer_logic.js';
import {renderSummaryPageFields, updateSubmitButtonColor, updateTabProgressIndicatorClasses} from "./summary.js";
import {selectNextField} from "./navigation.js";
import {isEmptyValue, sendJson, getCookie} from "./utilities.js";
import {getFieldState, updateClientStateDict} from "./state_current_review.js";

window.selectedField = window.selectedField ?? null;
export let selectedFieldValue=null;

export function setSelectedField(fieldKey) {
  selectedField = fieldKey;
}
export function setselectedFieldValue(fieldValue) {
  selectedFieldValue = fieldValue;
}
export let selectedState;
export let selectedCategory;

export function setSelectedCategory(value) {
  selectedCategory = value;
}

export let current_review;

export function initCurrentReview(config) {
  current_review = {
    topic: config.topic,
    table: config.table,
    dateStarted: null,
    dateFinished: null,
    metadataVersion: "v1.6.0",
    reviews: [],
    reviewFinished: false,
    grantedBadge: null,
    metaMetadata: {
      reviewVersion: "OEP-0.1.0",
      metadataLicense: {
        name: "CC0-1.0",
        title: "Creative Commons Zero v1.0 Universal",
        path: "https://creativecommons.org/publicdomain/zero/1.0/",
      },
    },
  };
  window.current_review = current_review;
}

export function initializeEventBindings(saveEntrancesFn) {
  // Submit field review
  $('#submitButton').bind('click', saveEntrancesFn);
  $('#submitCommentButton').bind('click', saveEntrancesFn);
  $('#submitButton').bind('click', hideReviewerOptions);
  $('#submitCommentButton').bind('click', hideReviewerOptions);

  // Submit review (visible to contributor)
  $('#submit_summary').bind('click', submitPeerReview);
  // save the current review (not visible to contributor)
  $('#peer_review-save').bind('click', savePeerReview);
  // Cancel review
  $('#peer_review-cancel').bind('click', cancelPeerReview);
  $('#ok-button').bind('click', saveEntrancesFn);

  // Suggestion Field View Change
  $('#suggestion-button').bind('click', showReviewerOptions);
  $('#suggestion-button').bind('click', updateSubmitButtonColor);

  // Reject Field View Change
  $('#rejected-button').bind('click', showReviewerCommentsOptions);
  $('#rejected-button').bind('click', updateSubmitButtonColor);

  // Clear Input fields when new tab is selected
  $('.nav-link').click(clearInputFields);
}

/**
 * Returns name from cookies
 * @param {string} name Key to look up in cookie
 * @returns {value} Cookie value
 */

/**
 * Get CSRF Token
 * @returns {string} CSRF Token
 */
export function getCsrfToken() {
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

export function getAllFieldsAndValues() {
  const fields = document.querySelectorAll('.field');
  const fieldList = [];

  fields.forEach(field => {
    const fieldName = field.id.slice(6);
    const fieldValue = $(field).find('.value').text().replace(/\s+/g, ' ').trim();
    fieldList.push({ fieldName, fieldValue });
  });

  return fieldList;
}
/**
 * Reads error message from response
 * @param {json} response Get or post request
 * @returns {string} Response error message
 */
export function getErrorMsg(response) {
  try {
    var response_msg = (
      'Upload failed: ' + JSON.parse(response.responseJSON).error
    );
  } catch (e) {
    console.log(response);
    var response_msg = response.responseText;
  }
  return response_msg;
}

export function peerReview(config, checkState = false) {
  /*
    TODO: Show loading icon if peer review page is loaded
  */

  selectNextField();
  renderSummaryPageFields();
  updateTabProgressIndicatorClasses();

  if (checkState && typeof window.state_dict !== 'undefined') {
    check_if_review_finished();
  }
}

export function savePeerReview() {
  $('#peer_review-save').removeClass('d-none');
  let json = JSON.stringify({reviewType: 'save', reviewData: current_review});
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
export function submitPeerReview() {
  $('#peer_review-submitting').removeClass('d-none');
  let json = JSON.stringify({reviewType: 'submit', reviewData: current_review});
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
export function cancelPeerReview() {
  window.location = config.url_table;
}

export function updateFieldDescription(cleanedFieldKey, fieldValue) {
  const fieldDescriptionsElement = document.getElementById("field-descriptions");
  const selectedName = document.querySelector("#review-field-name");

  selectedName.textContent = cleanedFieldKey + " " + fieldValue;

  if (fieldDescriptionsData[cleanedFieldKey]) {
    const fieldInfo = fieldDescriptionsData[cleanedFieldKey];
    let fieldInfoText = '<div class="reviewer-item">';

    if (fieldInfo.title) {
      fieldInfoText += `<div class="reviewer-item__row"><h2 class="reviewer-item__title">${fieldInfo.title}</h2></div>`;
    }
    if (fieldInfo.description) {
      fieldInfoText += `<div class="reviewer-item__row"><div class="reviewer-item__key">Description:</div><div class="reviewer-item__value">${fieldInfo.description}</div></div>`;
    }
    if (fieldInfo.example) {
      fieldInfoText += `<div class="reviewer-item__row"><div class="reviewer-item__key">Example:</div><div class="reviewer-item__value">${fieldInfo.example}</div></div>`;
    }
    if (fieldInfo.badge) {
      fieldInfoText += `<div class="reviewer-item__row"><div class="reviewer-item__key">Badge:</div><div class="reviewer-item__value">${fieldInfo.badge}</div></div>`;
    }

    fieldInfoText += `<div class="reviewer-item__row">Does it comply with the required ${fieldInfo.title} description convention?</div></div>`;
    fieldDescriptionsElement.innerHTML = fieldInfoText;
  } else {
    fieldDescriptionsElement.textContent = "No description found";
  }
}

export function highlightSelectedField(fieldKey, highlightColor = '#F6F9FB') {
  const reviewItem = document.querySelectorAll('.review__item');
  const selectedDivId = 'field_' + fieldKey;
  const selectedDiv = document.getElementById(selectedDivId);

  reviewItem.forEach(div => {
    div.style.backgroundColor = '';
  });

  if (selectedDiv && !selectedDiv.classList.contains('field-ok')) {
    selectedDiv.style.backgroundColor = highlightColor;
  }
}

export function clearInputFields() {
  document.getElementById("valuearea").value = "";
  document.getElementById("commentarea").value = "";
}

/**
 * Switch to the category tab if needed
 */

/**
 * Function to provide the mapping of category to the correct tab ID
 */
export function getCategoryToTabIdMapping() {
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

/**
 * Creates List of all fields from html elements
 */
export function makeFieldList() {
  var fieldElements = [];
  $(".field").each(function() {
    fieldElements.push(this.id);
  });
  // alert(fieldElements[14]);
  return fieldElements;
}

/**
 * Selects the HTML field element after the current one and clicks it
 */

/**
 * Clicks a Field after checking it exists
 */
export function selectField(fieldList, field) {
  if (field >= 0 && field < fieldList.length) {
    var element = fieldList[field];
    document.getElementById(element).click();
  }
}

export function selectState(state, shouldUpdateClient = false) {
  selectedState = state;
  updateClientStateDict(selectedField, state);

  if (shouldUpdateClient) {
    check_if_review_finished();
  }
}


/**
 * Creates an HTML list of fields with their categories
 * @param {Array} fields Array of field objects
 * @returns {string} HTML list of fields
 */
export function createFieldList(fields) {
  return `
    <ul>
      ${fields.map((field) => `<li>${field.fieldCategory}: ${field.fieldValue}</li>`).join('')}
    </ul>
  `;
}
export function showToast(title, message, type) {
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
/**
 * Checks if all fields are reviewed and activates submit button if ready
 */
export function checkReviewComplete() {
  const fields = getAllFieldsAndValues();

  for (let field of fields) {
    const fieldState = getFieldState(field.fieldName);

    const reviewed = current_review["reviews"].find((review) => review.key === field.fieldName);

    if (!reviewed && fieldState !== 'ok' && fieldState !== 'rejected' && !isEmptyValue(field.fieldValue)) {
      $('#submit_summary').addClass('disabled');
      return;
    }
  }
  $('#submit_summary').removeClass('disabled');
  if (!clientSideReviewFinished) {
    showToast("Success", "You have reviewed all fields and can submit the review to get feedback!", 'success');
  }
}

/**
 * Shows reviewer Comment and Suggestion Input options
 */
export function showReviewerOptions() {
  $("#reviewer_remarks").removeClass('d-none');
}
/**
 * Hides reviewer Comment and Suggestion Input options
 */
export function hideReviewerOptions() {
  $("#reviewer_remarks").addClass('d-none');
}

export function showReviewerCommentsOptions() {
  $("#reviewer_comments").removeClass('d-none');
}
