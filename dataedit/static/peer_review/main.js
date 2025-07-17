// SPDX-FileCopyrightText: 2025 Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later
import * as common from "./peer_review.js";

document.addEventListener('DOMContentLoaded', function () {
    common.initCurrentReview(config);
  common.peerReview(config, true);
});