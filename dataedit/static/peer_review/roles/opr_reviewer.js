// SPDX-FileCopyrightText: 2023 Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2023 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2023 Bryan Lancien <https://github.com/bmlancien> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2024 Daryna Barabanova <https://github.com/Darynarli> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2026 Vismaya Jochem <https://github.com/vismayajochem> © Reiner Lemoine Institut
// // SPDX-License-Identifier: AGPL-3.0-or-later

import {
  hideReviewerOptions,
  showReviewerOptions,
  showReviewerCommentsOptions,
  hideReviewerCommentsOptions, // Now available
  setSelectedField,
  setselectedFieldValue,
  clearInputFields,
  selectedState,
  selectedFieldValue,
  current_review,
  selectedCategory,
  setSelectedCategory,
  checkReviewComplete,
  showToast,
  highlightSelectedField,
  updateFieldDescription,
  initializeEventBindings,
  getErrorMsg,
} from "../core/peer_review.js";

import { deleteReview } from "../api.js";
import { check_if_review_finished } from "./opr_reviewer_logic.js";
import {
  getFieldState,
  setGetFieldState,
  updateClientStateDict,
} from "../core/state_current_review.js";
import {
  switchCategoryTab,
  selectNextField,
  updatePercentageDisplay,
} from "../ui/navigation.js";
import {
  renderSummaryPageFields,
  updateTabProgressIndicatorClasses,
} from "../ui/summary.js";
import { isEmptyValue, isEffectivelyEmpty } from "../utilities.js";
window.clientSideReviewFinished = window.clientSideReviewFinished ?? false;
let initialReviewerSuggestions = {};
document.addEventListener("DOMContentLoaded", function () {
  initializeEmptyFields();
});
window.addEventListener("load", function () {
  initializeEmptyFields();
});
window.clientSideReviewFinished = window.clientSideReviewFinished ?? false;
export function initReviewer() {
  initializeEventBindings(saveEntrancesForReviewer);

  $("#peer_review-delete").off("click").on("click", deletePeerReview);

  // Toggle Logic for Reviewer Buttons
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

  document
    .querySelectorAll(".suggestion--highlight")
    .forEach(function (suggestion) {
      var field = suggestion.id.split("_")[1];
      if (field) initialReviewerSuggestions[field] = suggestion.innerText;
    });

  renderSummaryPageFields();
  updateTabProgressIndicatorClasses();
  updatePercentageDisplay();

  if (typeof window.state_dict !== "undefined") {
    check_if_review_finished();
  }
}

function initializeEmptyFields() {
  const allFields = document.querySelectorAll(".field");

  allFields.forEach((fieldEl) => {
    const fieldKey = fieldEl.dataset.fieldkey;
    const fieldValue = fieldEl.dataset.fieldvalue;

    const isEmpty = isEffectivelyEmpty(fieldKey, fieldValue);

    if (isEmpty) {
      // Grey out
      const labelEl = fieldEl.querySelector(".key");
      const valueEl = fieldEl.querySelector(".value");

      if (labelEl) labelEl.style.color = "#6c757d";
      if (valueEl) valueEl.style.color = "#6c757d";

      // Add explanation message
      const safeKey = fieldKey.replace(/[^a-zA-Z0-9_-]/g, "_");

      if (!document.getElementById(`explanation_${safeKey}`)) {
        const explanationElement = document.createElement("p");
        explanationElement.id = `explanation_${safeKey}`;
        explanationElement.classList.add("explanation", "text-muted", "mt-1");
        explanationElement.innerText =
          "Field is empty. Reviewing is not possible.";
        fieldEl.appendChild(explanationElement);
      }

      // Disable clicking completely
      fieldEl.style.pointerEvents = "none";
      fieldEl.style.cursor = "not-allowed";
      fieldEl.style.opacity = "0.7";
    }
  });
}

function deletePeerReview() {
  if (!confirm("Are you sure?")) return;
  const reviewId = current_review.review_id || config.review_id;

  $("#peer_review-delete").addClass("d-none");
  deleteReview(config, current_review, reviewId)
    .then(() => (window.location = config.url_table))
    .catch((err) => {
      $("#peer_review-delete").removeClass("d-none");
      alert(getErrorMsg(err));
    });
}

/**
 * Expands all ancestor accordion panels containing the field element,
 * then scrolls the field into view once they are open.
 */
function expandAccordionsAndScrollToField(fieldKey) {
  const fieldElement = document.querySelector(
    `.field[data-fieldkey="${fieldKey}"]`
  );
  if (!fieldElement) return;

  // Collect all collapsed accordion-collapse ancestors
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
    // No accordions to open, scroll immediately
    scrollToField(fieldElement);
    return;
  }

  // Reverse so we open outermost first, then inner
  collapsedAncestors.reverse();

  // Open each accordion in sequence, waiting for each transition to finish
  function openNext(index) {
    if (index >= collapsedAncestors.length) {
      // All open, now scroll
      scrollToField(fieldElement);
      return;
    }

    const collapseEl = collapsedAncestors[index];

    // Find the toggle button for this accordion panel
    const toggleButton = document.querySelector(
      `[data-bs-target="#${collapseEl.id}"]`
    );

    if (!toggleButton) {
      // No button found, try next
      openNext(index + 1);
      return;
    }

    // Listen for when this panel finishes opening
    collapseEl.addEventListener("shown.bs.collapse", function handler() {
      collapseEl.removeEventListener("shown.bs.collapse", handler);
      openNext(index + 1);
    });

    // Click the toggle to open it
    toggleButton.click();
  }

  openNext(0);
}

/**
 * Scrolls the field element into view smoothly, centered vertically.
 */
function scrollToField(fieldElement) {
  fieldElement.scrollIntoView({ behavior: "smooth", block: "center" });
}

function click_field(fieldKey, fieldValue, category) {
  const isEmpty = isEffectivelyEmpty(fieldKey, fieldValue);

  if (isEmpty) {
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

  // Keep the action buttons disabled in read-only mode (finished / not your
  // turn) — the field is still selectable so the review can be inspected.
  const readOnly = document.body.classList.contains("opr-readonly");
  const buttons = ["ok-button", "rejected-button", "suggestion-button"];
  buttons.forEach((btn) => {
    const el = document.getElementById(btn);
    if (el) el.disabled = readOnly;
  });

  const fieldElementForMsg = document.querySelector(
    `.field[data-fieldkey="${fieldKey}"]`
  );
  if (fieldElementForMsg) {
    const safeKey = fieldKey.replace(/[^a-zA-Z0-9_-]/g, "_");
    let explanationElement = document.getElementById(`explanation_${safeKey}`);
    const labelEl = fieldElementForMsg.querySelector(".key");
    const valueEl = fieldElementForMsg.querySelector(".value");

    if (explanationElement) explanationElement.remove();
    if (labelEl) labelEl.style.color = "";
    if (valueEl) valueEl.style.color = "";
  }

  // Always start fresh visually
  clearInputFields();
  hideReviewerOptions();
  hideReviewerCommentsOptions();

  // --- NEW: Restore previous review entry if it exists ---
  const existingReview = current_review.reviews.find((r) => r.key === fieldKey);
  if (existingReview && existingReview.fieldReview) {
    const fr = existingReview.fieldReview;
    const previousState = fr.state;

    // Simulate clicking the correct state button to show the right UI
    if (previousState === "suggestion") {
      showReviewerOptions();
      hideReviewerCommentsOptions();
      const valuearea = document.getElementById("valuearea");
      const commentarea = document.getElementById("commentarea");
      if (valuearea) valuearea.value = fr.newValue || "";
      if (commentarea) commentarea.value = fr.comment || "";
    } else if (previousState === "rejected") {
      hideReviewerOptions();
      showReviewerCommentsOptions();
      const comments = document.getElementById("comments");
      if (comments) comments.value = fr.additionalComment || "";
    }
    // For 'ok', no extra UI needed, fields stay hidden
  }
  expandAccordionsAndScrollToField(fieldKey);
}
function updateFieldColor(fieldKey, state) {
  const safeId = "#field_" + fieldKey.replace(/\./g, "\\.");
  $(safeId).removeClass("field-ok field-suggestion field-rejected");
  $(safeId).addClass(`field-${state}`);
}

function saveEntrancesForReviewer() {
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
      user: "oep_reviewer",
      role: "reviewer",
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

    // Reflect the review in the field row.
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
  checkReviewComplete();
  renderSummaryPageFields();
  updateTabProgressIndicatorClasses();
  updatePercentageDisplay();

  selectNextField();
  check_if_review_finished();
}
