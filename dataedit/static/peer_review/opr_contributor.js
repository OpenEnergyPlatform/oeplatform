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
    updateFieldDescription,
    highlightSelectedField

} from './peer_review.js';
window.selectState = common.selectState;

common.initializeEventBindings();
// OK Field View Change
$('#button').bind('click', hideReviewerOptions);




function click_field(fieldKey, fieldValue, category) {
  const cleanedFieldKey = fieldKey.replace(/\.\d+/g, '');

  switchCategoryTab(category);

  setSelectedField(fieldKey);

setselectedFieldValue(fieldValue);
    setSelectedCategory(category);

  updateFieldDescription(cleanedFieldKey, fieldValue);
  highlightSelectedField(fieldKey);

  const fieldState = getFieldState(fieldKey);

  if (fieldState === 'ok' || !fieldState || fieldState === 'rejected') {
    ["ok-button", "rejected-button"].forEach(btn => {
      document.getElementById(btn).disabled = true;
    });
  } else if (fieldState === 'suggestion') {
    ["ok-button", "rejected-button"].forEach(btn => {
      document.getElementById(btn).disabled = false;
    });
  } else {
    ["ok-button", "rejected-button", "suggestion-button"].forEach(btn => {
      document.getElementById(btn).disabled = false;
    });
  }

  clearInputFields();
  hideReviewerOptions();
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
/**
 * Saves selected state
 * @param fieldKey
 */

export function getFieldState(fieldKey) {
  // This function gets the state of a field
  return window.state_dict[fieldKey];
}

export function saveEntrances() {

  if (selectedState !== "ok" && selectedState !== "rejected") {
    // Get the valuearea element
    const valuearea = document.getElementById('valuearea');

    // const validityState = valuearea.validity;

    // Validate the valuearea before proceeding
    if (valuearea.value.trim() === '') {
      valuearea.setCustomValidity('Value suggestion is required');
      showToast("Error", "The value suggestion text field is required to save the field review!", "error");
      return; // Stop execution if validation fails
    } else {
      valuearea.setCustomValidity('');
    }

    valuearea.reportValidity();
  } else if (initialReviewerSuggestions[selectedField]) { // Check if the state is "ok" and if there's a valid suggestion
    var fieldElement = document.getElementById("field_" + selectedField);
    if (fieldElement) {
      var valueElement = fieldElement.querySelector('.value');
      if (valueElement) {
        valueElement.innerText = initialReviewerSuggestions[selectedField];
      }
    }
  }


  if (Object.keys(current_review["reviews"]).length === 0 &&
    current_review["reviews"].constructor === Object) {
    current_review["reviews"] = [];
  }

  if (selectedField) {
    var reviewFound = false;

    for (let i = 0; i < current_review["reviews"].length; i++) {
      if (current_review["reviews"][i]["key"] === selectedField) {
        reviewFound = true;
        // console.log("review" + current_review.reviews["reviews"][i]["fieldReview"]) //undefined "reviews"
        console.log("review" + current_review["reviews"][i]["fieldReview"]) //undefined "reviews"
        if (!Array.isArray(current_review["reviews"][i]["fieldReview"])) {
          current_review["reviews"][i]["fieldReview"] = [current_review["reviews"][i]["fieldReview"]];
        }
        var element = document.querySelector('[aria-selected="true"]');
        var category = element.getAttribute("data-bs-target");
        current_review["reviews"][i]["fieldReview"].push({
          "timestamp": Date.now(),
          "user": "oep_contributor", // TODO put actual username
          "role": "contributor",
          "contributorValue": selectedFieldValue,
          "newValue": selectedState === "ok" ? initialReviewerSuggestions[selectedField] : "",
          "comment": document.getElementById("commentarea").value,
          "additionalComment": document.getElementById("comments").value,
          "reviewerSuggestion": document.getElementById("valuearea").value,
          "state": selectedState,
        });
        // Aktualisiere die HTML-Elemente mit den eingegebenen Werten
        var fieldElement = document.getElementById("field_" + selectedField);
        var suggestionElement = fieldElement.querySelector('.suggestion--highlight');
        var commentElement = fieldElement.querySelector('.suggestion--comment');
        // var additionalCommentElement = fieldElement.querySelector('.suggestion--additional-comment');
        suggestionElement.innerText = document.getElementById("valuearea").value;
        commentElement.innerText = document.getElementById("commentarea").value;
        // additionalCommentElement.innerText = document.getElementById("comments").value;
        break;
      }
    }

    if (!reviewFound) {
      var element = document.querySelector('[aria-selected="true"]');
      var category = element.getAttribute("data-bs-target");
      current_review["reviews"].push({
        "category": selectedCategory,
        "key": selectedField,
        "fieldReview": [
          {
            "timestamp": Date.now(),
            "user": "oep_contributor", // TODO put actual username
            "role": "contributor",
            "contributorValue": selectedFieldValue,
            "newValue": selectedState === "ok" ? initialReviewerSuggestions[selectedField] : "",
            "comment": document.getElementById("commentarea").value,
            "additionalComment": document.getElementById("comments").value,
            "reviewerSuggestion": document.getElementById("valuearea").value,
            "state": selectedState,
          },
        ],
      });
      // Aktualisiere die HTML-Elemente mit den eingegebenen Werten
      var fieldElement = document.getElementById("field_" + selectedField);
      var suggestionElement = fieldElement.querySelector('.suggestion--highlight');
      var commentElement = fieldElement.querySelector('.suggestion--comment');
      var additionalCommentElement = fieldElement.querySelector('.suggestion--additional-comment'); // For new comment

      suggestionElement.innerText = document.getElementById("valuearea").value;
      commentElement.innerText = document.getElementById("commentarea").value;
      additionalCommentElement.innerText = document.getElementById("comments").value; // Update new comment

    }
  }
    document.getElementById("comments").value = "";
  updateFieldColor();
  checkReviewComplete();
  selectNextField();
  renderSummaryPageFields();
  updateTabProgressIndicatorClasses();
}


common.peerReview(config, true);