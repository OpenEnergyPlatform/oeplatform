// SPDX-FileCopyrightText: 2023 Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2023 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2023 Bryan Lancien <https://github.com/bmlancien> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2024 Daryna Barabanova <https://github.com/Darynarli> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2026 Vismaya Jochem <https://github.com/vismayajochem> © Reiner Lemoine Institut
// // SPDX-License-Identifier: AGPL-3.0-or-later

import {
  hideReviewerOptions,
  showReviewerOptions,
  showReviewerCommentsOptions,
  hideReviewerCommentsOptions, // Now available
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
  getErrorMsg,
  sendJson
} from './peer_review.js';

import { check_if_review_finished } from './opr_reviewer_logic.js';
import { getFieldState, setGetFieldState, updateClientStateDict } from "./state_current_review.js";
import { switchCategoryTab, selectNextField, updatePercentageDisplay } from "./navigation.js";
import { renderSummaryPageFields, updateTabProgressIndicatorClasses } from "./summary.js";
import {isEmptyValue, isEffectivelyEmpty} from "./utilities.js";window.clientSideReviewFinished = window.clientSideReviewFinished ?? false;
let initialReviewerSuggestions = {};
document.addEventListener('DOMContentLoaded', function() {
  initializeEmptyFields();
});
window.addEventListener('load', function() {
  initializeEmptyFields();
})
window.clientSideReviewFinished = window.clientSideReviewFinished ?? false;
export function initReviewer() {
  initializeEventBindings(saveEntrancesForReviewer);

  $('#peer_review-delete').off('click').on('click', deletePeerReview);
  
  // Toggle Logic for Reviewer Buttons
  $('#ok-button').on('click', () => {
      hideReviewerOptions();
      hideReviewerCommentsOptions();
  });
  $('#suggestion-button').on('click', () => {
      showReviewerOptions();
      hideReviewerCommentsOptions();
  });
  $('#rejected-button').on('click', () => {
      hideReviewerOptions();
      showReviewerCommentsOptions();
  });

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

  document.querySelectorAll(".suggestion--highlight").forEach(function (suggestion) {
      var field = suggestion.id.split("_")[1];
      if(field) initialReviewerSuggestions[field] = suggestion.innerText;
  });

  renderSummaryPageFields();
  updateTabProgressIndicatorClasses();
  updatePercentageDisplay();
  
  if (typeof window.state_dict !== 'undefined') {
    check_if_review_finished();
  }
}

function initializeEmptyFields() {
  const allFields = document.querySelectorAll(".field");

  allFields.forEach(fieldEl => {
    const fieldKey = fieldEl.dataset.fieldkey;
    const fieldValue = fieldEl.dataset.fieldvalue;

    const isEmpty = isEffectivelyEmpty(fieldKey, fieldValue);

    if (isEmpty) {
      // Grey out
      const labelEl = fieldEl.querySelector('.key');
      const valueEl = fieldEl.querySelector('.value');

      if (labelEl) labelEl.style.color = '#6c757d';
      if (valueEl) valueEl.style.color = '#6c757d';

      // Add explanation message
      const safeKey = fieldKey.replace(/[^a-zA-Z0-9_-]/g, '_');

      if (!document.getElementById(`explanation_${safeKey}`)) {
        const explanationElement = document.createElement('p');
        explanationElement.id = `explanation_${safeKey}`;
        explanationElement.classList.add('explanation', 'text-muted', 'mt-1');
        explanationElement.innerText = 'Field is empty. Reviewing is not possible.';
        fieldEl.appendChild(explanationElement);
      }

      // Disable clicking completely
      fieldEl.style.pointerEvents = "none";
      fieldEl.style.cursor = "not-allowed";
      fieldEl.style.opacity = "0.7";
    }
  });
}

function deletePeerReview() {
  if (!confirm("Are you sure?")) return;
  const json = JSON.stringify({ 
    reviewType: 'delete', 
    reviewData: current_review, 
    review_id: current_review.review_id || config.review_id
  });

  $('#peer_review-delete').addClass('d-none');
  sendJson("POST", config.url_peer_review, json)
    .then(() => window.location = config.url_table)
    .catch((err) => {
      $('#peer_review-delete').removeClass('d-none');
      alert(getErrorMsg(err));
    });
}

function click_field(fieldKey, fieldValue, category) {
  const isEmpty = isEffectivelyEmpty(fieldKey, fieldValue);

  if (isEmpty) {
    return;
  }
  
  switchCategoryTab(category);
  setSelectedField(fieldKey);
  setselectedFieldValue(fieldValue);
  setSelectedCategory(category);

  const cleanedFieldKey = fieldKey.replace(/\.\d+/g, '');
  
  const candidateKeys = [
    `resources.${category}.${fieldKey}`,
    `resources.${category}.${cleanedFieldKey}`,
    `resources.${fieldKey}`,
    `resources.${cleanedFieldKey}`,
    fieldKey,
    cleanedFieldKey,
  ];

  let resolvedKey = cleanedFieldKey;
  if (typeof fieldDescriptionsData !== 'undefined' && fieldDescriptionsData) {
    for (const candidate of candidateKeys) {
      if (fieldDescriptionsData[candidate]) {
        resolvedKey = candidate;
        break;
      }
    }
  }

  updateFieldDescription(resolvedKey, fieldValue);
  highlightSelectedField(fieldKey);

  const buttons = ["ok-button", "rejected-button", "suggestion-button"];
  buttons.forEach(btn => {
    const el = document.getElementById(btn);
    el.disabled = false;
  });

  const fieldElementForMsg = document.querySelector(`.field[data-fieldkey="${fieldKey}"]`);
  if (fieldElementForMsg) {
    const safeKey = fieldKey.replace(/[^a-zA-Z0-9_-]/g, '_');
    let explanationElement = document.getElementById(`explanation_${safeKey}`);
    const labelEl = fieldElementForMsg.querySelector('.key');
    const valueEl = fieldElementForMsg.querySelector('.value');

    if (explanationElement) explanationElement.remove();
    if (labelEl) labelEl.style.color = '';
    if (valueEl) valueEl.style.color = '';
  }

  // Always start fresh visually
  clearInputFields();
  hideReviewerOptions();
  hideReviewerCommentsOptions();

  // --- NEW: Restore previous review entry if it exists ---
  const existingReview = current_review.reviews.find(r => r.key === fieldKey);
  if (existingReview && existingReview.fieldReview) {
    const fr = existingReview.fieldReview;
    const previousState = fr.state;

    // Simulate clicking the correct state button to show the right UI
    if (previousState === 'suggestion') {
      showReviewerOptions();
      hideReviewerCommentsOptions();
      const valuearea = document.getElementById('valuearea');
      const commentarea = document.getElementById('commentarea');
      if (valuearea) valuearea.value = fr.newValue || '';
      if (commentarea) commentarea.value = fr.comment || '';
    } else if (previousState === 'rejected') {
      hideReviewerOptions();
      showReviewerCommentsOptions();
      const comments = document.getElementById('comments');
      if (comments) comments.value = fr.additionalComment || '';
    }
    // For 'ok', no extra UI needed, fields stay hidden
  }
}
function updateFieldColor(fieldKey, state) {
  const safeId = '#field_' + fieldKey.replace(/\./g, "\\.");
  $(safeId).removeClass('field-ok field-suggestion field-rejected');
  $(safeId).addClass(`field-${state}`);
}

function saveEntrancesForReviewer() {
    if (selectedState === "rejected") {
        const comments = document.getElementById('comments');
        if (comments.value.trim() === '') {
            showToast("Error", "Comment is required for rejection!", "error");
            return;
        }
    } else if (selectedState === "suggestion") {
        const valuearea = document.getElementById('valuearea');
        if (valuearea.value.trim() === '') {
            showToast("Error", "Value suggestion is required!", "error");
            return;
        }
    }

    if (selectedState === "ok") {
        clearInputFields();
    }

    if (window.selectedField) {
        const currentKey = window.selectedField;
        let fieldExists = false;
        
        const reviewObj = {
            "timestamp": Date.now(),
            "user": "oep_reviewer",
            "role": "reviewer",
            "contributorValue": selectedFieldValue,
            "newValue": (selectedState === "suggestion") ? document.getElementById("valuearea").value : "",
            "comment": document.getElementById("commentarea").value,
            "additionalComment": document.getElementById("comments").value,
            "reviewerSuggestion": (selectedState === "suggestion") ? document.getElementById("valuearea").value : "",
            "state": selectedState,
        };

        current_review.reviews.forEach(function(review, idx) {
            if (review["key"] === currentKey) {
                fieldExists = true;
                Object.assign(current_review["reviews"][idx], {
                    "category": selectedCategory,
                    "fieldReview": reviewObj
                });
            }
        });

        if (!fieldExists) {
            current_review.reviews.push({
                "category": selectedCategory,
                "key": currentKey,
                "fieldReview": reviewObj
            });
        }

        updateFieldColor(currentKey, selectedState);
        updateClientStateDict(currentKey, selectedState);
        
        // Update DOM suggestions immediately
        const fieldElement = document.getElementById("field_" + currentKey);
        if (fieldElement) {
            const suggEl = fieldElement.querySelector('.suggestion--highlight');
            if (suggEl) suggEl.innerText = reviewObj.reviewerSuggestion;
            
            const commEl = fieldElement.querySelector('.suggestion--additional-comment');
            if (commEl) commEl.innerText = reviewObj.additionalComment;
        }
    }

    document.getElementById("comments").value = "";
    checkReviewComplete();
    renderSummaryPageFields();
    updateTabProgressIndicatorClasses();
    updatePercentageDisplay();
    
    selectNextField();
    check_if_review_finished();
}
