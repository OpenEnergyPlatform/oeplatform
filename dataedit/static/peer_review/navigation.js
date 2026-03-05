// SPDX-FileCopyrightText: 2025 Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

import { getCategoryToTabIdMapping, makeFieldList, selectField } from "./peer_review.js";

export function updateTabProgress() {
  const allFields = document.querySelectorAll('.review__item');
  const total = allFields.length;
  let completed = 0;

  allFields.forEach(field => {
    // Check for any of the completed states (ok, rejected, suggestion)
    if (field.classList.contains('field-ok') || 
        field.classList.contains('field-rejected') || 
        field.classList.contains('field-suggestion')) {
      completed++;
    }
  });

  const percentage = total === 0 ? 0 : Math.round((completed / total) * 100);

  // Update the circular progress bar
  const circle = document.getElementById('okProgressCircle');
  const text = document.getElementById('okPercentageText');
  
  if (circle && text) {
    // 326.72 is 2*PI*r where r=52 (from your SVG)
    const circumference = 326.72; 
    const offset = circumference - (percentage / 100) * circumference;
    circle.style.strokeDashoffset = offset;
    text.textContent = `${percentage}%`;
  }
}

// Alias to fix the ReferenceError in summary.js
export const updatePercentageDisplay = updateTabProgress;

export function switchCategoryTab(category) {
  const currentTab = document.querySelector('.tab-pane.active');
  const tabIdForCategory = getCategoryToTabIdMapping()[category];
  
  if (currentTab && currentTab.getAttribute('id') !== tabIdForCategory) {
    const targetTab = document.getElementById(tabIdForCategory);
    if (targetTab) {
      targetTab.click();
    }
  }
}

export function selectNextField() {
  var fieldList = makeFieldList();
  var next = fieldList.indexOf('field_' + window.selectedField) + 1;
  selectField(fieldList, next);
}

export function selectPreviousField() {
  var fieldList = makeFieldList();
  var prev = fieldList.indexOf('field_' + window.selectedField) - 1;
  selectField(fieldList, prev);
}