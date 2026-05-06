// SPDX-FileCopyrightText: 2025 Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2026 Vismaya Jochem <https://github.com/vismayajochem> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

import { getCategoryToTabIdMapping, makeFieldList, selectField } from "./peer_review.js";
import { isEmptyValue, isEffectivelyEmpty, sendJson } from "./utilities.js";

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
  const fieldList = makeFieldList();
  const currentIndex = fieldList.indexOf('field_' + window.selectedField);

  for (let i = currentIndex + 1; i < fieldList.length; i++) {
    const fieldElement = document.getElementById(fieldList[i]);
    if (!fieldElement) continue;

    const fieldKey = fieldElement.dataset.fieldkey;
    const fieldValue = fieldElement.dataset.fieldvalue;

    if (!isEffectivelyEmpty(fieldKey, fieldValue)) {
      selectField(fieldList, i);
      return;
    }
  }
}

export function selectPreviousField() {
  const fieldList = makeFieldList();
  const currentIndex = fieldList.indexOf('field_' + window.selectedField);

  for (let i = currentIndex - 1; i >= 0; i--) {
    const fieldElement = document.getElementById(fieldList[i]);
    if (!fieldElement) continue;

    const fieldKey = fieldElement.dataset.fieldkey;
    const fieldValue = fieldElement.dataset.fieldvalue;

    if (!isEffectivelyEmpty(fieldKey, fieldValue)) {
      selectField(fieldList, i);
      return;
    }
  }
}
/**
 * Selects the first field that needs review (not empty and not yet reviewed)
 */
export function selectFirstReviewableField() {
  const allFields = document.querySelectorAll('.review__item.field');
  
  for (let field of allFields) {
    const fieldKey = field.getAttribute('data-fieldkey');
    const fieldValue = field.getAttribute('data-fieldvalue');
    
    // Skip if no fieldKey
    if (!fieldKey || fieldKey === '') continue;
    
    // Check if field is effectively empty
    if (isEffectivelyEmpty(fieldKey, fieldValue)) continue;
    
    // Check if field is already reviewed
    const currentState = window.state_dict?.[fieldKey];
    const isReviewed = currentState && ['ok', 'suggestion', 'rejected'].includes(currentState);
    
    // Select if NOT empty AND NOT reviewed
    if (!isReviewed) {
      // Get the category from the field
      const category = field.getAttribute('data-category');
      
      // Check if field is in a collapsed accordion
      const accordionCollapse = field.closest('.accordion-collapse');
      
      if (accordionCollapse && !accordionCollapse.classList.contains('show')) {
        // Find and click the accordion button to expand it
        const accordionButton = document.querySelector(
          `[data-bs-target="#${accordionCollapse.id}"]`
        );
        
        if (accordionButton) {
          // Wait for accordion to expand, then select field
          accordionCollapse.addEventListener('shown.bs.collapse', () => {
            selectFieldAfterTabSwitch(fieldKey, fieldValue, category);
          }, { once: true });
          
          accordionButton.click();
          return; // Exit early, will be called after accordion opens
        }
      }
      
      // Check if we need to switch tabs
      const tabPane = field.closest('.tab-pane');
      if (tabPane && !tabPane.classList.contains('active')) {
        const tabId = tabPane.id;
        const tabButton = document.querySelector(`[data-bs-target="#${tabId}"]`);
        
        if (tabButton) {
          // Wait for tab transition
          setTimeout(() => {
            selectFieldAfterTabSwitch(fieldKey, fieldValue, category);
          }, 300);
          
          tabButton.click();
          return;
        }
      }
      
      // Field is visible, select it directly
      selectFieldAfterTabSwitch(fieldKey, fieldValue, category);
      return; // Stop after selecting first field
    }
  }
  
  console.log('No reviewable fields found (all are either empty or already reviewed)');
}

/**
 * Helper function to select field after tab/accordion animation
 */
function selectFieldAfterTabSwitch(fieldKey, fieldValue, category) {
  // Trigger the field click programmatically
  const fieldElement = document.querySelector(`.field[data-fieldkey="${fieldKey}"]`);
  
  if (fieldElement) {
    // Scroll to field
    fieldElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
    
    // Trigger click event (this will call your click_field function)
    fieldElement.click();
  }
}