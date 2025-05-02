import * as common from "./peer_review.js";

document.addEventListener('DOMContentLoaded', function () {
    common.initCurrentReview(config);
  common.peerReview(config, true);
});