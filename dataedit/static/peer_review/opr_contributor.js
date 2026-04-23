// SPDX-FileCopyrightText: 2023 Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2023 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2023 Bryan Lancien <https://github.com/bmlancien> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Daryna Barabanova <https://github.com/Darynarli> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2026 Vismaya Jochem <https://github.com/vismayajochem> © Reiner Lemoine Institut
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
  savePeerReview
} from './peer_review.js';

import {
  selectNextField,
  switchCategoryTab,
  updatePercentageDisplay
} from "./navigation.js";

import {
  renderSummaryPageFields,
  updateTabProgressIndicatorClasses
} from "./summary.js";

import {
  isEmptyValue
} from "./utilities.js";

// --- Local Helpers ---

function updateFieldColor(fieldKey, state) {
  // Escaping dots for jQuery selector if needed
  const safeId = '#field_' + fieldKey.replace(/\./g, "\\.");
  $(safeId).removeClass('field-ok field-suggestion field-rejected');
  $(safeId).addClass(`field-${state}`);
}

// --- Main Initialization ---

export function initContributor() {
  // Contributors typically use the same save mechanism for now
  initializeEventBindings(saveEntrancesForContributor);
  
  // Delegated event listener for field clicks
  document.addEventListener('click', function(event) {
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
  const cleanedFieldKey = fieldKey.replace(/\.\d+/g, '');
  
  switchCategoryTab(category);
  setSelectedField(fieldKey);
  setselectedFieldValue(fieldValue);
  setSelectedCategory(category);
  
  updateFieldDescription(cleanedFieldKey, fieldValue);
  highlightSelectedField(fieldKey);
  
  clearInputFields();
  hideReviewerOptions();
}

function saveEntrancesForContributor() {
    // Basic logic for contributor saving actions
    checkReviewComplete();
    selectNextField();
}