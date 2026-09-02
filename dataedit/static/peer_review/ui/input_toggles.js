// SPDX-FileCopyrightText: 2025 Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Daryna Barabanova <https://github.com/Darynarli> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2026 Vismaya Jochem <https://github.com/vismayajochem> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

// Show/hide and reset helpers for the per-field response inputs (the value
// suggestion box and the comment/deny box). Pure DOM toggles shared by the
// reviewer and contributor flows. Extracted from peer_review.js as part of the
// Phase 3 frontend split; peer_review.js re-exports them so existing importers
// keep working.

export function clearInputFields() {
  const v = document.getElementById("valuearea");
  const c = document.getElementById("commentarea");
  if (v) v.value = "";
  if (c) c.value = "";
}

export function showReviewerOptions() {
  $("#reviewer_remarks").removeClass("d-none");
}
export function hideReviewerOptions() {
  $("#reviewer_remarks").addClass("d-none");
}
export function showReviewerCommentsOptions() {
  $("#reviewer_comments").removeClass("d-none");
}
export function hideReviewerCommentsOptions() {
  $("#reviewer_comments").addClass("d-none");
}
