// SPDX-FileCopyrightText: 2023 Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2023 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2023 Bryan Lancien <https://github.com/bmlancien> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Daryna Barabanova <https://github.com/Darynarli> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2026 Vismaya Jochem <https://github.com/vismayajochem> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

// NOTE: this mirrors much of opr_reviewer.js on purpose. The reviewer and
// contributor flows differ (the contributor only responds to fields the
// reviewer suggested/denied and never finishes/awards a badge), so they are kept
// as separate code paths for now. De-duplicating the shared parts (click_field,
// save, accordion scroll) is a task for the Phase 3 frontend refactor.

import {
  hideReviewerOptions,
  showReviewerOptions,
  showReviewerCommentsOptions,
  hideReviewerCommentsOptions,
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
  highlightSelectedField,
  initializeEventBindings,
} from './peer_review.js';

import { updateClientStateDict } from "./state_current_review.js";
import { switchCategoryTab, selectNextField, updatePercentageDisplay } from "./navigation.js";
import { renderSummaryPageFields, updateTabProgressIndicatorClasses } from "./summary.js";
import { isEffectivelyEmpty } from "./utilities.js";

// --- Local Helpers ---

function updateFieldColor(fieldKey, state) {
  const safeId = '#field_' + fieldKey.replace(/\./g, "\\.");
  $(safeId).removeClass('field-ok field-suggestion field-rejected');
  $(safeId).addClass(`field-${state}`);
}

/**
 * Expands all ancestor accordion panels containing the field, then scrolls it
 * into view once they are open. (Duplicated from opr_reviewer.js; Phase 3 dedup.)
 */
function expandAccordionsAndScrollToField(fieldKey) {
  const fieldElement = document.querySelector(`.field[data-fieldkey="${fieldKey}"]`);
  if (!fieldElement) return;

  const collapsedAncestors = [];
  let parent = fieldElement.parentElement;
  while (parent) {
    if (
      parent.classList.contains('accordion-collapse') &&
      !parent.classList.contains('show')
    ) {
      collapsedAncestors.push(parent);
    }
    parent = parent.parentElement;
  }

  if (collapsedAncestors.length === 0) {
    fieldElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
    return;
  }

  collapsedAncestors.reverse();

  function openNext(index) {
    if (index >= collapsedAncestors.length) {
      fieldElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
      return;
    }
    const collapseEl = collapsedAncestors[index];
    const toggleButton = document.querySelector(`[data-bs-target="#${collapseEl.id}"]`);
    if (!toggleButton) {
      openNext(index + 1);
      return;
    }
    collapseEl.addEventListener('shown.bs.collapse', function handler() {
      collapseEl.removeEventListener('shown.bs.collapse', handler);
      openNext(index + 1);
    });
    toggleButton.click();
  }

  openNext(0);
}

// --- Main Initialization ---

export function initContributor() {
  initializeEventBindings(saveEntrancesForContributor);

  // Reveal the right inputs for the chosen response (mirror of the reviewer).
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

  // Delegated event listener for field clicks
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

  // Initial renders
  renderSummaryPageFields();
  updateTabProgressIndicatorClasses();
  updatePercentageDisplay();
}

function click_field(fieldKey, fieldValue, category) {
  if (isEffectivelyEmpty(fieldKey, fieldValue)) {
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

  // Enable the response buttons for this field.
  ["ok-button", "rejected-button", "suggestion-button"].forEach(btn => {
    const el = document.getElementById(btn);
    if (el) el.disabled = false;
  });

  // Always start fresh visually.
  clearInputFields();
  hideReviewerOptions();
  hideReviewerCommentsOptions();

  // Restore a previous contributor response for this field, if one was made in
  // this session.
  const existingReview = current_review.reviews.find(r => r.key === fieldKey);
  if (existingReview && existingReview.fieldReview && !Array.isArray(existingReview.fieldReview)) {
    const fr = existingReview.fieldReview;
    if (fr.state === 'suggestion') {
      showReviewerOptions();
      hideReviewerCommentsOptions();
      const valuearea = document.getElementById('valuearea');
      const commentarea = document.getElementById('commentarea');
      if (valuearea) valuearea.value = fr.newValue || '';
      if (commentarea) commentarea.value = fr.comment || '';
    } else if (fr.state === 'rejected') {
      hideReviewerOptions();
      showReviewerCommentsOptions();
      const comments = document.getElementById('comments');
      if (comments) comments.value = fr.additionalComment || '';
    }
  }

  expandAccordionsAndScrollToField(fieldKey);
}

function saveEntrancesForContributor() {
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
      "user": "oep_contributor",
      "role": "contributor",
      "contributorValue": selectedFieldValue,
      "newValue": (selectedState === "suggestion") ? document.getElementById("valuearea").value : "",
      "comment": document.getElementById("commentarea").value,
      "additionalComment": document.getElementById("comments").value,
      "reviewerSuggestion": (selectedState === "suggestion") ? document.getElementById("valuearea").value : "",
      "state": selectedState,
    };

    current_review.reviews.forEach(function (review, idx) {
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

    // Reflect the contributor's response in the field row (the reviewer side
    // does the same). Uses the slots that exist in the markup.
    const fieldElement = document.getElementById("field_" + currentKey);
    if (fieldElement) {
      const suggEl = fieldElement.querySelector('.suggestion--highlight');
      if (suggEl) {
        suggEl.innerText =
          (selectedState === "suggestion") ? reviewObj.reviewerSuggestion : '';
      }
      const commentEl = fieldElement.querySelector('.comment');
      if (commentEl) {
        commentEl.innerText =
          (selectedState === "rejected")
            ? reviewObj.additionalComment
            : reviewObj.comment;
      }
    }
  }

  document.getElementById("comments").value = "";
  checkReviewComplete();
  renderSummaryPageFields();
  updateTabProgressIndicatorClasses();
  updatePercentageDisplay();

  selectNextField();
}