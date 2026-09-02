// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// Pure derivations over the store state (Phase 3 foundation). This is the single
// place the two distinct actor rules live, so the reviewer/contributor UIs stop
// re-deriving them from the DOM:
//
//   Reviewer:    must review EVERY non-empty field; all-accepted -> Finish,
//                any suggestion/deny -> Submit (ping-pong).
//   Contributor: acts ONLY on fields the reviewer suggested/denied.
//
// All functions take the store state explicitly so they are trivially testable.

const REVIEWED = new Set(["ok", "suggestion", "rejected"]);
const CHANGES = new Set(["suggestion", "rejected"]);

export function getFieldState(state, key) {
  return state.fieldState?.[key] ?? null;
}

export function isReviewed(stateValue) {
  return REVIEWED.has(stateValue);
}

export function nonEmptyFields(state) {
  return (state.fields || []).filter((f) => !f.isEmpty);
}

// Progress = share of non-empty fields accepted (mirrors updateTabProgress).
export function reviewProgress(state) {
  const fields = nonEmptyFields(state);
  const total = fields.length;
  const accepted = fields.filter((f) => getFieldState(state, f.key) === "ok").length;
  const percent = total === 0 ? 0 : Math.round((accepted / total) * 100);
  return { total, accepted, percent };
}

// Reviewer: every non-empty field has a state.
export function isReviewerComplete(state) {
  const fields = nonEmptyFields(state);
  return fields.length > 0 && fields.every((f) => isReviewed(getFieldState(state, f.key)));
}

// Reviewer: there is at least one change to send to the contributor.
export function reviewerHasChanges(state) {
  return nonEmptyFields(state).some((f) => CHANGES.has(getFieldState(state, f.key)));
}

// Contributor: the fields the reviewer flagged (suggested/denied) — the only
// ones the contributor needs to respond to.
export function contributorTargets(state) {
  return nonEmptyFields(state).filter((f) => CHANGES.has(getFieldState(state, f.key)));
}