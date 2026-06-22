// SPDX-FileCopyrightText: 2025 Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Daryna Barabanova <https://github.com/Darynarli> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2026 Vismaya Jochem <https://github.com/vismayajochem> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

// Renders the side panel describing the currently selected field (title,
// description, example, badge) and highlights the selected row. Falls back to
// text scraped from the field row when no entry exists in fieldDescriptionsData.
// Extracted from peer_review.js as part of the Phase 3 frontend split;
// peer_review.js re-exports these so existing importers keep working.

import { escapeHtml } from "./utilities.js";

// --- DOM helpers ---
function getFieldElByKey(fieldKey) {
  return document.getElementById(`field_${fieldKey}`);
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