// SPDX-FileCopyrightText: 2025 Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

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
  const cleanedFieldKey = fieldKey.replace(/\.\d+/g, '');

  switchCategoryTab(category);
  setSelectedField(fieldKey);
  setselectedFieldValue(fieldValue);
  setSelectedCategory(category);

  updateFieldDescription(cleanedFieldKey, fieldValue);
  highlightSelectedField(fieldKey);

  const fieldState = getFieldState(fieldKey);
  
  // Enable/Disable buttons based on state
    // 2. Logic to Enable/Disable buttons
  // If it's empty, buttons MUST be disabled, regardless of previous state (unless you want to allow un-reviewing, but generally empty = no action)
  const buttons = ["ok-button", "rejected-button", "suggestion-button"];
  
  buttons.forEach(btn => {
      const el = document.getElementById(btn);
      if (isEmpty) {
          el.disabled = true; // Force disable if empty
      } else {
          // If not empty, disable if no state is selected yet? 
          // Actually, in the original code, buttons were enabled if a state existed. 
          // But usually, you want buttons enabled so you CAN select a state.
          // Let's assume buttons should be enabled if the field has content.
          el.disabled = false;
      }
  });

  // 3. Handle empty field messages
  // We need to escape the selector for jQuery/querySelector because keys can have dots
  const safeFieldKey = CSS.escape(fieldKey); // Native JS escape
  // Or manually if you prefer: fieldKey.replace(/(:|\.|\[|\]|,|=|@)/g, "\\$1");
  

  // Handle empty field messages
  const fieldElementForMsg = document.querySelector(`.field[data-fieldkey="${fieldKey}"]`);
  if (fieldElementForMsg) {
    const safeKey = fieldKey.replace(/[^a-zA-Z0-9_-]/g, '_');
    let explanationElement = document.getElementById(`explanation_${safeKey}`);
    const labelEl = fieldElementForMsg.querySelector('.key');
    const valueEl = fieldElementForMsg.querySelector('.value');

    if (isEmpty) {
      if (!explanationElement) {
        explanationElement = document.createElement('p');
        explanationElement.id = `explanation_${safeKey}`;
        explanationElement.classList.add('explanation', 'text-muted', 'mt-1');
        explanationElement.innerText = 'Field is empty. Reviewing is not possible.';
        fieldElementForMsg.appendChild(explanationElement);
      }
      if(labelEl) labelEl.style.color = '#6c757d';
      if(valueEl) valueEl.style.color = '#6c757d';
    } else {
      if (explanationElement) explanationElement.remove();
      if(labelEl) labelEl.style.color = '';
      if(valueEl) valueEl.style.color = '';
    }
  }

  // Reset UI state for new selection
  clearInputFields();
  hideReviewerOptions();
  hideReviewerCommentsOptions();
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