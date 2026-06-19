// SPDX-FileCopyrightText: 2025 Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Daryna Barabanova <https://github.com/Darynarli> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2026 Vismaya Jochem <https://github.com/vismayajochem> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later
import {
  current_review,
  getErrorMsg,
  showToast,
  snapshotReviewState,
} from "./peer_review.js";
import { sendJson } from "./utilities.js";
import { isReviewerComplete, reviewerHasChanges } from "./selectors.js";
export function finishPeerReview() {
  $("#peer_review-submitting").removeClass("d-none");

  var selectedBadge = $('input[name="reviewer-option"]:checked').val();
  console.log(selectedBadge);
  current_review.badge = selectedBadge;
  current_review.reviewFinished = true;
  let json = JSON.stringify({
    reviewType: "finished",
    reviewData: current_review,
    reviewBadge: selectedBadge,
  });
  sendJson("POST", config.url_peer_review, json)
    .then(function () {
      window.location = config.url_table;
    })
    .catch(function (err) {
      // TODO evaluate error, show user message
      $("#peer_review-submitting").addClass("d-none");
      alert(getErrorMsg(err));
    });
}
export function check_if_review_finished() {
  // Reviewer-only flow: contributors never finish / award badges, so this must
  // not touch their controls (check_if_review_finished also runs on the
  // contributor page via peerReview()).
  const marker = document.getElementById("opr-page-marker");
  if (!marker || marker.dataset.oprPage !== "reviewer") {
    return;
  }

  // Not every non-empty field has a state yet -> offer nothing special.
  if (!checkFieldStates()) {
    hideFinishUI();
    return;
  }

  const submitButton = $("#submit_summary");

  // At least one field is suggested or rejected: the contributor has to
  // respond, so offer "Submit" (the ping-pong) and NOT the finish/badge UI.
  if (reviewHasChanges()) {
    hideFinishUI();
    submitButton.removeClass("disabled").prop("disabled", false);
    return;
  }

  // All non-empty fields are accepted: there is nothing to negotiate, so offer
  // the finish/badge option instead of submitting to the contributor.
  submitButton.prop("disabled", true);

  if (!window.clientSideReviewFinished) {
    window.clientSideReviewFinished = true;
    showToast(
      "Review completed!",
      "All fields are accepted – you can now award a badge and finish the review!",
      "success"
    );

    var reviewerDiv = $(
      '<div class="bg-warning" id="finish-review-div"></div>'
    );
    var bronzeRadio = $(
      '<input type="radio" name="reviewer-option" value="bronze"> Bronze<br>'
    );
    var silverRadio = $(
      '<input type="radio" name="reviewer-option" value="silver"> Silver<br>'
    );
    var goldRadio = $(
      '<input type="radio" name="reviewer-option" value="gold"> Gold<br>'
    );
    var platinRadio = $(
      '<input type="radio" name="reviewer-option" value="platin"> Platin <br>'
    );
    var reviewText = $(
      "<p>The review is complete. Please award a badge and finish the review.</p>"
    );
    var finishButton = $(
      '<button type="button" id="review-finish-button">Finish</button>'
    );

    reviewerDiv.append(reviewText);
    reviewerDiv.append(bronzeRadio);
    reviewerDiv.append(silverRadio);
    reviewerDiv.append(goldRadio);
    reviewerDiv.append(platinRadio);
    reviewerDiv.append(finishButton);

    finishButton.on("click", finishPeerReview);

    if (config.review_finished) {
      reviewerDiv.hide();
      $("#submit_summary").hide();
      $("#peer_review-save").hide();
      $("#review-window").css("visibility", "hidden");
    } else {
      reviewerDiv.show();
    }

    $(".content-finish-review").append(reviewerDiv);
  }
}

// Remove the finish/badge UI if it was shown but the review is no longer in the
// "all accepted" state (e.g. the reviewer changed a field to suggested).
function hideFinishUI() {
  if (window.clientSideReviewFinished) {
    $("#finish-review-div").remove();
    window.clientSideReviewFinished = false;
  }
}

// True if any non-empty field is suggested or rejected (i.e. there is something
// the contributor needs to respond to). Now via the tested selector.
function reviewHasChanges() {
  return reviewerHasChanges(snapshotReviewState());
}

// True when every non-empty field has a review state. Now via the tested
// selector (was a duplicated DOM loop).
export function checkFieldStates() {
  return isReviewerComplete(snapshotReviewState());
}
