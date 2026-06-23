// SPDX-FileCopyrightText: 2023 Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2023 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2023 Bryan Lancien <https://github.com/bmlancien> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Daryna Barabanova <https://github.com/Darynarli> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2026 Vismaya Jochem <https://github.com/vismayajochem> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

// NOTE: this mirrors much of opr_reviewer.js on purpose. The reviewer and
// contributor flows differ (the contributor only responds to fields the
// reviewer suggested/denied and never finishes/awards a badge), so they are kept
// as separate code paths for now. De-duplicating the shared parts (click_field,
// save, accordion scroll) is a task for the Phase 3 frontend refactor.

import {
  hideReviewerOptions,
  showReviewerOptions,
  showReviewerCommentsOptions,
  hideReviewerCommentsOptions,
  setSelectedField,
  setselectedFieldValue,
  clearInputFields,
  selectedState,
  selectedFieldValue,
  current_review,
  selectedCategory,
  setSelectedCategory,
  showToast,
  updateFieldDescription,
  highlightSelectedField,
  initializeEventBindings,
} from "../core/peer_review.js";

import { updateClientStateDict } from "../core/state_current_review.js";

// Fields the reviewer left open (suggestion/deny) — only these need a
// contributor response. Accepted fields are read-only for the contributor.
// Captured once at init from the reviewer's states, so it does not shift as the
// contributor responds.
let contributorOpenFields = new Set();
import {
  switchCategoryTab,
  selectNextField,
  updatePercentageDisplay,
} from "../ui/navigation.js";
import {
  renderSummaryPageFields,
  updateTabProgressIndicatorClasses,
} from "../ui/summary.js";
import { isEffectivelyEmpty } from "../utilities.js";

// --- Local Helpers ---

function updateFieldColor(fieldKey, state) {
  const safeId = "#field_" + fieldKey.replace(/\./g, "\\.");
  $(safeId).removeClass("field-ok field-suggestion field-rejected");
  $(safeId).addClass(`field-${state}`);
}

/**
 * Expands all ancestor accordion panels containing the field, then scrolls it
 * into view once they are open. (Duplicated from opr_reviewer.js; Phase 3 dedup.)
 */
function expandAccordionsAndScrollToField(fieldKey) {
  const fieldElement = document.querySelector(
    `.field[data-fieldkey="${fieldKey}"]`
  );
  if (!fieldElement) return;

  const collapsedAncestors = [];
  let parent = fieldElement.parentElement;
  while (parent) {
    if (
      parent.classList.contains("accordion-collapse") &&
      !parent.classList.contains("show")
    ) {
      collapsedAncestors.push(parent);
    }
    parent = parent.parentElement;
  }

  if (collapsedAncestors.length === 0) {
    fieldElement.scrollIntoView({ behavior: "smooth", block: "center" });
    return;
  }

  collapsedAncestors.reverse();

  function openNext(index) {
    if (index >= collapsedAncestors.length) {
      fieldElement.scrollIntoView({ behavior: "smooth", block: "center" });
      return;
    }
    const collapseEl = collapsedAncestors[index];
    const toggleButton = document.querySelector(
      `[data-bs-target="#${collapseEl.id}"]`
    );
    if (!toggleButton) {
      openNext(index + 1);
      return;
    }
    collapseEl.addEventListener("shown.bs.collapse", function handler() {
      collapseEl.removeEventListener("shown.bs.collapse", handler);
      openNext(index + 1);
    });
    toggleButton.click();
  }

  openNext(0);
}

// --- Main Initialization ---

export function initContributor() {
  initializeEventBindings(saveEntrancesForContributor);

  // Reveal the right inputs for the chosen response (mirror of the reviewer).
  $("#ok-button").on("click", () => {
    hideReviewerOptions();
    hideReviewerCommentsOptions();
  });
  $("#suggestion-button").on("click", () => {
    showReviewerOptions();
    hideReviewerCommentsOptions();
  });
  $("#rejected-button").on("click", () => {
    hideReviewerOptions();
    showReviewerCommentsOptions();
  });

  // Delegated event listener for field clicks
  document.addEventListener("click", function (event) {
    // Clicks inside the per-field history disclosure must not select the field.
    if (event.target.closest(".opr-history")) return;

    const field = event.target.closest(".field");
    if (!field) return;

    const fieldKey = field.dataset.fieldkey;
    const fieldValue = field.dataset.fieldvalue;
    const category = field.dataset.category;

    if (fieldKey && category !== undefined) {
      click_field(fieldKey, fieldValue, category);
    }
  });

  // The reviewer's open fields (suggestion/deny) are the ones the contributor
  // must respond to. Snapshot them from the reviewer's states at load.
  contributorOpenFields = new Set(
    Object.entries(window.state_dict || {})
      .filter(([, s]) => s === "suggestion" || s === "rejected")
      .map(([key]) => key)
  );
  // Expose for the summary's per-category dot indicator (red until every flagged
  // field in a category has a contributor response this round).
  window.contributorOpenFields = contributorOpenFields;

  // Initial renders
  renderSummaryPageFields();
  updateTabProgressIndicatorClasses();
  updatePercentageDisplay();

  // Submit stays disabled until every open field has a response.
  checkContributorComplete();
}

// The contributor may submit only once they have responded to every open
// (suggestion/deny) field; accepted fields need nothing.
function checkContributorComplete() {
  const responded = new Set(current_review.reviews.map((r) => r.key));
  const allResponded = [...contributorOpenFields].every((k) =>
    responded.has(k)
  );
  const submitButton = $("#submit_summary");
  if (allResponded) {
    submitButton.removeClass("disabled").prop("disabled", false);
  } else {
    submitButton.addClass("disabled").prop("disabled", true);
  }
}

function click_field(fieldKey, fieldValue, category) {
  if (isEffectivelyEmpty(fieldKey, fieldValue)) {
    return;
  }

  switchCategoryTab(category);
  setSelectedField(fieldKey);
  setselectedFieldValue(fieldValue);
  setSelectedCategory(category);

  const cleanedFieldKey = fieldKey.replace(/\.\d+/g, "");

  const candidateKeys = [
    `resources.${category}.${fieldKey}`,
    `resources.${category}.${cleanedFieldKey}`,
    `resources.${fieldKey}`,
    `resources.${cleanedFieldKey}`,
    fieldKey,
    cleanedFieldKey,
  ];

  let resolvedKey = cleanedFieldKey;
  if (typeof fieldDescriptionsData !== "undefined" && fieldDescriptionsData) {
    for (const candidate of candidateKeys) {
      if (fieldDescriptionsData[candidate]) {
        resolvedKey = candidate;
        break;
      }
    }
  }

  updateFieldDescription(resolvedKey, fieldValue);
  highlightSelectedField(fieldKey);

  // Only fields the reviewer left open (suggestion/deny) can be responded to;
  // accepted fields are read-only for the contributor. In read-only mode
  // (finished / not your turn) nothing is actionable.
  const readOnly = document.body.classList.contains("opr-readonly");
  const isOpen = contributorOpenFields.has(fieldKey);
  const actionable = isOpen && !readOnly;
  ["ok-button", "rejected-button", "suggestion-button"].forEach((btn) => {
    const el = document.getElementById(btn);
    if (el) el.disabled = !actionable;
  });
  $(".review__btns").toggle(actionable);

  // Always start fresh visually.
  clearInputFields();
  hideReviewerOptions();
  hideReviewerCommentsOptions();

  // Restore a previous contributor response for this field, if one was made in
  // this session.
  const existingReview = current_review.reviews.find((r) => r.key === fieldKey);
  if (
    existingReview &&
    existingReview.fieldReview &&
    !Array.isArray(existingReview.fieldReview)
  ) {
    const fr = existingReview.fieldReview;
    if (fr.state === "suggestion") {
      showReviewerOptions();
      hideReviewerCommentsOptions();
      const valuearea = document.getElementById("valuearea");
      const commentarea = document.getElementById("commentarea");
      if (valuearea) valuearea.value = fr.newValue || "";
      if (commentarea) commentarea.value = fr.comment || "";
    } else if (fr.state === "rejected") {
      hideReviewerOptions();
      showReviewerCommentsOptions();
      const comments = document.getElementById("comments");
      if (comments) comments.value = fr.additionalComment || "";
    }
  }

  expandAccordionsAndScrollToField(fieldKey);
}

function saveEntrancesForContributor() {
  if (selectedState === "rejected") {
    const comments = document.getElementById("comments");
    if (comments.value.trim() === "") {
      showToast("Error", "Comment is required for rejection!", "error");
      return;
    }
  } else if (selectedState === "suggestion") {
    const valuearea = document.getElementById("valuearea");
    if (valuearea.value.trim() === "") {
      showToast("Error", "Value suggestion is required!", "error");
      return;
    }
  }

  if (selectedState === "ok") {
    clearInputFields();
  }

  if (window.selectedField) {
    const currentKey = window.selectedField;
    let fieldExists = false;

    const reviewObj = {
      timestamp: Date.now(),
      user: "oep_contributor",
      role: "contributor",
      contributorValue: selectedFieldValue,
      newValue:
        selectedState === "suggestion"
          ? document.getElementById("valuearea").value
          : "",
      comment: document.getElementById("commentarea").value,
      additionalComment: document.getElementById("comments").value,
      reviewerSuggestion:
        selectedState === "suggestion"
          ? document.getElementById("valuearea").value
          : "",
      state: selectedState,
    };

    current_review.reviews.forEach(function (review, idx) {
      if (review["key"] === currentKey) {
        fieldExists = true;
        Object.assign(current_review["reviews"][idx], {
          category: selectedCategory,
          fieldReview: reviewObj,
        });
      }
    });

    if (!fieldExists) {
      current_review.reviews.push({
        category: selectedCategory,
        key: currentKey,
        fieldReview: reviewObj,
      });
    }

    updateFieldColor(currentKey, selectedState);
    updateClientStateDict(currentKey, selectedState);

    // Reflect the contributor's response in the field row.
    const fieldElement = document.getElementById("field_" + currentKey);
    if (fieldElement) {
      const suggEl = fieldElement.querySelector(".suggestion--highlight");
      const valueEl = fieldElement.querySelector(".value");
      // Accepting a suggestion means the proposed value becomes the value.
      if (selectedState === "ok" && suggEl && valueEl) {
        const accepted = suggEl.textContent.trim();
        if (accepted) valueEl.textContent = accepted;
      }
      if (suggEl) {
        suggEl.innerText =
          selectedState === "suggestion" ? reviewObj.reviewerSuggestion : "";
      }
      const commentEl = fieldElement.querySelector(".suggestion--comment");
      if (commentEl) {
        commentEl.innerText =
          selectedState === "suggestion" ? reviewObj.comment : "";
      }
      const denyEl = fieldElement.querySelector(
        ".suggestion--additional-comment"
      );
      if (denyEl) {
        denyEl.innerText =
          selectedState === "rejected" ? reviewObj.additionalComment : "";
      }
    }
  }

  document.getElementById("comments").value = "";
  checkContributorComplete();
  renderSummaryPageFields();
  updateTabProgressIndicatorClasses();
  updatePercentageDisplay();

  selectNextField();
}
