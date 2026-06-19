// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// Phase 3 foundation: a single observable store for the OPR frontend.
//
// This is the future single source of truth. It is NOT yet wired into the
// existing modules — the reviewer/contributor UIs will adopt it incrementally so
// the DOM stops being the state store (see design note "10 - Phase 3"). Kept
// framework-free (no new runtime dependency) and pure enough to unit-test.

const listeners = new Set();

function initialState() {
  return {
    config: {}, // urls, table, review_id, ... from the template
    role: null, // 'reviewer' | 'contributor'
    fields: [], // inventory: [{ key, category, value, isEmpty }]
    review: { reviews: [] }, // the review datamodel (POSTed as reviewData)
    fieldState: {}, // key -> 'ok' | 'suggestion' | 'rejected' | null
    selection: { fieldKey: null, fieldValue: null, category: null, draftState: null },
  };
}

let state = initialState();

export function getState() {
  return state;
}

export function subscribe(listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function emit() {
  for (const listener of listeners) listener(state);
}

export function initStore({
  config = {},
  role = null,
  fields = [],
  review = null,
  fieldState = {},
} = {}) {
  state = {
    ...initialState(),
    config,
    role,
    fields,
    review: review ?? { reviews: [] },
    fieldState: { ...fieldState },
  };
  emit();
}

export function selectField({ fieldKey = null, fieldValue = null, category = null } = {}) {
  state.selection = { fieldKey, fieldValue, category, draftState: null };
  emit();
}

export function setDraftState(draftState) {
  state.selection = { ...state.selection, draftState };
  emit();
}

// Upsert a field's review (one entry per key) and mirror its state into
// fieldState. fieldReview is a single dict for the current turn.
export function setFieldReview(key, category, fieldReview) {
  const reviews = state.review.reviews;
  const existing = reviews.find((r) => r.key === key);
  if (existing) {
    existing.category = category;
    existing.fieldReview = fieldReview;
  } else {
    reviews.push({ key, category, fieldReview });
  }
  state.fieldState = { ...state.fieldState, [key]: fieldReview?.state ?? null };
  emit();
}

export function setFinished(finished, badge) {
  state.review.reviewFinished = finished;
  if (badge !== undefined) state.review.grantedBadge = badge;
  emit();
}

// Test hook: reset module state + listeners between tests.
export function _resetStore() {
  state = initialState();
  listeners.clear();
}