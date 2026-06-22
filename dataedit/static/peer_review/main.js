// SPDX-FileCopyrightText: 2025 Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2026 Vismaya Jochem <https://github.com/vismayajochem> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Daryna Barabanova <https://github.com/Darynarli> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

import * as common from "./core/peer_review.js";
import { selectState } from './core/peer_review.js';
import { selectNextField, selectPreviousField, selectFirstReviewableField, selectFirstContributorField } from './ui/navigation.js';
import { setGetFieldState } from './core/state_current_review.js';

// Static imports avoid the "Failed to fetch" dynamic import errors
import { initReviewer } from './roles/opr_reviewer.js';
import { initContributor } from './roles/opr_contributor.js';

// Expose functions to global window scope for HTML onclick events
window.selectState = selectState;
window.selectNextField = selectNextField;
window.selectPreviousField = selectPreviousField;

// Initialize the state getter
setGetFieldState((fieldKey) => {
  return window.state_dict?.[fieldKey] ?? null;
});

document.addEventListener('DOMContentLoaded', function () {
  // Initialize common logic
  // 'config' is defined in the HTML template
  if (typeof config !== 'undefined') {
    common.initCurrentReview(config);
    common.peerReview(config, true);
  }

  // Initialize role-specific logic based on the HTML marker
  const marker = document.getElementById('opr-page-marker');
  const oprPage = marker?.dataset?.oprPage;

  if (oprPage === 'reviewer') {
    initReviewer();
    
    // Auto-select first reviewable field after all initialization is complete
    // Use a longer timeout to ensure all accordions, tabs, and state are ready
    setTimeout(() => {
      selectFirstReviewableField();
    }, 600);
    
  } else if (oprPage === 'contributor') {
    initContributor();

    // Auto-select the first field the reviewer flagged (suggested/denied), once
    // accordions, tabs and state are ready.
    setTimeout(() => {
      selectFirstContributorField();
    }, 600);

  } else {
    console.warn('OPR page marker not found or invalid; skipping role-specific initialization');
  }

  // Inline, collapsible per-field review history under each field row.
  common.renderAllFieldHistories();

  // Read-only when the review is finished OR it is not this actor's turn: the
  // review can be inspected (states, comments, per-field history) but not edited.
  if (typeof config !== 'undefined' && (config.read_only || config.review_finished)) {
    common.applyReadOnlyMode();
  }
});