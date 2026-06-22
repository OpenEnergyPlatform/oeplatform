// SPDX-FileCopyrightText: 2025 Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Daryna Barabanova <https://github.com/Darynarli> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2026 Vismaya Jochem <https://github.com/vismayajochem> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

// Per-field review history (the ping-pong between reviewer & contributor).
// Rendered inline under each field row as a Bootstrap collapse, so it sits next
// to the value being discussed and is expandable on demand. Extracted from
// peer_review.js as part of the Phase 3 frontend split; peer_review.js re-exports
// renderAllFieldHistories so existing importers keep working.

import { escapeHtml } from "./utilities.js";

function historyItemHtml(contribution) {
  const role = contribution.role || "unknown";
  const state = contribution.state || "";
  const when = contribution.timestamp
    ? new Date(contribution.timestamp).toLocaleString()
    : "";
  const stateLabel =
    { ok: "Accepted", suggestion: "Suggestion", rejected: "Rejected" }[state] ||
    state;

  // Only a suggestion has a before/after value; a rejection has a reason; an
  // acceptance ("ok") just confirms the current value — so don't show a
  // misleading "was:" line for it.
  let body = "";
  if (state === "suggestion") {
    const previous = contribution.contributorValue || "";
    const proposed =
      contribution.newValue || contribution.reviewerSuggestion || "";
    const comment = contribution.comment || "";
    if (previous) {
      body += `<div class="opr-history__previous">was: ${escapeHtml(previous)}</div>`;
    }
    if (proposed) {
      body += `<div class="opr-history__value">proposed: ${escapeHtml(proposed)}</div>`;
    }
    if (comment) {
      body += `<div class="opr-history__comment">${escapeHtml(comment)}</div>`;
    }
  } else if (state === "rejected") {
    const reason = contribution.additionalComment || contribution.comment || "";
    if (reason) {
      body += `<div class="opr-history__comment">${escapeHtml(reason)}</div>`;
    }
  }

  return (
    `<li class="opr-history__item opr-history__item--${escapeHtml(state)}">` +
    `<span class="opr-history__role">${escapeHtml(role)}</span> ` +
    `<span class="opr-history__state">${escapeHtml(stateLabel)}</span>` +
    body +
    (when ? `<span class="opr-history__time">${escapeHtml(when)}</span>` : "") +
    `</li>`
  );
}

// Inject a collapsible history under every field row that has one. Idempotent.
export function renderAllFieldHistories() {
  const all = window.field_history || {};
  Object.keys(all).forEach((fieldKey) => {
    const history = all[fieldKey] || [];
    if (history.length < 1) return;

    const fieldEl = document.getElementById("field_" + fieldKey);
    if (!fieldEl || fieldEl.querySelector(".opr-history")) return;

    // If the field ended up accepted AFTER a change, show the agreed value in
    // the field header (with its green check) instead of the original — the
    // history below still shows the full chain. Accepted-as-is keeps the original.
    const latest = history[history.length - 1];
    if (latest && latest.state === "ok") {
      let agreed = "";
      for (let i = history.length - 1; i >= 0; i -= 1) {
        const v = history[i].newValue || history[i].reviewerSuggestion;
        if (v) {
          agreed = v;
          break;
        }
      }
      const valueEl = fieldEl.querySelector(".value");
      if (agreed && valueEl) valueEl.textContent = agreed;
    }

    const roundWord = history.length === 1 ? "round" : "rounds";
    const panelId = "opr-hist-" + fieldKey.replace(/[^a-zA-Z0-9_-]/g, "_");

    // Bootstrap collapse so it animates smoothly and matches the page's other
    // accordions, instead of a native <details>.
    const wrapper = document.createElement("div");
    wrapper.className = "opr-history";
    wrapper.innerHTML =
      `<button class="opr-history__toggle" type="button" ` +
      `data-bs-toggle="collapse" data-bs-target="#${panelId}" ` +
      `aria-expanded="false" aria-controls="${panelId}">` +
      `<span class="opr-history__caret" aria-hidden="true">›</span> ` +
      `Review history (${history.length} ${roundWord})</button>` +
      `<div class="collapse opr-history__panel" id="${panelId}">` +
      `<ul class="opr-history__list">${history.map(historyItemHtml).join("")}</ul>` +
      `</div>`;
    fieldEl.appendChild(wrapper);
  });
}
