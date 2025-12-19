// SPDX-FileCopyrightText: 2025 Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

import * as common from "./peer_review.js";
import { selectState } from './peer_review.js';
window.selectState = selectState;

import { selectNextField } from './navigation.js'
window.selectNextField = selectNextField;

import { selectPreviousField } from './navigation.js'
window.selectPreviousField = selectPreviousField;

import { setGetFieldState } from './state_current_review.js';
// Load only the role-specific bundle for the current page.
// Templates set: <div id="opr-page-marker" data-opr-page="reviewer|contributor" ...>
const oprPage = document.getElementById('opr-page-marker')?.dataset?.oprPage;

if (oprPage === 'reviewer') {
  await import('./opr_reviewer.js');
} else if (oprPage === 'contributor') {
  await import('./opr_contributor.js');
} else {
  console.warn('OPR page marker not found; skipping role-specific bundle');
}

setGetFieldState((fieldKey) => {
  return window.state_dict?.[fieldKey] ?? null;
});
document.addEventListener('DOMContentLoaded', function () {
  common.initCurrentReview(config);
  common.peerReview(config, true);
});