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
export function getCookie(name) {
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
export function sendJson(method, url, data, success, error) {
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

  // (function init() {
  //   $('#peer_review-loading').removeClass('d-none');
  //   config.form = $('#peer_review-form');
  // })();

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

export function isEmptyValue(value) {
    return value === "" || value === "None" || value === "[]";
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
export function switchCategoryTab(category) {
  const currentTab = document.querySelector('.tab-pane.active'); // Get the currently active tab
  const tabIdForCategory = getCategoryToTabIdMapping()[category];
  console.log("tabID", tabIdForCategory);
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
export function selectNextField() {
  var fieldList = makeFieldList();
  var next = fieldList.indexOf('field_' + window.selectedField) + 1;
  selectField(fieldList, next);
}

/**
 * Selects the HTML field element previous to the current one and clicks it
 */
export function selectPreviousField() {
  var fieldList = makeFieldList();
  var prev = fieldList.indexOf('field_' + window.selectedField) - 1;
  selectField(fieldList, prev);
}

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

  if (shouldUpdateClient) {
    updateClientStateDict(selectedField, state);
    check_if_review_finished();
  }
}

export function updateClientStateDict(fieldKey, state) {
  window.state_dict = window.state_dict ?? {};
  window.state_dict[fieldKey] = state;
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

export function renderSummaryPageFields() {
  const acceptedFields = [];
  const suggestingFields = [];
  const rejectedFields = [];
  const missingFields = [];
  const emptyFields = [];

  const processedFields = new Set();
  if (window.state_dict && Object.keys(window.state_dict).length > 0) {
    const fields = document.querySelectorAll('.field');
    for (let field of fields) {
      let field_id = field.id.slice(6);
      const fieldValue = $(field).find('.value').text().replace(/\s+/g, ' ').trim();
      const fieldState = getFieldState(field_id);
      const fieldCategory = field.getAttribute('data-category');
        const fieldSuggestion = field.querySelector('.suggestion.suggestion--highlight')?.textContent.trim() || "";


      // remove the numbers and replace the dots with spaces
      let fieldName = field_id.replace(/\./g, ' ');

      if (fieldCategory !== "general") {
        fieldName = fieldName.split(' ').slice(1).join(' '); // remove first word
      }

      const uniqueFieldIdentifier = `${fieldName}-${fieldCategory}`;

      if (isEmptyValue(fieldValue)) {
        emptyFields.push({ fieldName, fieldValue, fieldCategory: "emptyFields", fieldSuggestion });
      } else if (fieldState === 'ok') {
        acceptedFields.push({ fieldName, fieldValue, fieldCategory });
        processedFields.add(uniqueFieldIdentifier);
      }
    }
  }

  for (const review of current_review.reviews) {
    const field_id = `#field_${review.key}`.replaceAll(".", "\\.");
    const fieldValue = $(field_id).find('.value').text().replace(/\s+/g, ' ').trim();
    const fieldState = review.fieldReview.state;
    const fieldCategory = review.category;
    const fieldSuggestion = review.fieldReview.reviewerSuggestion
    let fieldName = review.key.replace(/\./g, ' ');

    if (fieldCategory !== "general") {
      fieldName = fieldName.split(' ').slice(1).join(' ');
    }

    const uniqueFieldIdentifier = `${fieldName}-${fieldCategory}`;

    if (processedFields.has(uniqueFieldIdentifier)) {
      continue;
    }

    if (isEmptyValue(fieldValue)) {
      emptyFields.push({ fieldName, fieldValue, fieldCategory: "emptyFields" });
    } else if (fieldState === 'ok') {
      acceptedFields.push({ fieldName, fieldValue, fieldCategory });
    } else if (fieldState === 'suggestion') {
      suggestingFields.push({ fieldName, fieldValue, fieldCategory, fieldSuggestion });
    } else if (fieldState === 'rejected') {
      rejectedFields.push({ fieldName, fieldValue, fieldCategory });
    }

    processedFields.add(uniqueFieldIdentifier);
  }

  const categories = document.querySelectorAll(".tab-pane");

  for (const category of categories) {
    const category_name = category.id;

    if (category_name === "summary") {
      continue;
    }
    const category_fields = category.querySelectorAll(".field");
    for (let field of category_fields) {
      const field_id = field.id.slice(6);
      const fieldValue = $(field).find('.value').text().replace(/\s+/g, ' ').trim();
      const found = current_review.reviews.some((review) => review.key === field_id);
      const fieldState = getFieldState(field_id);
      const fieldCategory = field.getAttribute('data-category');
      const fieldSuggestion = field.querySelector('.suggestion.suggestion--highlight')?.textContent.trim() || "";


      let fieldName = field_id.replace(/\./g, ' ');

      if (fieldCategory !== "general") {
        fieldName = fieldName.split(' ').slice(1).join(' ');
      }

      const uniqueFieldIdentifier = `${fieldName}-${fieldCategory}`;

      if (!found && fieldState !== 'ok' && !isEmptyValue(fieldValue) && !processedFields.has(uniqueFieldIdentifier)) {
        missingFields.push({ fieldName, fieldValue, fieldCategory, fieldSuggestion });
        processedFields.add(uniqueFieldIdentifier);
      }
    }
  }



  // Functions for displaying a table with results on a page
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
    header.innerHTML = '<th scope="col">Status</th><th scope="col">Field Category</th><th scope="col">Field Name</th><th scope="col">Field Value</th><th scope="col">Field Suggestion</th>';
    thead.appendChild(header);
    table.appendChild(thead);

    let tbody = document.createElement('tbody');

    data.forEach((item) => {
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
      tdFieldId.textContent = item.fieldName;
      row.appendChild(tdFieldId);

      let tdFieldValue = document.createElement('td');
      tdFieldValue.textContent = item.fieldValue;
      row.appendChild(tdFieldValue);

      let tdFieldSuggestion = document.createElement('td');
        tdFieldSuggestion.textContent = item.fieldSuggestion;
        row.appendChild(tdFieldSuggestion);

      tbody.appendChild(row);
    });

    table.appendChild(tbody);

    return table;
  }

  function updateSummaryTable() {
    clearSummaryTable();
    let allData = [];
    allData.push(...missingFields.map((item) => ({ ...item, fieldStatus: 'Missing' })));
    allData.push(...acceptedFields.map((item) => ({ ...item, fieldStatus: 'Accepted' })));
    allData.push(...suggestingFields.map((item) => ({ ...item, fieldStatus: 'Suggested' })));
    allData.push(...rejectedFields.map((item) => ({ ...item, fieldStatus: 'Rejected' })));
    allData.push(...emptyFields.map((item) => ({ ...item, fieldStatus: 'Empty' })));

    let table = generateTable(allData);
    summaryContainer.appendChild(table);
  }

  updateSummaryTable();
  updateTabProgressIndicatorClasses();
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

/**
 * Colors Field based on Reviewer input
 */
export function updateFieldColor() {
  // Color ok/suggestion/rejected
  let field_id = `#field_${selectedField}`.replaceAll(".", "\\.");
  $(field_id).removeClass('field-ok');
  $(field_id).removeClass('field-suggestion');
  $(field_id).removeClass('field-rejected');
  $(field_id).addClass(`field-${selectedState}`);
}

/**
 * Colors Field based on Reviewer input
 */
export function updateSubmitButtonColor() {
  // Color Save comment / new value
  $(submitButton).removeClass('btn-warning');
  $(submitCommentButton).removeClass('btn-warning');
  $(submitButton).removeClass('btn-danger');
  $(submitCommentButton).removeClass('btn-danger');
  if (selectedState === "suggestion") {
    $(submitButton).addClass('btn-warning');
  } else {
    $(submitCommentButton).addClass('btn-danger');
  }
}

export function updateTabClasses() {
  const tabNames = ['general', 'spatiotemporal', 'source', 'license'];
  for (let i = 0; i < tabNames.length; i++) {
    let tabName = tabNames[i];
    let tab = document.getElementById(tabName + '-tab');
    if (!tab) continue;

    let fields = Array.from(document.querySelectorAll('#' + tabName + ' .field'));

   let allReviewed = fields.every(field => {
      let fieldValue = $(field).find('.value').text().replace(/\s+/g, ' ').trim();
      let fieldState = getFieldState(field.id.replace('field_', ''));
      return isEmptyValue(fieldValue) || ['ok', 'suggest', 'rejected'].includes(fieldState);
    });

    if (allReviewed) {
      tab.classList.add('status');
      tab.classList.add('status--done');
    } else {
      tab.classList.add('status');
      tab.classList.remove('status--done');
    }
  }
}
 window.addEventListener('DOMContentLoaded', updateTabClasses);

/**
 * Hide and show revier controles once the user clicks the summary tab
 */
export const summaryTab = document.getElementById('summary-tab');
export const otherTabs = [
  document.getElementById('general-tab'),
  document.getElementById('spatiotemporal-tab'),
  document.getElementById('source-tab'),
  document.getElementById('license-tab'),
];
export const reviewContent = document.querySelector(".review__content");

export function updateTabProgressIndicatorClasses() {
  const tabNames = ['general', 'spatiotemporal', 'source', 'license'];

  tabNames.forEach(tabName => {
    const tab = document.getElementById(`${tabName}-tab`);
    if (!tab) return;

    const fieldsInTab = Array.from(document.querySelectorAll(`#${tabName} .field`));

    const allReviewed = fieldsInTab.every(field => {
      const fieldValue = $(field).find('.value').text().replace(/\s+/g, ' ').trim();
      const fieldState = getFieldState(field.id.replace('field_', ''));
      return isEmptyValue(fieldValue) || ['ok', 'suggestion', 'rejected'].includes(fieldState);
    });

    tab.classList.toggle('status--done', allReviewed);
  });
}

document.addEventListener('DOMContentLoaded', function() {
  if (summaryTab && reviewContent) {
    summaryTab.addEventListener('click', () => {
      toggleReviewControls(false);
      reviewContent.classList.toggle("tab-pane--100");
    });
  } else {
    console.error('Summary tab or review content not found');
  }

  otherTabs.forEach((tab, index) => {
    if (tab) {
      tab.addEventListener('click', () => {
        toggleReviewControls(true);
        reviewContent.classList.remove("tab-pane--100");
      });
    } else {
      console.error(`Tab at index ${index} not found`);
    }
  });

  function toggleReviewControls(show) {
    const reviewControls = document.querySelector('.review__controls');
    if (reviewControls) {
      reviewControls.style.display = show ? '' : 'none';
    }
  }
});

let getFieldStateImpl = (fieldKey) => {
  console.warn(`getFieldState is not defined yet. Can't get state for fieldKey: ${fieldKey}`);
  return null;
};

export function setGetFieldState(fn) {
  getFieldStateImpl = fn;
}

export function getFieldState(fieldKey) {
  return getFieldStateImpl(fieldKey);
}

