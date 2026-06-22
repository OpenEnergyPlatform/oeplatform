// SPDX-FileCopyrightText: 2025 Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Daryna Barabanova <https://github.com/Darynarli> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2026 Vismaya Jochem <https://github.com/vismayajochem> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

import { check_if_review_finished } from './opr_reviewer_logic.js';
import { renderSummaryPageFields, updateSubmitButtonColor, updateTabProgressIndicatorClasses } from "./summary.js";
import { selectNextField, updatePercentageDisplay } from "./navigation.js";
import {isEmptyValue, isEffectivelyEmpty, sendJson, getCookie, getErrorMsg} from "./utilities.js";
import { getFieldState, updateClientStateDict } from "./state_current_review.js";
import { isReviewerComplete, reviewerHasChanges } from "./selectors.js";
import { saveReview, submitReview } from "./api.js";

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

// Snapshot the current field inventory + states into the shape the pure
// selectors expect. Bridges the legacy DOM/global state to selectors.js while
// the full store migration is in progress (Phase 3).
export function snapshotReviewState() {
  const fields = getAllFieldsAndValues().map(({ fieldName, fieldValue }) => ({
    key: fieldName,
    isEmpty: isEffectivelyEmpty(fieldName, fieldValue),
  }));
  return { fields, fieldState: window.state_dict || {} };
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
  saveReview(config, current_review).then(function() {
    window.location = config.url_table;
  }).catch(function(err) {
    $('#peer_review-save').addClass('d-none');
    alert(getErrorMsg(err));
  });
}

export function submitPeerReview() {
  $('#peer_review-submitting').removeClass('d-none');
  submitReview(config, current_review).then(function() {
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
  // "All non-empty fields reviewed" — now via the tested selector instead of a
  // duplicated DOM loop (Phase 3 step B).
  const allComplete = isReviewerComplete(snapshotReviewState());

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


export function updateFieldDescription(resolvedKey, fieldValue) {
  const fieldDescriptionsElement = document.getElementById("field-descriptions");
  const selectedName = document.querySelector("#review-field-name");

  // Use the resolvedKey directly - it has already been matched
  // against fieldDescriptionsData in click_field
  const fieldInfo = (typeof fieldDescriptionsData !== 'undefined' && fieldDescriptionsData)
    ? fieldDescriptionsData[resolvedKey] || null
    : null;

  const rawKey = window.selectedField || resolvedKey;
  const titleText = fieldInfo?.title || getFallbackTitle(rawKey) || resolvedKey;
  
  selectedName.textContent = `${titleText}${fieldValue ? ' — ' + fieldValue : ''}`;
  selectedName.style.display = 'block';

  let html = '<div class="reviewer-item">';
  html += `<div class="reviewer-item__row">
    <h2 class="reviewer-item__title">${escapeHtml(titleText)}</h2>
  </div>`;

  const desc = fieldInfo?.description || getFallbackDescription(rawKey) || 'No description available.';
  html += `<div class="reviewer-item__row">
    <div class="reviewer-item__key">Description:</div>
    <div class="reviewer-item__value">${escapeHtml(desc)}</div>
  </div>`;

  if (fieldInfo?.example !== undefined) {
    html += `<div class="reviewer-item__row">
      <div class="reviewer-item__key">Example:</div>
      <div class="reviewer-item__value">${escapeHtml(String(fieldInfo.example))}</div>
    </div>`;
  }

  if (fieldInfo?.badge) {
    html += `<div class="reviewer-item__row">
      <div class="reviewer-item__key">Badge:</div>
      <div class="reviewer-item__value">${escapeHtml(fieldInfo.badge)}</div>
    </div>`;
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

// --- Per-field review history (the ping-pong between reviewer & contributor) ---
// Rendered inline under each field row as a native collapsible <details>, so it
// sits next to the value being discussed and is expandable on demand.
function historyItemHtml(contribution) {
  const role = contribution.role || 'unknown';
  const state = contribution.state || '';
  const when = contribution.timestamp
    ? new Date(contribution.timestamp).toLocaleString()
    : '';
  const previous = contribution.contributorValue || '';
  const proposed = contribution.newValue || contribution.reviewerSuggestion || '';
  const comment = contribution.comment || contribution.additionalComment || '';
  return (
    `<li class="opr-history__item opr-history__item--${escapeHtml(state)}">` +
    `<span class="opr-history__role">${escapeHtml(role)}</span> ` +
    `<span class="opr-history__state">${escapeHtml(state)}</span>` +
    (previous
      ? `<div class="opr-history__previous">was: ${escapeHtml(previous)}</div>`
      : '') +
    (proposed
      ? `<div class="opr-history__value">proposed: ${escapeHtml(proposed)}</div>`
      : '') +
    (comment ? `<div class="opr-history__comment">${escapeHtml(comment)}</div>` : '') +
    (when ? `<span class="opr-history__time">${escapeHtml(when)}</span>` : '') +
    `</li>`
  );
}

// Inject a collapsible history under every field row that has one. Idempotent.
export function renderAllFieldHistories() {
  const all = window.field_history || {};
  Object.keys(all).forEach(fieldKey => {
    const history = all[fieldKey] || [];
    if (history.length < 1) return;

    const fieldEl = document.getElementById('field_' + fieldKey);
    if (!fieldEl || fieldEl.querySelector('.opr-history')) return;

    const roundWord = history.length === 1 ? 'round' : 'rounds';
    const panelId = 'opr-hist-' + fieldKey.replace(/[^a-zA-Z0-9_-]/g, '_');

    // Bootstrap collapse so it animates smoothly and matches the page's other
    // accordions, instead of a native <details>.
    const wrapper = document.createElement('div');
    wrapper.className = 'opr-history';
    wrapper.innerHTML =
      `<button class="opr-history__toggle" type="button" ` +
      `data-bs-toggle="collapse" data-bs-target="#${panelId}" ` +
      `aria-expanded="false" aria-controls="${panelId}">` +
      `<span class="opr-history__caret" aria-hidden="true">›</span> ` +
      `Review history (${history.length} ${roundWord})</button>` +
      `<div class="collapse opr-history__panel" id="${panelId}">` +
      `<ul class="opr-history__list">${history.map(historyItemHtml).join('')}</ul>` +
      `</div>`;
    fieldEl.appendChild(wrapper);
  });
}

// --- Read-only mode for finished reviews ---
// Hide every editing affordance so a finished review can be inspected (states,
// comments, history) but not changed. The backend also rejects edits to a
// finished review (ReviewFinishedError) as defense in depth.
export function applyReadOnlyMode() {
  $('#ok-button, #suggestion-button, #rejected-button').prop('disabled', true);
  $('.review__btns').hide();
  $('#reviewer_remarks, #reviewer_comments').addClass('d-none');
  $('#submit_summary, #peer_review-save, #peer_review-delete').hide();
  $('#submitButton, #submitCommentButton').hide();
  $('.content-finish-review').hide();
  document.body.classList.add('opr-readonly');
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