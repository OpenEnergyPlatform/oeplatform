// SPDX-FileCopyrightText: 2025 Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Daryna Barabanova <https://github.com/Darynarli> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2026 Vismaya Jochem <https://github.com/vismayajochem> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

import { check_if_review_finished } from "./opr_reviewer_logic.js";
import {
  renderSummaryPageFields,
  updateSubmitButtonColor,
  updateTabProgressIndicatorClasses,
} from "./summary.js";
import { selectNextField, updatePercentageDisplay } from "./navigation.js";
import {
  isEmptyValue,
  isEffectivelyEmpty,
  sendJson,
  getCookie,
  getErrorMsg,
} from "./utilities.js";
import {
  getFieldState,
  updateClientStateDict,
} from "./state_current_review.js";
import { isReviewerComplete, reviewerHasChanges } from "./selectors.js";
import { saveReview, submitReview } from "./api.js";
import { renderAllFieldHistories } from "./field_history.js";
import {
  updateFieldDescription,
  highlightSelectedField,
} from "./field_description.js";
import {
  clearInputFields,
  showReviewerOptions,
  hideReviewerOptions,
  showReviewerCommentsOptions,
  hideReviewerCommentsOptions,
} from "./input_toggles.js";

// Re-export utilities for other modules
export { getCookie, sendJson, getErrorMsg };

// Re-export so existing importers keep their import path while the
// implementation lives in its own module.
export { renderAllFieldHistories };
export { updateFieldDescription, highlightSelectedField };
export {
  clearInputFields,
  showReviewerOptions,
  hideReviewerOptions,
  showReviewerCommentsOptions,
  hideReviewerCommentsOptions,
};

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
  $("#submitButton").off("click").on("click", saveEntrancesFn);
  $("#submitCommentButton").off("click").on("click", saveEntrancesFn);
  $("#ok-button").off("click").on("click", saveEntrancesFn);

  // Global Review Actions
  $("#submit_summary").off("click").on("click", submitPeerReview);
  $("#peer_review-save").off("click").on("click", savePeerReview);
  $("#peer_review-cancel").off("click").on("click", cancelPeerReview);

  // Button State Toggles (Visual)
  $("#suggestion-button")
    .off("click")
    .on("click", () => {
      selectState("suggestion");
      updateSubmitButtonColor();
    });
  $("#rejected-button")
    .off("click")
    .on("click", () => {
      selectState("rejected");
      updateSubmitButtonColor();
    });
  $("#ok-button").on("click", () => {
    selectState("ok");
    updateSubmitButtonColor();
  });

  $(".nav-link").click(clearInputFields);
}

// --- Helper Functions ---
export function getAllFieldsAndValues() {
  const fields = document.querySelectorAll(".field");
  const fieldList = [];
  fields.forEach((field) => {
    const fieldName = field.id.slice(6);
    const fieldValue = $(field)
      .find(".value")
      .text()
      .replace(/\s+/g, " ")
      .trim();
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
  $(".field").each(function () {
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

// --- Core Logic ---
export function peerReview(config, checkState = false) {
  selectNextField();
  renderSummaryPageFields();
  updateTabProgressIndicatorClasses();
  updatePercentageDisplay();

  if (checkState && typeof window.state_dict !== "undefined") {
    check_if_review_finished();
  }
}

export function savePeerReview() {
  $("#peer_review-save").removeClass("d-none");
  saveReview(config, current_review)
    .then(function () {
      window.location = config.url_table;
    })
    .catch(function (err) {
      $("#peer_review-save").addClass("d-none");
      alert(getErrorMsg(err));
    });
}

export function submitPeerReview() {
  $("#peer_review-submitting").removeClass("d-none");
  submitReview(config, current_review)
    .then(function () {
      window.location = config.url_table;
    })
    .catch(function (err) {
      $("#peer_review-submitting").addClass("d-none");
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

  const submitButton = $("#submit_summary");

  if (allComplete) {
    submitButton.removeClass("disabled");
    if (!window.clientSideReviewFinished) {
      showToast(
        "Success",
        "You have reviewed all fields and can submit the review to get feedback!",
        "success"
      );
    }
  } else {
    submitButton.addClass("disabled");
  }
}

// --- Read-only mode for finished reviews ---
// Hide every editing affordance so a finished review can be inspected (states,
// comments, history) but not changed. The backend also rejects edits to a
// finished review (ReviewFinishedError) as defense in depth.
export function applyReadOnlyMode() {
  $("#ok-button, #suggestion-button, #rejected-button").prop("disabled", true);
  $(".review__btns").hide();
  $("#reviewer_remarks, #reviewer_comments").addClass("d-none");
  $("#submit_summary, #peer_review-save, #peer_review-delete").hide();
  $("#submitButton, #submitCommentButton").hide();
  // Hide only the progress circle, NOT the whole .content-finish-review: that
  // container also holds the category tab nav (#myTab), so hiding it would strip
  // the tabs and leave a read-only review stuck on the General pane.
  $(".ok-progress-wrapper").hide();
  document.body.classList.add("opr-readonly");
}

export function getCategoryToTabIdMapping() {
  return {
    general: "general-tab",
    spatial: "spatiotemporal-tab",
    temporal: "spatiotemporal-tab",
    source: "source-tab",
    license: "license-tab",
  };
}

export function showToast(title, message, type) {
  var toast = document.getElementById("liveToast");
  var toastTitle = document.getElementById("toastTitle");
  var toastBody = document.getElementById("toastBody");

  toast.className = `toast hide ${type === "error" ? "bg-danger" : "bg-success"}`;
  toastTitle.textContent = title;
  toastBody.textContent = message;

  new bootstrap.Toast(toast).show();
}
