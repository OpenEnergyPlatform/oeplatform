// SPDX-FileCopyrightText: 2025 Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later
import {current_review, selectedState} from "./peer_review.js";
import {getFieldState} from "./state_current_review.js";
import {isEmptyValue} from "./utilities.js";

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

export const summaryTab = document.getElementById('summary-tab');
export const otherTabs = [
  document.getElementById('general-tab'),
  document.getElementById('spatiotemporal-tab'),
  document.getElementById('source-tab'),
  document.getElementById('license-tab'),
];
export const reviewContent = document.querySelector(".review__content");

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