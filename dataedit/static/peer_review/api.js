// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// Phase 3 step C: all Open Peer Review backend calls go through this module, so
// request shaping lives in one place. Callers keep their own UI side effects
// (showing spinners, redirect on success, error toasts) — these functions just
// build the payload and return the sendJson promise.

import { sendJson } from "./utilities.js";

// Pure: build the POST body for a review action. Exported so it can be unit
// tested without touching the network.
export function reviewPayload(reviewType, currentReview, extra = {}) {
  return { reviewType, reviewData: currentReview, ...extra };
}

function post(config, payload) {
  return sendJson("POST", config.url_peer_review, JSON.stringify(payload));
}

export function saveReview(config, currentReview) {
  return post(config, reviewPayload("save", currentReview));
}

export function submitReview(config, currentReview) {
  return post(config, reviewPayload("submit", currentReview));
}

export function finishReview(config, currentReview, badge) {
  return post(config, reviewPayload("finished", currentReview, { reviewBadge: badge }));
}

export function deleteReview(config, currentReview, reviewId) {
  return post(config, reviewPayload("delete", currentReview, { review_id: reviewId }));
}