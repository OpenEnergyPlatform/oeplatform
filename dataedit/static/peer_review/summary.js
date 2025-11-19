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
      const field_id = field.id.slice(6);
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
        emptyFields.push({ fieldName, fieldValue, fieldCategory, fieldSuggestion });
      } else if (fieldState === 'ok') {
        acceptedFields.push({ fieldName, fieldValue, fieldCategory, fieldSuggestion });
        processedFields.add(uniqueFieldIdentifier);
      }
    }
  }

  for (const review of current_review.reviews) {
    const field_id = `#field_${review.key}`.replaceAll(".", "\\.");
    const fieldValue = $(field_id).find('.value').text().replace(/\s+/g, ' ').trim();
    const fieldState = review.fieldReview.state;
    const fieldCategory = review.category;
    const fieldSuggestion = review.fieldReview.reviewerSuggestion || "";

    let fieldName = review.key.replace(/\./g, ' ');

    if (fieldCategory !== "general") {
      fieldName = fieldName.split(' ').slice(1).join(' ');
    }

    const uniqueFieldIdentifier = `${fieldName}-${fieldCategory}`;

    if (processedFields.has(uniqueFieldIdentifier)) {
      continue;
    }

    if (isEmptyValue(fieldValue)) {
      emptyFields.push({ fieldName, fieldValue, fieldCategory, fieldSuggestion });
    } else if (fieldState === 'ok') {
      acceptedFields.push({ fieldName, fieldValue, fieldCategory, fieldSuggestion });
    } else if (fieldState === 'suggestion') {
      suggestingFields.push({ fieldName, fieldValue, fieldCategory, fieldSuggestion });
    } else if (fieldState === 'rejected') {
      rejectedFields.push({ fieldName, fieldValue, fieldCategory, fieldSuggestion });
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

      if (
        !found &&
        fieldState !== 'ok' &&
        !isEmptyValue(fieldValue) &&
        !processedFields.has(uniqueFieldIdentifier)
      ) {
        missingFields.push({ fieldName, fieldValue, fieldCategory, fieldSuggestion });
        processedFields.add(uniqueFieldIdentifier);
      }
    }
  }

  const allData = [];
  allData.push(...missingFields.map((item) => ({ ...item, fieldStatus: 'Missing' })));
  allData.push(...acceptedFields.map((item) => ({ ...item, fieldStatus: 'Accepted' })));
  allData.push(...suggestingFields.map((item) => ({ ...item, fieldStatus: 'Suggested' })));
  allData.push(...rejectedFields.map((item) => ({ ...item, fieldStatus: 'Rejected' })));
  allData.push(...emptyFields.map((item) => ({ ...item, fieldStatus: 'Empty' })));

  const categoriesMap = {};

  function addFieldToCategory(category, field) {
    if (!categoriesMap[category]) categoriesMap[category] = [];
    categoriesMap[category].push(field);
  }

  allData.forEach(item => {
    const category = item.fieldCategory || 'general';
    addFieldToCategory(category, item);
  });

  const summaryContainer = document.getElementById("summary");
  summaryContainer.innerHTML = '';

  const tabsNav = document.createElement('ul');
  tabsNav.className = 'nav nav-tabs';

  const tabsContent = document.createElement('div');
  tabsContent.className = 'tab-content';

  let firstTab = true;

  for (const category in categoriesMap) {
    const tabId = `tab-${category}`;

    const navItem = document.createElement('li');
    navItem.className = 'nav-item';
    navItem.innerHTML = `
      <button class="nav-link${firstTab ? ' active' : ''}" data-bs-toggle="tab" data-bs-target="#${tabId}">
        ${category}
      </button>
    `;
    tabsNav.appendChild(navItem);

    const tabPane = document.createElement('div');
    tabPane.className = `tab-pane fade${firstTab ? ' show active' : ''}`;
    tabPane.id = tabId;

    const fieldsForCategory = categoriesMap[category];
    const singleFields = [];
    const groupedFields = {};

    fieldsForCategory.forEach(field => {
      const words = field.fieldName.split(' ');
      if (words.length === 1) {
        singleFields.push(field);
      } else {
        const prefix = words[0];
        const rest = words.slice(1);
        const indices = rest.filter(word => !isNaN(word));
        const nameWithoutIndices = rest.filter(word => isNaN(word)).join(' ');

        if (!groupedFields[prefix]) groupedFields[prefix] = { indexed: {}, noIndex: [] };

        if (indices.length > 0) {
          const indexKey = indices.map(num => (parseInt(num, 10) + 1)).join('.');
          if (!groupedFields[prefix].indexed[indexKey]) groupedFields[prefix].indexed[indexKey] = [];
          groupedFields[prefix].indexed[indexKey].push({ ...field, fieldName: nameWithoutIndices });
        } else {
          groupedFields[prefix].noIndex.push({ ...field, fieldName: nameWithoutIndices });
        }
      }
    });

    if (singleFields.length > 0) {
      const table = document.createElement('table');
      table.className = 'table review-summary';
      table.innerHTML = `
        <thead>
          <tr>
            <th>Status</th>
            <th>Field Name</th>
            <th>Field Value</th>
            <th>Field Suggestion</th>
          </tr>
        </thead>
        <tbody>
          ${singleFields.map(f => `
            <tr>
              <td class="status ${f.fieldStatus.toLowerCase()}">${f.fieldStatus}</td>
              <td>${f.fieldName}</td>
              <td>${f.fieldValue}</td>
              <td>${f.fieldSuggestion || ''}</td>
            </tr>
          `).join('')}
        </tbody>
      `;
      tabPane.appendChild(table);
    }

    if (Object.keys(groupedFields).length > 0) {
      const accordionContainer = document.createElement('div');
      accordionContainer.className = 'accordion';
      accordionContainer.id = `accordion-${category}`;

      let accordionIndex = 0;
      for (const prefix in groupedFields) {
        const accordionItem = document.createElement('div');
        accordionItem.className = 'accordion-item';
        const headingId = `heading-${category}-${accordionIndex}`;
        const collapseId = `collapse-${category}-${accordionIndex}`;

        const { noIndex, indexed } = groupedFields[prefix];

        let innerHTML = '';

        if (noIndex.length > 0) {
          innerHTML += `
            <table class="table table-sm table-bordered">
              <thead>
                <tr>
                  <th>Status</th>
                  <th>Field Name</th>
                  <th>Field Value</th>
                  <th>Field Suggestion</th>
                </tr>
              </thead>
              <tbody>
                ${noIndex.map(f => `
                  <tr>
                    <td class="status ${f.fieldStatus.toLowerCase()}">${f.fieldStatus}</td>
                    <td>${f.fieldName}</td>
                    <td>${f.fieldValue}</td>
                    <td>${f.fieldSuggestion || ''}</td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          `;
        }

        if (Object.keys(indexed).length > 0) {
          const subAccordionId = `subAccordion-${category}-${accordionIndex}`;
          innerHTML += `<div class="accordion" id="${subAccordionId}">`;

          Object.entries(indexed).forEach(([idx, idxFields], idxAccordionIndex) => {
            const idxHeadingId = `idxHeading-${category}-${accordionIndex}-${idxAccordionIndex}`;
            const idxCollapseId = `idxCollapse-${category}-${accordionIndex}-${idxAccordionIndex}`;

            const tabLabel = ['source', 'license'].includes(category) ? 'fields' : `${prefix} ${idx}`;

            innerHTML += `
              <div class="accordion-item">
                <h2 class="accordion-header" id="${idxHeadingId}">
                  <button class="accordion-button collapsed" data-bs-toggle="collapse" data-bs-target="#${idxCollapseId}">
                    ${tabLabel}
                  </button>
                </h2>
                <div id="${idxCollapseId}" class="accordion-collapse collapse" data-bs-parent="#${subAccordionId}">
                  <div class="accordion-body">
                    <table class="table table-sm table-bordered">
                      <thead>
                        <tr>
                          <th>Status</th>
                          <th>Field Name</th>
                          <th>Field Value</th>
                          <th>Field Suggestion</th>
                        </tr>
                      </thead>
                      <tbody>
                        ${idxFields.map(f => `
                          <tr>
                            <td class="status ${f.fieldStatus.toLowerCase()}">${f.fieldStatus}</td>
                            <td>${f.fieldName}</td>
                            <td>${f.fieldValue}</td>
                            <td>${f.fieldSuggestion || ''}</td>
                          </tr>
                        `).join('')}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            `;
          });

          innerHTML += `</div>`;
        }

        accordionItem.innerHTML = `
          <h2 class="accordion-header" id="${headingId}">
            <button class="accordion-button collapsed" data-bs-toggle="collapse" data-bs-target="#${collapseId}">
              ${['source', 'license'].includes(category) ? 'fields name' : prefix}
            </button>
          </h2>
          <div id="${collapseId}" class="accordion-collapse collapse" data-bs-parent="#accordion-${category}">
            <div class="accordion-body">
              ${innerHTML}
            </div>
          </div>
        `;

        accordionContainer.appendChild(accordionItem);
        accordionIndex++;
      }

      tabPane.appendChild(accordionContainer);
    }

    tabsContent.appendChild(tabPane);
    firstTab = false;
  }

  const viewsNavItem = document.createElement('li');
  viewsNavItem.className = 'nav-item';
  viewsNavItem.innerHTML = `
    <button class="nav-link" data-bs-toggle="tab" data-bs-target="#tab-views">
      views
    </button>
  `;
  tabsNav.appendChild(viewsNavItem);

  const viewsPane = document.createElement('div');
  viewsPane.className = 'tab-pane fade';
  viewsPane.id = 'tab-views';

  viewsPane.innerHTML = `
    <table class="table review-summary">
      <thead>
        <tr>
          <th>Status</th>
          <th>Category</th>
          <th>Field Name</th>
          <th>Field Value</th>
          <th>Field Suggestion</th>
        </tr>
      </thead>
      <tbody>
        ${allData.map(f => `
          <tr>
            <td class="status ${f.fieldStatus.toLowerCase()}">${f.fieldStatus}</td>
            <td>${f.fieldCategory}</td>
            <td>${f.fieldName}</td>
            <td>${f.fieldValue}</td>
            <td>${f.fieldSuggestion || ''}</td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;

  tabsContent.appendChild(viewsPane);
  summaryContainer.appendChild(tabsNav);
  summaryContainer.appendChild(tabsContent);

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