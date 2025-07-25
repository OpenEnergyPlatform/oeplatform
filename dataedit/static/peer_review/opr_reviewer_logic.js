// SPDX-FileCopyrightText: 2025 Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later
import {current_review, getAllFieldsAndValues, getErrorMsg, showToast} from "./peer_review.js";
import {isEmptyValue, sendJson} from "./utilities.js";
import {getFieldState} from "./state_current_review.js";
export function finishPeerReview() {
  $('#peer_review-submitting').removeClass('d-none');

  var selectedBadge = $('input[name="reviewer-option"]:checked').val();
  console.log(selectedBadge);
  current_review.badge = selectedBadge;
  current_review.reviewFinished = true;
  let json = JSON.stringify({reviewType: 'finished', reviewData: current_review, reviewBadge: selectedBadge});
  sendJson("POST", config.url_peer_review, json).then(function() {
    window.location = config.url_table;
  }).catch(function(err) {
    // TODO evaluate error, show user message
    $('#peer_review-submitting').addClass('d-none');
    alert(getErrorMsg(err));
  });
}
export function check_if_review_finished() {
    if (!checkFieldStates()) {
        return;
    }

    if (!clientSideReviewFinished) {
        clientSideReviewFinished = true;
        showToast("Review completed!", "You completed the review and can now award a suitable badge!", 'success');

        var reviewerDiv = $('<div class="bg-warning" id="finish-review-div"></div>');
        var bronzeRadio = $('<input type="radio" name="reviewer-option" value="bronze"> Bronze<br>');
        var silverRadio = $('<input type="radio" name="reviewer-option" value="silver"> Silver<br>');
        var goldRadio = $('<input type="radio" name="reviewer-option" value="gold"> Gold<br>');
        var platinRadio = $('<input type="radio" name="reviewer-option" value="platin"> Platin <br>');
        var reviewText = $('<p>The review is complete. Please award a badge and finish the review.</p>');
        var finishButton = $('<button type="button" id="review-finish-button">Finish</button>');

        reviewerDiv.append(reviewText);
        reviewerDiv.append(bronzeRadio);
        reviewerDiv.append(silverRadio);
        reviewerDiv.append(goldRadio);
        reviewerDiv.append(platinRadio);
        reviewerDiv.append(finishButton);

        finishButton.on('click', finishPeerReview);

        if (!config.review_finished) {
            reviewerDiv.show();
            $('#submit_summary').prop('disabled', true);
        } else {
            reviewerDiv.hide();
            $('#submit_summary').hide();
            $('#peer_review-save').hide();
            $('#review-window').css('visibility', 'hidden');
        }

        $('.content-finish-review').append(reviewerDiv);
    }
}

export function checkFieldStates() {
    const allFields = getAllFieldsAndValues();

    for (const { fieldName, fieldValue } of allFields) {
        if (!isEmptyValue(fieldValue)) {
            const fieldState = getFieldState(fieldName);

            if (fieldState !== 'ok' && fieldState !== 'rejected') {
                return false;
            }
        }
    }
    return true;
}
