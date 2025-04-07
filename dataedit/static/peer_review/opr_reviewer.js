// this raises more errors as transition from script to module
// makes it more complicated to use onclick in html elements
// import { updateClientStateDict } from './frontend/state.js'
import * as common from './peer_review.js';
import {
    isEmptyValue,
    hideReviewerOptions,
    switchCategoryTab,
    setSelectedField,
    setselectedFieldValue,
    clearInputFields,
    selectedState,
    selectedField,
    selectedFieldValue,
    current_review,
    selectedCategory,
    setSelectedCategory,
    updateFieldColor,
    checkReviewComplete,
    selectNextField,
    renderSummaryPageFields,
    updateTabProgressIndicatorClasses,
    showToast,
    highlightSelectedField, updateFieldDescription,


} from './peer_review.js';
window.selectState = common.selectState;


common.initializeEventBindings();

export let clientSideReviewFinished = false;

// Delete review
$('#peer_review-delete').bind('click', deletePeerReview);
// OK Field View Change
$('#ok-button').bind('click', hideReviewerOptions);
// Suggestion Field View Change
$('#suggestion-button').bind('click', hideReviewerCommentOptions);
// Reject Field View Change
$('#rejected-button').bind('click', hideReviewerOptions);

/**
 * Configurates peer review
 * @param {json} config Configuration JSON from Django backend.
 */

function deletePeerReview() {
  // confirm
  if (!confirm("Are you sure?")) {
    return;
  }

  const json = JSON.stringify({ reviewType: 'delete', reviewData: current_review, review_id: current_review.review_id || config.review_id});

  $('#peer_review-delete').addClass('d-none');

  sendJson("POST", config.url_peer_review, json)
    .then(function() {
      window.location = config.url_table;
    })
    .catch(function(err) {
      $('#peer_review-delete').removeClass('d-none');
      alert(getErrorMsg(err));
    });
}

/**
 * Finish peer review and save to backend
 */
function finishPeerReview() {
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

/**
 * Identifies field name and value sets selected stlye and refreshes
 * reviewer box (side panel) infos.
 * @param value
 */

var fieldEvaluations = {}; // Object for tracking evaluated fields

function click_field(fieldKey, fieldValue, category) {
  const isEmpty = isEmptyValue(fieldValue);
  const cleanedFieldKey = fieldKey.replace(/\.\d+/g, '');

  switchCategoryTab(category);
  setSelectedField(fieldKey);

setselectedFieldValue(fieldValue);
    setSelectedCategory(category);

  updateFieldDescription(cleanedFieldKey, fieldValue);
  highlightSelectedField(fieldKey);

  const fieldState = getFieldState(fieldKey);
  const fieldWasEvaluated = fieldEvaluations[fieldKey];

  if (fieldState) {
    if (fieldState === 'ok' && !fieldWasEvaluated) {
      ["ok-button", "rejected-button", "suggestion-button"].forEach(btn => {
        document.getElementById(btn).disabled = true;
      });
    } else if (['suggestion', 'rejected'].includes(fieldState) || fieldWasEvaluated) {
      ["ok-button", "rejected-button", "suggestion-button"].forEach(btn => {
        document.getElementById(btn).disabled = false;
      });
    }
  } else {
    ["ok-button", "rejected-button", "suggestion-button"].forEach(btn => {
      document.getElementById(btn).disabled = isEmpty;
    });

    const explanationContainer = document.getElementById("explanation-container");
    const existingExplanation = explanationContainer.querySelector('.explanation');

    if (isEmpty && !existingExplanation) {
      const explanationElement = document.createElement('p');
      explanationElement.textContent = 'Field is empty. Reviewing is not possible.';
      explanationElement.classList.add('explanation');
      explanationContainer.appendChild(explanationElement);
    } else if (!isEmpty && existingExplanation) {
      explanationContainer.removeChild(existingExplanation);
    }
  }

  document.getElementById("ok-button").addEventListener('click', () => {
    fieldEvaluations[fieldKey] = 'ok';
  });
  document.getElementById("rejected-button").addEventListener('click', () => {
    fieldEvaluations[fieldKey] = 'rejected';
  });
  document.getElementById("suggestion-button").addEventListener('click', () => {
    fieldEvaluations[fieldKey] = 'suggestion';
  });

  clearInputFields();
  hideReviewerOptions();
  hideReviewerCommentOptions();
}


document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.field').forEach((field) => {
    field.addEventListener('click', () => {
      const fieldKey = field.getAttribute('data-fieldkey');
      const fieldValue = field.getAttribute('data-fieldvalue');
      const category = field.getAttribute('data-category');

      click_field(fieldKey, fieldValue, category);
    });
  });
});

// // Function to show the error toast
// function showErrorToast(liveToast) {
//   liveToast.show();
// }

/**
 * Saves field review to current review list
 */
export function saveEntrances() {
    if (selectedState === "rejected") {
        const comments = document.getElementById('comments');

        if (comments.value.trim() === '') {
            comments.setCustomValidity('Comment is required');
            showToast("Error", "The comment text field is required to save the field review!", "error");
            return;
        } else {
            comments.setCustomValidity('');
        }

        valuearea.reportValidity();
    }
    // If the field state is neither "ok" nor "rejected", user input should be checked for suggestions
    if (selectedState !== "ok" && selectedState !== "rejected") {
        const valuearea = document.getElementById('valuearea');

        if (valuearea.value.trim() === '') {
            valuearea.setCustomValidity('Value suggestion is required');
            showToast("Error", "The value suggestion text field is required to save the field review!", "error");
            return;
        } else {
            valuearea.setCustomValidity('');
        }

        valuearea.reportValidity();
    } else if (selectedState === "ok") {
        var fieldElement = document.getElementById("field_" + selectedField);
        if (fieldElement) {
            var valueElement = fieldElement.querySelector('.value');
            if (valueElement) {
                // Check if the suggested value was present before the page loaded
                if (initialReviewerSuggestions[selectedField] && initialReviewerSuggestions[selectedField].trim() !== '') {
                    // If the proposed value was previous, then we overwrite the original value with this proposal.
                    valueElement.innerText = initialReviewerSuggestions[selectedField];
                } else {
                    // Otherwise, set the original value
                    valueElement.innerText = selectedFieldValue;
                }
            }

            document.getElementById('valuearea').value = '';
            document.getElementById('commentarea').value = '';

            var suggestionElement = fieldElement.querySelector('.suggestion--highlight');
            if (suggestionElement) {
                suggestionElement.innerText = ''; // Clearing the proposed value
            }

            if (initialReviewerSuggestions[selectedField]) {
                initialReviewerSuggestions[selectedField] = ''; // Resetting a previously saved proposal
            }
        }
    }

    if (selectedField) {
        var fieldExists = false;

        current_review["reviews"].forEach(function(review, idx) {
            if (review["key"] === selectedField) {
                fieldExists = true;

                if (selectedState === "ok" || selectedState === "rejected") {
                    Object.assign(current_review["reviews"][idx], {
                        "category": selectedCategory,
                        "key": selectedField,
                        "fieldReview": {
                            "timestamp": Date.now(),
                            "user": "oep_reviewer",
                            "role": "reviewer",
                            "contributorValue": selectedFieldValue,
                            // If there was a suggested value before loading, save it as the new value
                            "newValue": initialReviewerSuggestions[selectedField] ? initialReviewerSuggestions[selectedField] : "",
                            "comment": document.getElementById("commentarea").value,
                            "additionalComment": document.getElementById("comments").value,
                            "reviewerSuggestion": "",
                            "state": selectedState,
                        },
                    });
                } else if (selectedState === "suggest" ){
                    Object.assign(current_review["reviews"][idx], {
                        "category": selectedCategory,
                        "key": selectedField,
                        "fieldReview": {
                            "timestamp": Date.now(),
                            "user": "oep_reviewer",
                            "role": "reviewer",
                            "contributorValue": selectedFieldValue,
                            "newValue": document.getElementById("valuearea").value,
                            "comment": document.getElementById("commentarea").value,
                            "additionalComment": document.getElementById("comments").value,
                            "reviewerSuggestion": document.getElementById("valuearea").value,
                            "state": selectedState,
                        },
                    });

                    var fieldElement = document.getElementById("field_" + selectedField);
                    if (fieldElement) {
                        var suggestionElement = fieldElement.querySelector('.suggestion--highlight');
                        var additionalCommentElement = fieldElement.querySelector('.suggestion--additional-comment');
                        if (suggestionElement) {
                            suggestionElement.innerText = document.getElementById("valuearea").value;
                        } if (additionalCommentElement) {
                            additionalCommentElement.innerText = document.getElementById("comments").value;
                        }
                    }
                }
            }
        });

        if (!fieldExists) {
            current_review["reviews"].push({
                "category": selectedCategory,
                "key": selectedField,
                "fieldReview": {
                    "timestamp": Date.now(),
                    "user": "oep_reviewer",
                    "role": "reviewer",
                    "contributorValue": selectedFieldValue,
                    "newValue": selectedState === "ok" ? (initialReviewerSuggestions[selectedField] || "") : document.getElementById("valuearea").value,
                    "comment": document.getElementById("commentarea").value,
                    "additionalComment": document.getElementById("comments").value,
                    "reviewerSuggestion": selectedState === "ok" ? "" : document.getElementById("valuearea").value,
                    "state": selectedState,
                },
            });

            var fieldElement = document.getElementById("field_" + selectedField);
            if (fieldElement) {
                var suggestionElement = fieldElement.querySelector('.suggestion--highlight');
                var additionalCommentElement = fieldElement.querySelector('.suggestion--additional-comment');
                if (suggestionElement) {
                    suggestionElement.innerText = document.getElementById("valuearea").value;
                } if (additionalCommentElement) {
                    additionalCommentElement.innerText = document.getElementById("comments").value;
                }
            }
        }
    }

    updateFieldColor();
    if (selectedState === "ok" ) {
        document.getElementById("valuearea").value = "";
        document.getElementById("commentarea").value = "";
    }
    document.getElementById("comments").value = "";
    checkReviewComplete();
    selectNextField();
    renderSummaryPageFields();
    updateTabProgressIndicatorClasses();
    check_if_review_finished();
}


/**
 * Checks if all fields are reviewed and activates submit button if ready
 */
/**
 * Returns a list of all fields and their values.
 * @returns {Array} List of objects with field names and values.
 */
export function getAllFieldsAndValues() {
  const fields = document.querySelectorAll('.field');
  const fieldList = [];

  fields.forEach(field => {
    const fieldName = field.id.slice(6);
    const fieldValue = $(field).find('.value').text().replace(/\s+/g, ' ').trim();
    fieldList.push({ fieldName, fieldValue });
  });

  return fieldList;
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

export function getFieldState(fieldKey) {
  if (window.state_dict && window.state_dict[fieldKey] !== undefined) {
    return window.state_dict[fieldKey];
  } else {
    // I don't like that this shows as an error in the console.log(Cannot get state for fieldKey "${fieldKey}"
    // because it is not found in stateDict or stateDict itself is null.);
    return null;
  }
}
/**
 * Checks if all fields are accepted and activates award badge div to finish the review.
 * Also deactivates the submitbutton.
 */
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

function hideReviewerCommentOptions() {
  $("#reviewer_comments").addClass('d-none');
}



function getTotalFieldCount() {
  var allFields = makeFieldList();
  return allFields.length;
}


function calculateOkPercentage(stateDict) {
  let totalCount = getTotalFieldCount();
  let okCount = 0;

  for (let key in stateDict) {
    if (stateDict[key] === "ok") {
      okCount++;
    }
  }

  let percentage = (okCount / totalCount) * 100;
  return percentage.toFixed(2);
}

function updatePercentageDisplay() {
  document.getElementById("percentageDisplay").textContent = calculateOkPercentage(window.state_dict);
}
common.peerReview(config, true);