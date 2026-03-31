// SPDX-FileCopyrightText: 2025 Bryan Lancien <https://github.com/bmlancien> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Daryna Barabanova <https://github.com/Darynarli> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Christian Hofmann <https://github.com/christian-rli> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Stephan Uller <https://github.com/steull> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 user <https://github.com/Darynarli> © Reiner Lemoine Institut
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import * as common from './peer_review.js';
import {
  hideReviewerOptions as hideReviewerOptionsImported,
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
  highlightSelectedField,
  updateFieldDescription,
  initializeEventBindings,
  makeFieldList
} from './peer_review.js';

window.selectState = common.selectState;

import { check_if_review_finished, checkFieldStates } from './opr_reviewer_logic.js';
import { getFieldState as getFieldStateImported, setGetFieldState } from "./state_current_review.js";
import { selectNextField, switchCategoryTab } from "./navigation.js";
import { renderSummaryPageFields, updateTabProgressIndicatorClasses } from "./summary.js";
import { isEmptyValue, updateFieldColor as updateFieldColorImported } from "./utilities.js";

window.clientSideReviewFinished = window.clientSideReviewFinished ?? false;
var fieldEvaluations = {}; // Object for tracking evaluated fields

// Initial jQuery Bindings
$('#peer_review-delete').bind('click', deletePeerReview);
$('#ok-button').bind('click', hideReviewerOptions);
$('#suggestion-button').bind('click', hideReviewerCommentOptions);
$('#rejected-button').bind('click', hideReviewerOptions);

/**
 * Configurates peer review
 * @param {json} config Configuration JSON from Django backend.
 */
function peerReview(config) {
  selectNextField();
  renderSummaryPageFields();
  updateTabProgressIndicatorClasses();
  updatePercentageDisplay();

  if (typeof state_dict !== 'undefined' && state_dict) {
    check_if_review_finished();
  }

  // Save config to window so global functions can access it
  window.current_config = config;
  updateSummaryTable();
}

/**
 * UTILITY FUNCTIONS
 */
function deletePeerReview() {
  if (!confirm("Are you sure?")) {
    return;
  }

  const config = window.current_config || {};
  const json = JSON.stringify({
    reviewType: 'delete',
    reviewData: current_review,
    review_id: current_review.review_id || config.review_id
  });

  $('#peer_review-delete').addClass('d-none');

  sendJson("POST", config.url_peer_review, json)
    .then(function () {
      window.location = config.url_table;
    })
    .catch(function (err) {
      $('#peer_review-delete').removeClass('d-none');
      alert(getErrorMsg(err));
    });
}

function click_field(fieldKey, fieldValue, category) {
  const isEmpty = isEmptyValue(fieldValue);
  const cleanedFieldKey = fieldKey.replace(/\.\d+/g, '');

  switchCategoryTab(category);
  setSelectedField(fieldKey);
  setselectedFieldValue(fieldValue);
  setSelectedCategory(category);
  updateFieldDescription(cleanedFieldKey, fieldValue);
  highlightSelectedField(fieldKey);

  const fieldState = getFieldState(fieldKey);
  const fieldWasEvaluated = fieldEvaluations[fieldKey];

  if (fieldState) {
    if (fieldState === 'ok' && !fieldWasEvaluated) {
      ["ok-button", "rejected-button", "suggestion-button"].forEach(btn => {
        const buttonEl = document.getElementById(btn);
        if (buttonEl) buttonEl.disabled = true;
      });
    } else if (['suggestion', 'rejected'].includes(fieldState) || fieldWasEvaluated) {
      ["ok-button", "rejected-button", "suggestion-button"].forEach(btn => {
        const buttonEl = document.getElementById(btn);
        if (buttonEl) buttonEl.disabled = false;
      });
    }
  } else {
    ["ok-button", "rejected-button", "suggestion-button"].forEach(btn => {
      const buttonEl = document.getElementById(btn);
      if (buttonEl) buttonEl.disabled = isEmpty;
    });

    const explanationContainer = document.getElementById("explanation-container");
    if (explanationContainer) {
      const existingExplanation = explanationContainer.querySelector('.explanation');
      if (isEmpty && !existingExplanation) {
        const explanationElement = document.createElement('p');
        explanationElement.textContent = 'Field is empty. Reviewing is not possible.';
        explanationElement.classList.add('explanation');
        explanationContainer.appendChild(explanationElement);
      } else if (!isEmpty && existingExplanation) {
        explanationContainer.removeChild(existingExplanation);
      }
    }

    document.getElementById("ok-button").addEventListener('click', () => { fieldEvaluations[fieldKey] = 'ok'; }, { once: true });
    document.getElementById("rejected-button").addEventListener('click', () => { fieldEvaluations[fieldKey] = 'rejected'; }, { once: true });
    document.getElementById("suggestion-button").addEventListener('click', () => { fieldEvaluations[fieldKey] = 'suggestion'; }, { once: true });

    clearInputFields();
    hideReviewerOptions();
    hideReviewerCommentOptions();
  }
}
window.click_field = click_field;

function generateTable(data) {
  let table = document.createElement('table');
  table.className = 'table review-summary';

  let thead = document.createElement('thead');
  let header = document.createElement('tr');
  header.innerHTML = '<th scope="col">Status</th><th scope="col">Field Category</th><th scope="col">Field Name</th><th scope="col">Field Value</th>';
  thead.appendChild(header);
  table.appendChild(thead);

  let tbody = document.createElement('tbody');

  data.forEach((item) => {
    let row = document.createElement('tr');

    let th = document.createElement('th');
    th.scope = "row";
    th.className = item.fieldStatus === "Missing" ? "status missing" : "status";
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
  if (typeof clearSummaryTable === "function") clearSummaryTable();
  if (typeof summaryContainer === "undefined" || !summaryContainer) return;

  let allData = [];
  if (typeof missingFields !== "undefined") allData.push(...missingFields.map((item) => ({ ...item, fieldStatus: 'Missing' })));
  if (typeof acceptedFields !== "undefined") allData.push(...acceptedFields.map((item) => ({ ...item, fieldStatus: 'Accepted' })));
  if (typeof suggestingFields !== "undefined") allData.push(...suggestingFields.map((item) => ({ ...item, fieldStatus: 'Suggested' })));
  if (typeof rejectedFields !== "undefined") allData.push(...rejectedFields.map((item) => ({ ...item, fieldStatus: 'Rejected' })));
  if (typeof emptyFields !== "undefined") allData.push(...emptyFields.map((item) => ({ ...item, fieldStatus: 'Empty' })));

  let table = generateTable(allData);
  summaryContainer.appendChild(table);
}

function saveEntrancesForReviewer() {
  if (selectedState === "rejected") {
    const comments = document.getElementById('comments');
    if (comments.value.trim() === '') {
      comments.setCustomValidity('Comment is required');
      showToast("Error", "The comment text field is required to save the field review!", "error");
      return;
    } else {
      comments.setCustomValidity('');
    }
    const valuearea = document.getElementById('valuearea');
    if (valuearea) valuearea.reportValidity();
  }

  if (selectedState !== "ok" && selectedState !== "rejected") {
    const valuearea = document.getElementById('valuearea');
    if (valuearea.value.trim() === '') {
      valuearea.setCustomValidity('Value suggestion is required');
      showToast("Error", "The value suggestion text field is required to save the field review!", "error");
      return;
    } else {
      valuearea.setCustomValidity('');
    }
    valuearea.reportValidity();
  } else if (selectedState === "ok") {
    var fieldElement = document.getElementById("field_" + selectedField);
    if (fieldElement) {
      var valueElement = fieldElement.querySelector('.value');
      if (valueElement) {
        if (typeof initialReviewerSuggestions !== 'undefined' && initialReviewerSuggestions[selectedField] && initialReviewerSuggestions[selectedField].trim() !== '') {
          valueElement.innerText = initialReviewerSuggestions[selectedField];
        } else {
          valueElement.innerText = selectedFieldValue;
        }
      }

      const valArea = document.getElementById('valuearea');
      const commArea = document.getElementById('commentarea');
      if (valArea) valArea.value = '';
      if (commArea) commArea.value = '';

      var suggestionElement = fieldElement.querySelector('.suggestion--highlight');
      if (suggestionElement) {
        suggestionElement.innerText = '';
      }

      if (typeof initialReviewerSuggestions !== 'undefined' && initialReviewerSuggestions[selectedField]) {
        initialReviewerSuggestions[selectedField] = '';
      }
    }
  }

  if (typeof selectedField !== 'undefined' && selectedField) {
    var fieldExists = false;

    current_review["reviews"].forEach(function (review, idx) {
      if (review["key"] === selectedField) {
        fieldExists = true;

        if (selectedState === "ok" || selectedState === "rejected") {
          Object.assign(current_review["reviews"][idx], {
            "category": selectedCategory,
            "key": selectedField,
            "fieldReview": {
              "timestamp": Date.now(),
              "user": "oep_reviewer",
              "role": "reviewer",
              "contributorValue": selectedFieldValue,
              "newValue": (typeof initialReviewerSuggestions !== 'undefined' && initialReviewerSuggestions[selectedField]) ? initialReviewerSuggestions[selectedField] : "",
              "comment": document.getElementById("commentarea") ? document.getElementById("commentarea").value : "",
              "additionalComment": document.getElementById("comments") ? document.getElementById("comments").value : "",
              "reviewerSuggestion": "",
              "state": selectedState,
            },
          });
        } else if (selectedState === "suggest") {
          Object.assign(current_review["reviews"][idx], {
            "category": selectedCategory,
            "key": selectedField,
            "fieldReview": {
              "timestamp": Date.now(),
              "user": "oep_reviewer",
              "role": "reviewer",
              "contributorValue": selectedFieldValue,
              "newValue": document.getElementById("valuearea") ? document.getElementById("valuearea").value : "",
              "comment": document.getElementById("commentarea") ? document.getElementById("commentarea").value : "",
              "additionalComment": document.getElementById("comments") ? document.getElementById("comments").value : "",
              "reviewerSuggestion": document.getElementById("valuearea") ? document.getElementById("valuearea").value : "",
              "state": selectedState,
            },
          });

          var fieldElement = document.getElementById("field_" + selectedField);
          if (fieldElement) {
            var suggestionElement = fieldElement.querySelector('.suggestion--highlight');
            var additionalCommentElement = fieldElement.querySelector('.suggestion--additional-comment');
            if (suggestionElement) {
              suggestionElement.innerText = document.getElementById("valuearea").value;
            } if (additionalCommentElement) {
              additionalCommentElement.innerText = document.getElementById("comments").value;
            }
          }
        }
      }
    });

    if (!fieldExists) {
      current_review["reviews"].push({
        "category": selectedCategory,
        "key": selectedField,
        "fieldReview": {
          "timestamp": Date.now(),
          "user": "oep_reviewer",
          "role": "reviewer",
          "contributorValue": selectedFieldValue,
          "newValue": selectedState === "ok" ? ((typeof initialReviewerSuggestions !== 'undefined' && initialReviewerSuggestions[selectedField]) || "") : (document.getElementById("valuearea") ? document.getElementById("valuearea").value : ""),
          "comment": document.getElementById("commentarea") ? document.getElementById("commentarea").value : "",
          "additionalComment": document.getElementById("comments") ? document.getElementById("comments").value : "",
          "reviewerSuggestion": selectedState === "ok" ? "" : (document.getElementById("valuearea") ? document.getElementById("valuearea").value : ""),
          "state": selectedState,
        },
      });

      var fieldElement = document.getElementById("field_" + selectedField);
      if (fieldElement) {
        var suggestionElement = fieldElement.querySelector('.suggestion--highlight');
        var additionalCommentElement = fieldElement.querySelector('.suggestion--additional-comment');
        if (suggestionElement) {
          suggestionElement.innerText = document.getElementById("valuearea").value;
        } if (additionalCommentElement) {
          additionalCommentElement.innerText = document.getElementById("comments").value;
        }
      }
    }
  }

  updateFieldColor();
  if (selectedState === "ok") {
    if (document.getElementById("valuearea")) document.getElementById("valuearea").value = "";
    if (document.getElementById("commentarea")) document.getElementById("commentarea").value = "";
  }
  if (document.getElementById("comments")) document.getElementById("comments").value = "";

  checkReviewComplete();
  selectNextField();
  renderSummaryPageFields();
  updateTabProgressIndicatorClasses();
  check_if_review_finished();
}

initializeEventBindings(saveEntrancesForReviewer);

function getFieldState(fieldKey) {
  if (typeof window.state_dict !== 'undefined' && window.state_dict[fieldKey] !== undefined) {
    return window.state_dict[fieldKey];
  } else if (typeof state_dict !== 'undefined' && state_dict[fieldKey] !== undefined) {
    return state_dict[fieldKey];
  } else {
    return null;
  }
}

export function getFieldStateForReviewer(fieldKey) {
  if (window.state_dict && window.state_dict[fieldKey] !== undefined) {
    return window.state_dict[fieldKey];
  } else {
    return null;
  }
}
setGetFieldState(getFieldStateForReviewer);

function hideReviewerCommentOptions() {
  $("#reviewer_comments").addClass('d-none');
}

function showReviewerOptions() {
  $("#reviewer_remarks").removeClass('d-none');
}

function hideReviewerOptions() {
  $("#reviewer_remarks").addClass('d-none');
}

function updateFieldColor() {
  if (typeof selectedField === 'undefined') return;
  let field_id = `#field_${selectedField}`.replaceAll(".", "\\.");
  $(field_id).removeClass('field-ok field-suggestion field-rejected');
  $(field_id).addClass(`field-${selectedState}`);
}

function updateSubmitButtonColor() {
  if (typeof submitButton === 'undefined') return;
  $(submitButton).removeClass('btn-warning btn-danger');
  if (selectedState === "suggestion") {
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

    let allOkOrEmpty = fields.every(field => {
      let fieldValue = $(field).find('.value').text().replace(/\s+/g, ' ').trim();
      let fieldState = getFieldState(field.id.replace('field_', ''));
      return isEmptyValue(fieldValue) || fieldState === 'ok';
    });

    tab.classList.remove('status--done');
    tab.classList.add('status');
    if (allOkOrEmpty && fields.length > 0) {
      tab.classList.add('status--done');
    }
  }
}

function getTotalFieldCount() {
  var allFields = makeFieldList();
  return allFields.length;
}

function calculateOkPercentage(stateDict) {
  if (!stateDict) return "0.00";
  let totalCount = 0;
  let okCount = 0;

  for (let key in stateDict) {
    let el = document.getElementById(`field_${key}`);
    if (!el) continue;

    let fieldValue = $(el).find('.value').text().replace(/\s+/g, ' ').trim();
    if (!isEmptyValue(fieldValue)) {
      totalCount++;
      if (stateDict[key] === "ok") {
        okCount++;
      }
    }
  }

  let percentage = totalCount === 0 ? 0 : (okCount / totalCount) * 100;
  return percentage.toFixed(2);
}

function updatePercentageDisplay() {
  const display = document.getElementById("percentageDisplay");
  if (display) {
    display.textContent = calculateOkPercentage(window.state_dict);
  }
}

// Global Event Listeners attached ONCE
document.addEventListener('DOMContentLoaded', function () {
  document.addEventListener('click', function (event) {
    const field = event.target.closest('.field');
    if (!field) return;

    const fieldKey = field.dataset.fieldkey;
    const fieldValue = field.dataset.fieldvalue;
    const category = field.dataset.category;

    if (fieldKey && category !== undefined) {
      click_field(fieldKey, fieldValue, category);
    }
  });

  updateTabClasses();
  updatePercentageDisplay();
});