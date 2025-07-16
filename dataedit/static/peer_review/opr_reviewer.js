// SPDX-FileCopyrightText: 2025 Bryan Lancien <https://github.com/bmlancien> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Daryna Barabanova <https://github.com/Darynarli> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Daryna Barabanova <https://github.com/Darynarli> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Christian Hofmann <https://github.com/christian-rli> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Daryna Barabanova <https://github.com/Darynarli> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Stephan Uller <https://github.com/steull> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 user <https://github.com/Darynarli> © Reiner Lemoine Institut
//
// SPDX-License-Identifier: AGPL-3.0-or-later

// this raises more errors as transition from script to module
// makes it more complicated to use onclick in html elements
// import { updateClientStateDict } from './frontend/state.js'
import * as common from './peer_review.js';
import {
    hideReviewerOptions,
    setSelectedField,
    setselectedFieldValue,
    clearInputFields,
    selectedState,
    selectedFieldValue,
    current_review,
    selectedCategory,
    setSelectedCategory,
    checkReviewComplete,
    showToast,
    highlightSelectedField, updateFieldDescription, initializeEventBindings, makeFieldList

} from './peer_review.js';
window.selectState = common.selectState;


import {check_if_review_finished, checkFieldStates } from './opr_reviewer_logic.js';
import {getFieldState, setGetFieldState} from "./state_current_review.js";
import {selectNextField, switchCategoryTab} from "./navigation.js";
import {renderSummaryPageFields, updateTabProgressIndicatorClasses} from "./summary.js";
import {isEmptyValue, updateFieldColor} from "./utilities.js";

window.clientSideReviewFinished = window.clientSideReviewFinished ?? false;

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
  const buttonEl = document.getElementById(btn);
  if (buttonEl) {
    buttonEl.disabled = true;
  }
});

    } else if (['suggestion', 'rejected'].includes(fieldState) || fieldWasEvaluated) {
      ["ok-button", "rejected-button", "suggestion-button"].forEach(btn => {
        document.getElementById(btn).disabled = false;
      });
    }
  } else {
    ["ok-button", "rejected-button", "suggestion-button"].forEach(btn => {
  const buttonEl = document.getElementById(btn);
  if (buttonEl) {
    buttonEl.disabled = isEmpty;
  }
});

const explanationContainer = document.getElementById("explanation-container");

if (explanationContainer) {
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
window.click_field = click_field;


/**
 * Saves field review to current review list
 */
function saveEntrancesForReviewer() {
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

initializeEventBindings(saveEntrancesForReviewer);



/**
 * Checks if all fields are reviewed and activates submit button if ready
 */
/**
 * Returns a list of all fields and their values.
 * @returns {Array} List of objects with field names and values.
 */



export function getFieldStateForReviewer(fieldKey) {
  if (window.state_dict && window.state_dict[fieldKey] !== undefined) {
    return window.state_dict[fieldKey];
  } else {
    // I don't like that this shows as an error in the console.log(Cannot get state for fieldKey "${fieldKey}"
    // because it is not found in stateDict or stateDict itself is null.);
    return null;
  }
}

setGetFieldState(getFieldStateForReviewer);

/**
 * Checks if all fields are accepted and activates award badge div to finish the review.
 * Also deactivates the submitbutton.
 */

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
