// SPDX-FileCopyrightText: 2025 Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

import { check_if_review_finished } from './opr_reviewer_logic.js';
import { renderSummaryPageFields, updateSubmitButtonColor, updateTabProgressIndicatorClasses } from "./summary.js";
import { selectNextField, updatePercentageDisplay } from "./navigation.js";
import { isEmptyValue, sendJson, getCookie, getErrorMsg } from "./utilities.js";
import { getFieldState, updateClientStateDict } from "./state_current_review.js";

// Re-export utilities for other modules
export { getCookie, sendJson, getErrorMsg };

// --- DOM Helpers ---
function getFieldElByKey(fieldKey) {
  return document.getElementById(`field_${fieldKey}`);
}

function normalizeFieldKey(fieldKey) {
  return String(fieldKey)
    .split('.')
    .filter(part => part !== '' && !/^\d+$/.test(part))
    .join('.');
}

function getTextFromEl(el, selectors) {
  if (!el) return '';
  for (const sel of selectors) {
    const found = el.querySelector(sel);
    const txt = found?.textContent?.replace(/\s+/g, ' ')?.trim();
    if (txt) return txt;
  }
  return '';
}

function getFallbackTitle(fieldKey) {
  const fieldEl = getFieldElByKey(fieldKey);
  return getTextFromEl(fieldEl, ['.field__label', '.label', 'label']) || fieldKey;
}

function getFallbackDescription(fieldKey) {
  const fieldEl = getFieldElByKey(fieldKey);
  const attr = fieldEl?.getAttribute('data-description') || fieldEl?.dataset?.description;
  
  if (attr && String(attr).trim()) return String(attr).trim();

  return getTextFromEl(fieldEl, ['.help-text', '.description']) || '';
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// --- State Management ---
window.selectedField = window.selectedField ?? null;
export let selectedFieldValue = null;
export let selectedState;
export let selectedCategory;
export let current_review;

export function setSelectedField(fieldKey) {
  window.selectedField = fieldKey;
}
export function setselectedFieldValue(fieldValue) {
  selectedFieldValue = fieldValue;
}
export function setSelectedCategory(value) {
  selectedCategory = value;
}

export function initCurrentReview(config) {
  current_review = {
    topic: config.topic,
    table: config.table,
    dateStarted: null,
    dateFinished: null,
    metadataVersion: "v1.6.0",
    reviews: [],
    reviewFinished: false,
    grantedBadge: null,
    metaMetadata: {
      reviewVersion: "OEP-0.1.0",
      metadataLicense: {
        name: "CC0-1.0",
        title: "Creative Commons Zero v1.0 Universal",
        path: "https://creativecommons.org/publicdomain/zero/1.0/",
      },
    },
  };
  window.current_review = current_review;
}

// --- Event Bindings ---
export function initializeEventBindings(saveEntrancesFn) {
  // Save actions
  $('#submitButton').off('click').on('click', saveEntrancesFn);
  $('#submitCommentButton').off('click').on('click', saveEntrancesFn);
  $('#ok-button').off('click').on('click', saveEntrancesFn);

  // Global Review Actions
  $('#submit_summary').off('click').on('click', submitPeerReview);
  $('#peer_review-save').off('click').on('click', savePeerReview);
  $('#peer_review-cancel').off('click').on('click', cancelPeerReview);

  // Button State Toggles (Visual)
  $('#suggestion-button').off('click').on('click', () => {
      selectState('suggestion'); 
      updateSubmitButtonColor();
  });
  $('#rejected-button').off('click').on('click', () => {
      selectState('rejected');
      updateSubmitButtonColor();
  });
  $('#ok-button').on('click', () => {
      selectState('ok');
      updateSubmitButtonColor();
  });

  $('.nav-link').click(clearInputFields);
}

// --- Helper Functions ---
export function getAllFieldsAndValues() {
  const fields = document.querySelectorAll('.field');
  const fieldList = [];
  fields.forEach(field => {
    const fieldName = field.id.slice(6);
    const fieldValue = $(field).find('.value').text().replace(/\s+/g, ' ').trim();
    fieldList.push({ fieldName, fieldValue });
  });
  return fieldList;
}

export function makeFieldList() {
  var fieldElements = [];
  $(".field").each(function() {
    fieldElements.push(this.id);
  });
  return fieldElements;
}

export function selectField(fieldList, field) {
  if (field >= 0 && field < fieldList.length) {
    var element = fieldList[field];
    document.getElementById(element).click();
  }
}

export function selectState(state, shouldUpdateClient = false) {
  selectedState = state;
  const selectedKey = window.selectedField;
  if (selectedKey) {
    updateClientStateDict(selectedKey, state);
  }
  if (shouldUpdateClient) {
    check_if_review_finished();
  }
}

export function clearInputFields() {
  const v = document.getElementById("valuearea");
  const c = document.getElementById("commentarea");
  if(v) v.value = "";
  if(c) c.value = "";
}

// --- UI Toggles ---
export function showReviewerOptions() {
  $("#reviewer_remarks").removeClass('d-none');
}
export function hideReviewerOptions() {
  $("#reviewer_remarks").addClass('d-none');
}
export function showReviewerCommentsOptions() {
  $("#reviewer_comments").removeClass('d-none');
}
export function hideReviewerCommentsOptions() {
  $("#reviewer_comments").addClass('d-none');
}

// --- Core Logic ---
export function peerReview(config, checkState = false) {
  selectNextField();
  renderSummaryPageFields();
  updateTabProgressIndicatorClasses();
  updatePercentageDisplay();

  if (checkState && typeof window.state_dict !== 'undefined') {
    check_if_review_finished();
  }
}

export function savePeerReview() {
  $('#peer_review-save').removeClass('d-none');
  let json = JSON.stringify({reviewType: 'save', reviewData: current_review});
  sendJson("POST", config.url_peer_review, json).then(function() {
    window.location = config.url_table;
  }).catch(function(err) {
    $('#peer_review-save').addClass('d-none');
    alert(getErrorMsg(err));
  });
}

export function submitPeerReview() {
  $('#peer_review-submitting').removeClass('d-none');
  let json = JSON.stringify({reviewType: 'submit', reviewData: current_review});
  sendJson("POST", config.url_peer_review, json).then(function() {
    window.location = config.url_table;
  }).catch(function(err) {
    $('#peer_review-submitting').addClass('d-none');
    alert(getErrorMsg(err));
  });
}

export function cancelPeerReview() {
  window.location = config.url_table;
}

export function checkReviewComplete() {
  const fields = getAllFieldsAndValues();
  let allComplete = true;

  for (let field of fields) {
    const fieldState = getFieldState(field.fieldName);
    const isEmpty = isEmptyValue(field.fieldValue) || field.fieldValue === '0';

    if (!isEmpty && fieldState !== 'ok' && fieldState !== 'rejected' && fieldState !== 'suggestion') {
      allComplete = false;
      break;
    }
  }

  const submitButton = $('#submit_summary');
  
  if (allComplete) {
    submitButton.removeClass('disabled');
    if (!window.clientSideReviewFinished) {
        showToast("Success", "You have reviewed all fields and can submit the review to get feedback!", 'success');
    }
  } else {
    submitButton.addClass('disabled');
  }
}

export function updateFieldDescription(cleanedFieldKey, fieldValue) {
  const fieldDescriptionsElement = document.getElementById("field-descriptions");
  const selectedName = document.querySelector("#review-field-name");

  const rawKey = window.selectedField || cleanedFieldKey;
  const normalizedKey = normalizeFieldKey(rawKey);

  const fieldInfo = (fieldDescriptionsData && (fieldDescriptionsData[rawKey] || fieldDescriptionsData[cleanedFieldKey] || fieldDescriptionsData[normalizedKey])) || null;

  const titleText = fieldInfo?.title || getFallbackTitle(rawKey) || cleanedFieldKey;
  selectedName.textContent = `${titleText}${fieldValue ? ' — ' + fieldValue : ''}`;

  let html = '<div class="reviewer-item">';
  html += `<div class="reviewer-item__row"><h2 class="reviewer-item__title">${escapeHtml(fieldInfo?.title || titleText)}</h2></div>`;
  
  const desc = fieldInfo?.description || getFallbackDescription(rawKey) || 'No description available.';
  html += `<div class="reviewer-item__row"><div class="reviewer-item__key">Description:</div><div class="reviewer-item__value">${escapeHtml(desc)}</div></div>`;
  
  if (fieldInfo?.example) {
      html += `<div class="reviewer-item__row"><div class="reviewer-item__key">Example:</div><div class="reviewer-item__value">${fieldInfo.example}</div></div>`;
  }
  html += '</div>';
  
  fieldDescriptionsElement.innerHTML = html;
}

export function highlightSelectedField(fieldKey, highlightColor = '#F6F9FB') {
  if (!fieldKey) return;
  const reviewItem = document.querySelectorAll('.review__item');
  const selectedDiv = document.getElementById('field_' + fieldKey);

  reviewItem.forEach(div => div.style.backgroundColor = '');
  if (selectedDiv && !selectedDiv.classList.contains('field-ok')) {
    selectedDiv.style.backgroundColor = highlightColor;
  }
}

export function getCategoryToTabIdMapping() {
  return {
    'general': 'general-tab',
    'spatial': 'spatiotemporal-tab',
    'temporal': 'spatiotemporal-tab',
    'source': 'source-tab',
    'license': 'license-tab',
  };
}

export function showToast(title, message, type) {
  var toast = document.getElementById('liveToast');
  var toastTitle = document.getElementById('toastTitle');
  var toastBody = document.getElementById('toastBody');

  toast.className = `toast hide ${type === 'error' ? 'bg-danger' : 'bg-success'}`;
  toastTitle.textContent = title;
  toastBody.textContent = message;

  new bootstrap.Toast(toast).show();
}