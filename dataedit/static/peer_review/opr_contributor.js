// SPDX-FileCopyrightText: 2025 Bryan Lancien <https://github.com/bmlancien> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Daryna Barabanova <https://github.com/Darynarli> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Stephan Uller <https://github.com/steull> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 user <https://github.com/Darynarli> © Reiner Lemoine Institut
//
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
} from './peer_review.js';

// expose selectState for any legacy inline handlers
window.selectState = selectState;
import {selectNextField, switchCategoryTab} from "./navigation.js";
import {getFieldState, setGetFieldState} from "./state_current_review.js";
import {isEmptyValue, updateFieldColor} from "./utilities.js";
import {updateTabProgressIndicatorClasses} from "./summary.js";

let selectedField = null;
let actionsEnabled = false;

// Track whether the contributor has already interacted with a field (local UI state)
const fieldEvaluations = {};


// OK Field View Change
$('#button').bind('click', hideReviewerOptions);

// Resolve the reviewer decision for a field (independent from later contributor actions)
function getReviewerState(fieldKey) {
  // Prefer the backend-computed state dict (represents reviewer outcome)
  if (window.state_dict && Object.prototype.hasOwnProperty.call(window.state_dict, fieldKey)) {
    return window.state_dict[fieldKey];
  }

  // Fallback: derive from current_review by picking the latest entry with role === 'reviewer'
  try {
    const reviews = current_review?.reviews;
    if (!Array.isArray(reviews)) return undefined;

    const review = reviews.find((r) => r && r.key === fieldKey);
    if (!review || !review.fieldReview) return undefined;

    const frArr = Array.isArray(review.fieldReview) ? review.fieldReview : [review.fieldReview];
    const reviewerEntries = frArr.filter((x) => x && x.role === 'reviewer');
    const pickFrom = reviewerEntries.length ? reviewerEntries : frArr;

    const latest = pickFrom
      .slice()
      .sort((a, b) => (b?.timestamp ?? 0) - (a?.timestamp ?? 0))[0];

    return latest?.state;
  } catch (_e) {
    return undefined;
  }
}


function click_field(fieldKey, fieldValue, category) {
  // Keep the original value (may be null/undefined if the template does not provide it)
  const rawFieldValue = fieldValue;

  // Ensure we always work with a string value for the UI
  const fieldValueStr = (fieldValue ?? '').toString();

  // Reset UI first; some helpers may toggle/disable controls
  clearInputFields();
  hideReviewerOptions();

  const cleanedFieldKey = fieldKey.replace(/\.\d+/g, '');

  switchCategoryTab(category);

  setSelectedField(fieldKey);

  // Keep a local copy for this module (peer_review.js stores the canonical value on window.selectedField)
  selectedField = fieldKey;

  setselectedFieldValue(fieldValueStr);
  setSelectedCategory(category);

  updateFieldDescription(cleanedFieldKey, fieldValueStr);
  highlightSelectedField(fieldKey);

  const fieldState = getReviewerState(fieldKey);
  const fieldWasEvaluated = !!fieldEvaluations[fieldKey];

  // IMPORTANT: Do NOT disable buttons just because we couldn't read the value from the DOM.
  // Some fields don't have `.value` / `data-fieldvalue` in the list, but are still reviewable.
  const isEmpty = (rawFieldValue !== null && rawFieldValue !== undefined)
    ? isEmptyValue(fieldValueStr)
    : false;

  const okBtn = document.getElementById('ok-button');
  const suggestionBtn = document.getElementById('suggestion-button');
  const rejectedBtn = document.getElementById('rejected-button');

  let enableActions = false;

  if (fieldState) {
    // Contributor rule: buttons active ONLY for reviewer suggestion fields.
    if (fieldState === 'suggestion' || fieldState === 'suggest') {
      enableActions = !isEmpty;
    } else if (fieldState === 'ok' && !fieldWasEvaluated) {
      enableActions = false;
    } else {
      enableActions = false;
    }
  } else {
    // If there is no reviewer state, keep buttons disabled.
    enableActions = false;
  }

  actionsEnabled = enableActions;

  [okBtn, suggestionBtn, rejectedBtn].forEach((btn) => {
    const buttonEl = btn;
    if (buttonEl) {
      buttonEl.disabled = !enableActions;
    }
  });
}

document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.field').forEach((field) => {
    const fieldKey = field.getAttribute('data-fieldkey');
    const reviewerState = getReviewerState(fieldKey);

    // Optional visual hint (still clickable)
    if (reviewerState !== 'suggestion') {
      field.classList.add('field-locked');
      field.setAttribute('aria-disabled', 'true');
      // DO NOT disable pointer events; contributors should be able to open/view all fields.
    }

    field.addEventListener('click', () => {
      // Some templates do not provide data-fieldvalue; fall back to rendered DOM text
      const fieldValueAttr = field.getAttribute('data-fieldvalue');
      const fieldValueDom =
        field.querySelector('.value, .field-value, .field__value, .field__content, .field-content')?.textContent;

      // Allow null if we can't reliably extract a value from the field list DOM
      const fieldValue = fieldValueAttr ?? (fieldValueDom != null ? fieldValueDom.trim() : null);

      // category is usually present; fall back to the parent tab pane id
      const categoryAttr = field.getAttribute('data-category');
      const categoryDom = field.closest('.tab-pane')?.id;
      const category = (categoryAttr ?? categoryDom ?? 'general').toString();

      click_field(fieldKey, fieldValue, category);
    });
  });

  // Bind action buttons once. They are enabled/disabled per-field via `actionsEnabled`.
  const okBtn = document.getElementById('ok-button');
  const suggestionBtn = document.getElementById('suggestion-button');
  const rejectedBtn = document.getElementById('rejected-button');

  const bindAction = (btn, state) => {
    if (!btn) return;
    btn.addEventListener(
      'click',
      (e) => {
        if (!actionsEnabled) {
          // Keep UI inert for non-suggestion fields
          e.preventDefault();
          e.stopPropagation();
          return;
        }

        const selectedKey = window.selectedField || selectedField;
        if (selectedKey) {
          fieldEvaluations[selectedKey] = state;
        }

        if (typeof selectState === 'function') {
          selectState(state);
        } else if (typeof window.selectState === 'function') {
          window.selectState(state);
        }
      },
      true
    );
  };

  bindAction(okBtn, 'ok');
  bindAction(rejectedBtn, 'rejected');
  bindAction(suggestionBtn, 'suggestion');
});
/**
 * Saves selected state
 * @param fieldKey
 */

export function getFieldStateForContributor(fieldKey) {
  // 1) Preferred: server-provided state_dict (if attached to window)
  if (window.state_dict && Object.prototype.hasOwnProperty.call(window.state_dict, fieldKey)) {
    return window.state_dict[fieldKey];
  }

  // 2) Fallback: derive from current_review (works even if state_dict is not on window)
  try {
    const reviews = current_review?.reviews;
    if (!Array.isArray(reviews)) return undefined;

    const review = reviews.find((r) => r && r.key === fieldKey);
    if (!review || !review.fieldReview) return undefined;

    // fieldReview can be an object or a list of objects
    const fr = review.fieldReview;
    const latest = Array.isArray(fr)
      ? fr
          .slice()
          .sort((a, b) => (b?.timestamp ?? 0) - (a?.timestamp ?? 0))[0]
      : fr;

    return latest?.state;
  } catch (_e) {
    return undefined;
  }
}


/**
 * Renders fields on the Summary page, sorted by review state
 */
/**
 * Displays fields based on selected category
 */
function renderSummaryPageFields() {
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
    const fieldDomId = `field_${review.key}`;
    const fieldEl = document.getElementById(fieldDomId);
    const fieldValue = fieldEl
      ? $(fieldEl).find('.value').text().replace(/\s+/g, ' ').trim()
      : '';
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
/**
 * Creates an HTML list of fields with their categories
 * @param {Array} fields Array of field objects
 * @returns {string} HTML list of fields
 */
function createFieldList(fields) {
  return `
    <ul>
      ${fields.map((field) => `<li>${field.fieldCategory}: ${field.fieldValue}</li>`).join('')}
    </ul>
  `;
}

// // Function to show the error toast
// function showErrorToast(liveToast) {
//   liveToast.show();
// }

function showToast(title, message, type) {
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

setGetFieldState(getFieldStateForContributor);

function saveEntrancesForContributor() {
  const selectedKey = window.selectedField || selectedField;

  if (selectedState !== "ok" && selectedState !== "rejected") {
    // Get the valuearea element
    const valuearea = document.getElementById('valuearea');

    // Validate the valuearea before proceeding
    if (valuearea.value.trim() === '') {
      valuearea.setCustomValidity('Value suggestion is required');
      showToast("Error", "The value suggestion text field is required to save the field review!", "error");
      return; // Stop execution if validation fails
    } else {
      valuearea.setCustomValidity('');
    }

    valuearea.reportValidity();
  } else if (initialReviewerSuggestions[selectedKey]) { // Check if the state is "ok" and if there's a valid suggestion
    var fieldElement = document.getElementById("field_" + selectedKey);
    if (fieldElement) {
      var valueElement = fieldElement.querySelector('.value');
      if (valueElement) {
        valueElement.innerText = initialReviewerSuggestions[selectedKey];
      }
    }
  }

  if (Object.keys(current_review["reviews"]).length === 0 &&
    current_review["reviews"].constructor === Object) {
    current_review["reviews"] = [];
  }

  if (selectedKey) {
    var reviewFound = false;

    for (let i = 0; i < current_review["reviews"].length; i++) {
      if (current_review["reviews"][i]["key"] === selectedKey) {
        reviewFound = true;
        console.log("review" + current_review["reviews"][i]["fieldReview"]);
        if (!Array.isArray(current_review["reviews"][i]["fieldReview"])) {
          current_review["reviews"][i]["fieldReview"] = [current_review["reviews"][i]["fieldReview"]];
        }
        var element = document.querySelector('[aria-selected="true"]');
        var category = element.getAttribute("data-bs-target");
        current_review["reviews"][i]["fieldReview"].push({
          "timestamp": Date.now(),
          "user": "oep_contributor", // TODO put actual username
          "role": "contributor",
          "contributorValue": selectedFieldValue,
          "newValue": selectedState === "ok" ? initialReviewerSuggestions[selectedKey] : "",
          "comment": document.getElementById("commentarea").value,
          "additionalComment": document.getElementById("comments").value,
          "reviewerSuggestion": document.getElementById("valuearea").value,
          "state": selectedState,
        });
        // Aktualisiere die HTML-Elemente mit den eingegebenen Werten
        var fieldElement = document.getElementById("field_" + selectedKey);
        var suggestionElement = fieldElement.querySelector('.suggestion--highlight');
        var commentElement = fieldElement.querySelector('.suggestion--comment');
        // var additionalCommentElement = fieldElement.querySelector('.suggestion--additional-comment');
        suggestionElement.innerText = document.getElementById("valuearea").value;
        commentElement.innerText = document.getElementById("commentarea").value;
        // additionalCommentElement.innerText = document.getElementById("comments").value;
        break;
      }
    }

    if (!reviewFound) {
      var element = document.querySelector('[aria-selected="true"]');
      var category = element.getAttribute("data-bs-target");
      current_review["reviews"].push({
        "category": selectedCategory,
        "key": selectedKey,
        "fieldReview": [
          {
            "timestamp": Date.now(),
            "user": "oep_contributor", // TODO put actual username
            "role": "contributor",
            "contributorValue": selectedFieldValue,
            "newValue": selectedState === "ok" ? initialReviewerSuggestions[selectedKey] : "",
            "comment": document.getElementById("commentarea").value,
            "additionalComment": document.getElementById("comments").value,
            "reviewerSuggestion": document.getElementById("valuearea").value,
            "state": selectedState,
          },
        ],
      });
      // Aktualisiere die HTML-Elemente mit den eingegebenen Werten
      var fieldElement = document.getElementById("field_" + selectedKey);
      var suggestionElement = fieldElement.querySelector('.suggestion--highlight');
      var commentElement = fieldElement.querySelector('.suggestion--comment');
      var additionalCommentElement = fieldElement.querySelector('.suggestion--additional-comment'); // For new comment

      suggestionElement.innerText = document.getElementById("valuearea").value;
      commentElement.innerText = document.getElementById("commentarea").value;
      additionalCommentElement.innerText = document.getElementById("comments").value; // Update new comment
    }
  }
  document.getElementById("comments").value = "";
  updateFieldColor();
  checkReviewComplete();
  selectNextField();
  renderSummaryPageFields();
  updateTabProgressIndicatorClasses();
}
initializeEventBindings(saveEntrancesForContributor);

function calculateOkPercentage(stateDict) {
  let totalCount = 0;
  let okCount = 0;

  if (!stateDict) {
    return "0.00";
  }

  for (let key in stateDict) {
    const fieldElement = document.getElementById(`field_${key}`);
    if (!fieldElement) continue;

    const fieldValue = $(fieldElement).find('.value').text().replace(/\s+/g, ' ').trim();
    if (!isEmptyValue(fieldValue)) {
      totalCount++;
      if (stateDict[key] === "ok") {
        okCount++;
      }
    }
  }

  const percentage = totalCount === 0 ? 0 : (okCount / totalCount) * 100;
  return percentage.toFixed(2);
}

function updatePercentageDisplay() {
  if (!window.state_dict) return;

  const percentage = parseFloat(calculateOkPercentage(window.state_dict));

  // Circle elements
  const circle = document.getElementById("okProgressCircle");
  const textEl =
    document.getElementById("okPercentageText") ||
    document.getElementById("percentageDisplay");

  if (circle) {
    // radius must match the SVG circle (r="52" in CSS)
    const radius = 52;
    const circumference = 2 * Math.PI * radius;

    // ensure dasharray is set
    circle.style.strokeDasharray = `${circumference}`;

    const offset = circumference - (percentage / 100) * circumference;
    circle.style.strokeDashoffset = `${offset}`;
  }

  if (textEl) {
    textEl.textContent = `${percentage.toFixed(2)}%`;
  }
}

// Expose for other modules (e.g. summary.js)
window.updatePercentageDisplay = updatePercentageDisplay;
