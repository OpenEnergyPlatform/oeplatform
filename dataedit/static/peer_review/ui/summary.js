// SPDX-FileCopyrightText: 2025 Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Daryna Barabanova <https://github.com/Darynarli> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2026 Vismaya Jochem <https://github.com/vismayajochem> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

import { current_review, selectedState } from "../core/peer_review.js";
import { getFieldState } from "../core/state_current_review.js";
import {
  isEmptyValue,
  isEffectivelyEmpty,
  sendJson,
  escapeHtml,
} from "../utilities.js";
import { updatePercentageDisplay } from "./navigation.js";
export function renderSummaryPageFields() {
  const acceptedFields = [];
  const suggestingFields = [];
  const rejectedFields = [];
  const missingFields = [];
  const emptyFields = [];

  const processedFields = new Set();

  if (window.state_dict && Object.keys(window.state_dict).length > 0) {
    const fields = document.querySelectorAll(".field");
    for (let field of fields) {
      let field_id = field.id.slice(6);
      const fieldValue = $(field)
        .find(".value")
        .text()
        .replace(/\s+/g, " ")
        .trim();
      const fieldState = getFieldState(field_id);
      const fieldCategory = field.getAttribute("data-category");
      const fieldSuggestion =
        field
          .querySelector(".suggestion.suggestion--highlight")
          ?.textContent.trim() || "";

      // ADD THIS: read comment from DOM just like fieldSuggestion
      const fieldComment =
        field.querySelector(".suggestion--comment")?.textContent.trim() ||
        field
          .querySelector(".suggestion--additional-comment")
          ?.textContent.trim() ||
        "";

      let fieldName = field_id.replace(/\./g, " ");

      if (fieldCategory !== "general") {
        fieldName = fieldName.split(" ").slice(1).join(" ");
      }

      const uniqueFieldIdentifier = `${fieldName}-${fieldCategory}`;

      if (isEffectivelyEmpty(field_id, fieldValue)) {
        emptyFields.push({
          fieldName,
          fieldValue,
          fieldCategory,
          fieldSuggestion,
          fieldComment, // now defined
        });
      } else if (fieldState === "ok") {
        acceptedFields.push({
          fieldName,
          fieldValue,
          fieldCategory,
          fieldSuggestion,
          fieldComment, // now defined
        });
        processedFields.add(uniqueFieldIdentifier);
      }

      for (const review of current_review.reviews) {
        const fieldDomId = `field_${review.key}`;
        const fieldEl = document.getElementById(fieldDomId);
        const fieldValue = fieldEl
          ? $(fieldEl).find(".value").text().replace(/\s+/g, " ").trim()
          : "";
        const fieldState = review.fieldReview.state;
        const fieldCategory = review.category;
        const field_id = field.id.slice(6);
        const fieldSuggestion = review.fieldReview.reviewerSuggestion || "";
        const fieldComment =
          review.fieldReview.comment ||
          review.fieldReview.additionalComment ||
          "";

        let fieldName = review.key.replace(/\./g, " ");

        if (fieldCategory !== "general") {
          fieldName = fieldName.split(" ").slice(1).join(" ");
        }

        const uniqueFieldIdentifier = `${fieldName}-${fieldCategory}`;

        if (processedFields.has(uniqueFieldIdentifier)) {
          continue;
        }

        if (isEffectivelyEmpty(field_id, fieldValue)) {
          emptyFields.push({
            fieldName,
            fieldValue,
            fieldCategory,
            fieldSuggestion,
            fieldComment,
          });
        } else if (fieldState === "ok") {
          acceptedFields.push({
            fieldName,
            fieldValue,
            fieldCategory,
            fieldSuggestion,
            fieldComment,
          });
        } else if (fieldState === "suggestion") {
          suggestingFields.push({
            fieldName,
            fieldValue,
            fieldCategory,
            fieldSuggestion,
            fieldComment,
          });
        } else if (fieldState === "rejected") {
          rejectedFields.push({
            fieldName,
            fieldValue,
            fieldCategory,
            fieldSuggestion,
            fieldComment,
          });
        }

        processedFields.add(uniqueFieldIdentifier);
      }
    }
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
      const fieldValue = $(field)
        .find(".value")
        .text()
        .replace(/\s+/g, " ")
        .trim();
      const found = current_review.reviews.some(
        (review) => review.key === field_id
      );
      const fieldState = getFieldState(field_id);
      const fieldCategory = field.getAttribute("data-category");
      const fieldSuggestion =
        field
          .querySelector(".suggestion.suggestion--highlight")
          ?.textContent.trim() || "";

      const fieldComment =
        field.querySelector(".suggestion--comment")?.textContent.trim() ||
        field
          .querySelector(".suggestion--additional-comment")
          ?.textContent.trim() ||
        "";

      let fieldName = field_id.replace(/\./g, " ");

      if (fieldCategory !== "general") {
        fieldName = fieldName.split(" ").slice(1).join(" ");
      }

      const uniqueFieldIdentifier = `${fieldName}-${fieldCategory}`;

      if (
        !found &&
        fieldState !== "ok" &&
        !isEffectivelyEmpty(field_id, fieldValue) &&
        !processedFields.has(uniqueFieldIdentifier)
      ) {
        missingFields.push({
          fieldName,
          fieldValue,
          fieldCategory,
          fieldSuggestion,
          fieldComment,
        });
        processedFields.add(uniqueFieldIdentifier);
      }
    }
  }

  const allData = [];
  allData.push(
    ...missingFields.map((item) => ({ ...item, fieldStatus: "Missing" }))
  );
  allData.push(
    ...acceptedFields.map((item) => ({ ...item, fieldStatus: "Accepted" }))
  );
  allData.push(
    ...suggestingFields.map((item) => ({ ...item, fieldStatus: "Suggested" }))
  );
  allData.push(
    ...rejectedFields.map((item) => ({ ...item, fieldStatus: "Rejected" }))
  );
  allData.push(
    ...emptyFields.map((item) => ({ ...item, fieldStatus: "Empty" }))
  );

  const categoriesMap = {};

  function addFieldToCategory(category, field) {
    if (!categoriesMap[category]) categoriesMap[category] = [];
    categoriesMap[category].push(field);
  }

  allData.forEach((item) => {
    const category = item.fieldCategory || "general";
    addFieldToCategory(category, item);
  });

  // ---- Render: condensed, grouped overview of the review state ----------
  injectSummaryStyles();

  const STATUS_META = {
    Accepted: { cls: "ok", label: "Accepted" },
    Suggested: { cls: "suggestion", label: "Suggested" },
    Rejected: { cls: "rejected", label: "Rejected" },
    Missing: { cls: "missing", label: "To review" },
    Empty: { cls: "empty", label: "Empty" },
  };
  // Within a category, surface the items needing attention first.
  const STATUS_ORDER = ["Rejected", "Suggested", "Missing", "Accepted"];
  const CATEGORY_LABELS = {
    general: "General",
    spatial: "Spatial",
    temporal: "Temporal",
    source: "Source",
    license: "License",
  };
  const CATEGORY_ORDER = ["general", "spatial", "temporal", "source", "license"];

  const counts = {};
  allData.forEach((f) => {
    counts[f.fieldStatus] = (counts[f.fieldStatus] || 0) + 1;
  });

  // Sticky overview bar: one colored-dot chip per state that occurs. Every chip
  // except "Empty" doubles as a filter toggle (Empty has no detail rows).
  const statsHtml = ["Accepted", "Suggested", "Rejected", "Missing", "Empty"]
    .filter((s) => counts[s])
    .map((s) => {
      const m = STATUS_META[s];
      const filterable = s !== "Empty";
      const cls = filterable ? " opr-summary__stat--filterable" : "";
      const attrs = filterable
        ? ` data-state="${m.cls}" role="button" tabindex="0"` +
          ` aria-pressed="false" title="Filter by ${m.label}"`
        : "";
      return (
        `<li class="opr-summary__stat opr-summary__stat--${m.cls}${cls}"${attrs}>` +
        `<span class="opr-summary__dot"></span>${counts[s]} ${m.label}</li>`
      );
    })
    .join("");

  // Per-category sections. Purely-empty fields are counted in the overview but
  // omitted from the detail list to keep it condensed.
  const sectionsHtml = CATEGORY_ORDER.filter((cat) => categoriesMap[cat])
    .map((cat) => {
      const rows = categoriesMap[cat]
        .filter((f) => f.fieldStatus !== "Empty")
        .sort(
          (a, b) =>
            STATUS_ORDER.indexOf(a.fieldStatus) -
            STATUS_ORDER.indexOf(b.fieldStatus)
        )
        .map((f) => summaryRowHtml(f, STATUS_META))
        .join("");
      if (!rows) return "";
      return (
        `<section class="opr-summary__section">` +
        `<h3 class="opr-summary__cat">${escapeHtml(CATEGORY_LABELS[cat] || cat)}</h3>` +
        `<ul class="opr-summary__list">${rows}</ul></section>`
      );
    })
    .join("");

  const summaryContainer = document.getElementById("summary");
  summaryContainer.innerHTML =
    `<div class="opr-summary">` +
    `<div class="opr-summary__overview"><ul class="opr-summary__stats">` +
    (statsHtml ||
      `<li class="opr-summary__stat opr-summary__stat--empty">` +
        `<span class="opr-summary__dot"></span>Nothing reviewed yet</li>`) +
    `</ul></div>` +
    (sectionsHtml ||
      `<p class="opr-summary__note">No reviewable fields in this review.</p>`) +
    `<p class="opr-summary__note opr-summary__nomatch" hidden>` +
    `No fields match this filter.</p>` +
    `</div>`;

  // Wire up the state-filter chips and re-apply any active filter (the selected
  // set persists in module scope across re-renders).
  attachSummaryFilter(summaryContainer);
  applySummaryFilter(summaryContainer);

  updateTabProgressIndicatorClasses();
  updatePercentageDisplay();
}

export function updateSubmitButtonColor() {
  // Color Save comment / new value
  $(submitButton).removeClass("btn-warning");
  $(submitCommentButton).removeClass("btn-warning");
  $(submitButton).removeClass("btn-danger");
  $(submitCommentButton).removeClass("btn-danger");
  if (selectedState === "suggestion") {
    $(submitButton).addClass("btn-warning");
  } else {
    $(submitCommentButton).addClass("btn-danger");
  }
}

function getOprRole() {
  return (
    document.getElementById("opr-page-marker")?.dataset?.oprPage || "reviewer"
  );
}

// A category tab shows a red dot while it still needs action this round, green
// ("done") once everything in it is handled. The rule depends on the role:
//   reviewer    — every non-empty field must have a state (ok/suggestion/rejected)
//   contributor — every field the reviewer left open (suggestion/rejected) must
//                 have a contributor response this round; accepted fields and
//                 empty fields need nothing.
function isCategoryDone(tabName, role, flagged, responded) {
  const fields = Array.from(document.querySelectorAll(`#${tabName} .field`));
  return fields.every((field) => {
    const key = field.id.replace("field_", "");
    const value = $(field).find(".value").text().replace(/\s+/g, " ").trim();
    if (isEffectivelyEmpty(key, value)) return true; // nothing to review

    if (role === "contributor") {
      // Done unless the reviewer flagged it and the contributor hasn't replied.
      return !(flagged.has(key) && !responded.has(key));
    }
    // Reviewer: done once the field carries any review state.
    return ["ok", "suggestion", "rejected"].includes(getFieldState(key));
  });
}

export function updateTabProgressIndicatorClasses() {
  const role = getOprRole();
  // Fields the reviewer left open (suggestion/deny), captured by the contributor
  // flow at load; empty for the reviewer role.
  const flagged = window.contributorOpenFields || new Set();
  const responded = new Set(
    ((current_review && current_review.reviews) || []).map((r) => r.key)
  );

  ["general", "spatiotemporal", "source", "license"].forEach((tabName) => {
    const tab = document.getElementById(`${tabName}-tab`);
    if (!tab) return;
    tab.classList.add("status"); // ensure the dot is rendered at all
    tab.classList.toggle(
      "status--done",
      isCategoryDone(tabName, role, flagged, responded)
    );
  });
}

window.addEventListener("DOMContentLoaded", updateTabProgressIndicatorClasses);

export const summaryTab = document.getElementById("summary-tab");
export const otherTabs = [
  document.getElementById("general-tab"),
  document.getElementById("spatiotemporal-tab"),
  document.getElementById("source-tab"),
  document.getElementById("license-tab"),
];
export const reviewContent = document.querySelector(".review__content");

document.addEventListener("DOMContentLoaded", function () {
  if (summaryTab && reviewContent) {
    summaryTab.addEventListener("click", () => {
      toggleReviewControls(false);
      reviewContent.classList.toggle("tab-pane--100");
    });
  } else {
    console.error("Summary tab or review content not found");
  }

  otherTabs.forEach((tab, index) => {
    if (tab) {
      tab.addEventListener("click", () => {
        toggleReviewControls(true);
        reviewContent.classList.remove("tab-pane--100");
      });
    } else {
      console.error(`Tab at index ${index} not found`);
    }
  });

  function toggleReviewControls(show) {
    const reviewControls = document.querySelector(".review__controls");
    if (reviewControls) {
      reviewControls.style.display = show ? "" : "none";
    }
  }
});

// ---- Condensed summary widget helpers ------------------------------------
// Field names arrive as space-joined key tokens (e.g. "licenses 0 path"). Array
// indices are zero-based in the data; show them as a human "#1" marker next to
// the element's sub-field instead of a bare "0".
function formatFieldName(name) {
  return String(name == null ? "" : name)
    .split(" ")
    .filter((t) => t !== "")
    .map((t) => (/^\d+$/.test(t) ? `#${parseInt(t, 10) + 1}` : t))
    .join(" ");
}

// Builds one row of the per-category summary list: a colored status dot, the
// field name + current value, the proposed value (for suggestions) and any
// comment. Colors mirror the field-state borders (green/yellow/red).
function summaryRowHtml(f, META) {
  const m = META[f.fieldStatus] || { cls: "empty", label: f.fieldStatus };
  const showSugg = f.fieldStatus === "Suggested" && f.fieldSuggestion;
  const value = f.fieldValue
    ? `<span class="opr-summary__value">${escapeHtml(f.fieldValue)}</span>`
    : "";
  const sugg = showSugg
    ? `<div class="opr-summary__suggestion">&rarr; ${escapeHtml(f.fieldSuggestion)}</div>`
    : "";
  const comment = f.fieldComment
    ? `<div class="opr-summary__comment">${escapeHtml(f.fieldComment)}</div>`
    : "";
  const name = escapeHtml(formatFieldName(f.fieldName));
  return (
    `<li class="opr-summary__row opr-summary__row--${m.cls}" data-state="${m.cls}">` +
    `<span class="opr-summary__dot" title="${escapeHtml(m.label)}"></span>` +
    `<div class="opr-summary__body">` +
    `<div class="opr-summary__line">` +
    `<span class="opr-summary__field">${name}</span>${value}` +
    `</div>${sugg}${comment}</div>` +
    `<span class="opr-summary__status opr-summary__status--${m.cls}">${escapeHtml(m.label)}</span>` +
    `</li>`
  );
}

// Inject the summary stylesheet once. The widget is rendered from JS and shared
// by the reviewer and contributor pages, so keeping its CSS here avoids
// duplicating it across both templates.
function injectSummaryStyles() {
  if (document.getElementById("opr-summary-styles")) return;
  const style = document.createElement("style");
  style.id = "opr-summary-styles";
  style.textContent = `
  .opr-summary { font-size: 0.9rem; color: #2b3b46; padding-bottom: 1rem; }
  .opr-summary__overview { position: sticky; top: 0; z-index: 2; background: #fff; padding: 0.75rem 0 0.9rem; margin-bottom: 1.1rem; border-bottom: 1px solid #e3e8ec; }
  .opr-summary__stats { list-style: none; display: flex; flex-wrap: wrap; gap: 0.4rem 1.4rem; margin: 0; padding: 0; }
  .opr-summary__stat { display: inline-flex; align-items: center; gap: 0.45rem; font-weight: 600; font-size: 0.85rem; }
  .opr-summary__dot { width: 10px; height: 10px; border-radius: 50%; background: #ced4da; flex: 0 0 auto; }
  .opr-summary__stat--ok .opr-summary__dot, .opr-summary__row--ok > .opr-summary__dot { background: #21A179; }
  .opr-summary__stat--suggestion .opr-summary__dot, .opr-summary__row--suggestion > .opr-summary__dot { background: #F0C808; }
  .opr-summary__stat--rejected .opr-summary__dot, .opr-summary__row--rejected > .opr-summary__dot { background: #CD4759; }
  .opr-summary__stat--missing .opr-summary__dot, .opr-summary__row--missing > .opr-summary__dot { background: #fff; box-shadow: inset 0 0 0 2px #adb5bd; }
  .opr-summary__stat--empty .opr-summary__dot { background: #e3e8ec; }
  .opr-summary__section { margin-bottom: 1.3rem; }
  .opr-summary__cat { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.07em; color: #6c757d; font-weight: 700; margin: 0 0 0.4rem; }
  .opr-summary__list { list-style: none; margin: 0; padding: 0; }
  .opr-summary__row { display: flex; align-items: flex-start; gap: 0.65rem; padding: 0.6rem 0.25rem; border-bottom: 1px solid #f0f3f5; }
  .opr-summary__row:last-child { border-bottom: 0; }
  .opr-summary__row > .opr-summary__dot { margin-top: 0.4rem; }
  .opr-summary__body { flex: 1 1 auto; min-width: 0; }
  .opr-summary__line { display: flex; flex-wrap: wrap; align-items: baseline; gap: 0.2rem 0.7rem; }
  .opr-summary__field { font-weight: 600; }
  .opr-summary__value { color: #6c757d; word-break: break-word; }
  .opr-summary__suggestion { color: #9a7d00; font-weight: 600; margin-top: 0.2rem; word-break: break-word; }
  .opr-summary__comment { font-style: italic; color: #56636b; margin-top: 0.2rem; word-break: break-word; }
  .opr-summary__status { flex: 0 0 auto; align-self: center; font-size: 0.66rem; text-transform: uppercase; letter-spacing: 0.04em; font-weight: 700; padding: 0.12rem 0.55rem; border-radius: 0.8rem; white-space: nowrap; }
  .opr-summary__status--ok { background: #e7f6f0; color: #13825F; }
  .opr-summary__status--suggestion { background: #fdf6cf; color: #7a6600; }
  .opr-summary__status--rejected { background: #fbe3e7; color: #a32f3e; }
  .opr-summary__status--missing { background: #eef1f3; color: #56636b; }
  .opr-summary__note { color: #6c757d; padding: 0.5rem 0.25rem; }
  .opr-summary__stat--filterable { cursor: pointer; border: 1px solid transparent; border-radius: 1rem; padding: 0.12rem 0.6rem; transition: background 0.12s ease, opacity 0.12s ease; }
  .opr-summary__stat--filterable:hover { background: #f0f3f5; }
  .opr-summary__stat--filterable:focus-visible { outline: 2px solid #2972A6; outline-offset: 1px; }
  .opr-summary__stat--filterable.is-active { background: #eef3f7; border-color: #cdd8e0; }
  .opr-summary__stat--filterable.is-dimmed { opacity: 0.4; }
  `;
  document.head.appendChild(style);
}

// Selected review states to show in the summary. Empty set = show all. Module
// scope so the choice survives the re-render after each save.
const summaryFilter = new Set();

// Attach click/keyboard toggles to the filter chips. Re-attached on every render
// because renderSummaryPageFields() replaces the container's innerHTML.
function attachSummaryFilter(container) {
  container
    .querySelectorAll(".opr-summary__stat--filterable")
    .forEach((chip) => {
      const toggle = () => {
        const state = chip.dataset.state;
        if (summaryFilter.has(state)) summaryFilter.delete(state);
        else summaryFilter.add(state);
        applySummaryFilter(container);
      };
      chip.addEventListener("click", toggle);
      chip.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          toggle();
        }
      });
    });
}

// Show only rows whose state is in summaryFilter (all when the set is empty),
// hide categories left with no visible rows, and reflect the selection on the
// chips. Pure DOM toggling — no re-render needed.
function applySummaryFilter(container) {
  const root = container.querySelector(".opr-summary");
  if (!root) return;
  const filtering = summaryFilter.size > 0;

  root.querySelectorAll(".opr-summary__stat--filterable").forEach((chip) => {
    const on = summaryFilter.has(chip.dataset.state);
    chip.setAttribute("aria-pressed", on ? "true" : "false");
    chip.classList.toggle("is-active", on);
    chip.classList.toggle("is-dimmed", filtering && !on);
  });

  root.querySelectorAll(".opr-summary__row").forEach((row) => {
    const show = !filtering || summaryFilter.has(row.dataset.state);
    row.style.display = show ? "" : "none";
  });

  let anyVisible = false;
  root.querySelectorAll(".opr-summary__section").forEach((sec) => {
    const visible = Array.from(
      sec.querySelectorAll(".opr-summary__row")
    ).some((r) => r.style.display !== "none");
    sec.style.display = visible ? "" : "none";
    if (visible) anyVisible = true;
  });

  const nomatch = root.querySelector(".opr-summary__nomatch");
  if (nomatch) nomatch.hidden = !(filtering && !anyVisible);
}
