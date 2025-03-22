// this raises more errors as transition from script to module
// makes it more complicated to use onclick in html elements
// import { updateClientStateDict } from './frontend/state.js'

import {buttonStyles} from "../../../factsheet/frontend/src/styles/oep-theme/components/buttonStyles";

var selectedField;
var selectedFieldValue;
var selectedState;
var clientSideReviewFinished = false;

var current_review = {
  "topic": config.topic,
  "table": config.table,
  "dateStarted": null,
  "dateFinished": null,
  "metadataVersion": "v1.6.0",
  "reviews": [],
  "reviewFinished": false,
  "grantedBadge": null,
  "metaMetadata": {
    "reviewVersion": "OEP-0.1.0",
    "metadataLicense": {
      "name": "CC0-1.0",
      "title": "Creative Commons Zero v1.0 Universal",
      "path": "https://creativecommons.org/publicdomain/zero/1.0/",
    },
  },
};

// BINDS

// Submit field review
$('#submitButton').bind('click', saveEntrances);
$('#submitCommentButton').bind('click', saveEntrances);
$('#submitButton').bind('click', hideReviewerOptions);
$('#submitCommentButton').bind('click', hideReviewerOptions);
// Submit review (visible to contributor)
$('#submit_summary').bind('click', submitPeerReview);
// save the current review (not visible to contributor)
$('#peer_review-save').bind('click', savePeerReview);
// Cancel review
$('#peer_review-cancel').bind('click', cancelPeerReview);
// Delete review
$('#peer_review-delete').bind('click', deletePeerReview);
// OK Field View Change
$('#ok-button').bind('click', hideReviewerOptions);
$('#ok-button').bind('click', saveEntrances);
// Suggestion Field View Change
$('#suggestion-button').bind('click', showReviewerOptions);
$('#suggestion-button').bind('click', updateSubmitButtonColor);
$('#suggestion-button').bind('click', hideReviewerCommentOptions);

// Reject Field View Change
$('#rejected-button').bind('click', showReviewerCommentsOptions);
$('#rejected-button').bind('click', updateSubmitButtonColor);
$('#rejected-button').bind('click', hideReviewerOptions);

// Clear Input fields when new tab is selected
// nav items are selected via their class
$('.nav-link').click(clearInputFields);
// field items selector
/**
 * Returns name from cookies
 * @param {string} name Key to look up in cookie
 */
function getCookie(name) {
  var cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    var cookies = document.cookie.split(";");
    for (var i = 0; i < cookies.length; i++) {
      var cookie = $.trim(cookies[i]);
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}
/**
 * Get CSRF Token
 * @returns {string} CSRF Token
 */
function getCsrfToken() {
  var token1 = getCookie("csrftoken");
  return token1;
}

/**
 * Sends JSON to backend url
 * @param {string} method Get or post request
 * @param {string} url URL to send JSON to
 * @param {json} data Data to send to backend
 * @param {function} success Success function
 * @param {function} error Error function
 * @returns {value} AJAX function return
 */
function sendJson(method, url, data, success, error) {
  var token = getCsrfToken();
  return $.ajax({
    url: url,
    headers: {"X-CSRFToken": token},
    data_type: "json",
    cache: false,
    contentType: "application/json; charset=utf-8",
    processData: false,
    data: data,
    type: method,
    success: success,
    error: error,
  });
}

/**
 * Reads error message from response
 * @param {json} response Get or post request
 * @returns {string} Response error message
 */
function getErrorMsg(response) {
  try {
    var response_msg = (
      'Upload failed: ' + JSON.parse(response.responseJSON).error
    );
  } catch (e) {
    console.log(response);
    var response_msg = response.responseText;
  }
  return response_msg;
}

/**
 * Configurates peer review
 * @param {json} config Configuration JSON from Django backend.
 */
function peerReview(config) {
  /*
    TODO: Show loading icon if peer review page is loaded
    */

  // (function init() {
  //   $('#peer_review-loading').removeClass('d-none');
  //   config.form = $('#peer_review-form');
  // })();


  selectNextField();
  renderSummaryPageFields();
  updateTabProgressIndicatorClasses();
  // updatePercentageDisplay();
  if (state_dict) {
    check_if_review_finished();
  }
}

/**
 * Save peer review to backend
 */
function savePeerReview() {
  $('#peer_review-save').removeClass('d-none');
  json = JSON.stringify({reviewType: 'save', reviewData: current_review});
  sendJson("POST", config.url_peer_review, json).then(function() {
    window.location = config.url_table;
  }).catch(function(err) {
    // TODO evaluate error, show user message
    $('#peer_review-save').addClass('d-none');
    alert(getErrorMsg(err));
  });
}
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
 * Submits peer review to backend
 */
function submitPeerReview() {
  $('#peer_review-submitting').removeClass('d-none');
  json = JSON.stringify({reviewType: 'submit', reviewData: current_review});
  sendJson("POST", config.url_peer_review, json).then(function() {
    window.location = config.url_table;
  }).catch(function(err) {
    // TODO evaluate error, show user message
    $('#peer_review-submitting').addClass('d-none');
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
  json = JSON.stringify({reviewType: 'finished', reviewData: current_review, reviewBadge: selectedBadge});
  sendJson("POST", config.url_peer_review, json).then(function() {
    window.location = config.url_table;
  }).catch(function(err) {
    // TODO evaluate error, show user message
    $('#peer_review-submitting').addClass('d-none');
    alert(getErrorMsg(err));
  });
}

/**
 * Cancels peer review and forwards to cancel url
 */
function cancelPeerReview() {
  window.location = config.url_table;
}


/**
 * Identifies field name and value sets selected stlye and refreshes
 * reviewer box (side panel) infos.
 * @param value
 */


function isEmptyValue(value) {
    return value === "" || value === "None" || value === "[]";
}

var fieldEvaluations = {}; // Object for tracking evaluated fields

function click_field(fieldKey, fieldValue, category) {
    var isEmpty = isEmptyValue(fieldValue);

    switchCategoryTab(category);

    selectedField = fieldKey;
    selectedFieldValue = fieldValue;
    selectedCategory = category;

    const cleanedFieldKey = fieldKey.replace(/\.\d+/g, '');
    const selectedName = document.querySelector("#review-field-name");
    selectedName.textContent = cleanedFieldKey + " " + fieldValue;
    const fieldDescriptionsElement = document.getElementById("field-descriptions");
    const reviewItem = document.querySelectorAll('.review__item');

    let selectedDivId = 'field_' + fieldKey;
    let selectedDiv = document.getElementById(selectedDivId);

    if (fieldDescriptionsData[cleanedFieldKey]) {
        let fieldInfo = fieldDescriptionsData[cleanedFieldKey];
        let fieldInfoText = '<div class="reviewer-item">';
        if (fieldInfo.title) {
            fieldInfoText += '<div class="reviewer-item__row"><h2 class="reviewer-item__title">' + fieldInfo.title + '</h2></div>';
        }
        if (fieldInfo.description) {
            fieldInfoText += '<div class="reviewer-item__row"><div class="reviewer-item__key">Description:</div><div class="reviewer-item__value">' + fieldInfo.description + '</div></div>';
        }
        if (fieldInfo.example) {
            fieldInfoText += '<div class="reviewer-item__row"><div class="reviewer-item__key">Example:</div><div class="reviewer-item__value">' + fieldInfo.example + '</div></div>';
        }
        if (fieldInfo.badge) {
            fieldInfoText += '<div class="reviewer-item__row"><div class="reviewer-item__key">Badge:</div><div class="reviewer-item__value">' + fieldInfo.badge + '</div></div>';
        }
        fieldInfoText += '<div class="reviewer-item__row reviewer-item__row--border">Does it comply with the required ' + fieldInfo.title + ' description convention?</div></div>';
        fieldDescriptionsElement.innerHTML = fieldInfoText;
    } else {
        fieldDescriptionsElement.textContent = "No description found";
    }

    const fieldState = getFieldState(fieldKey);
    const fieldWasEvaluated = fieldEvaluations[fieldKey]; // Check if the field has been evaluated
    if (fieldState) {
        if (fieldState === 'ok' && !fieldWasEvaluated) {
            document.getElementById("ok-button").disabled = true;
            document.getElementById("rejected-button").disabled = true;
            document.getElementById("suggestion-button").disabled = true;
        } else if (fieldState === 'suggestion' || fieldState === 'rejected' || fieldWasEvaluated) {
            document.getElementById("ok-button").disabled = false;
            document.getElementById("rejected-button").disabled = false;
            document.getElementById("suggestion-button").disabled = false;
        }
    } else {
        document.getElementById("ok-button").disabled = isEmpty;
        document.getElementById("rejected-button").disabled = isEmpty;
        document.getElementById("suggestion-button").disabled = isEmpty;
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

    // Save state if field is evaluated
    document.getElementById("ok-button").addEventListener('click', function() {
        fieldEvaluations[fieldKey] = 'ok';
    });
    document.getElementById("rejected-button").addEventListener('click', function() {
        fieldEvaluations[fieldKey] = 'rejected';
    });
    document.getElementById("suggestion-button").addEventListener('click', function() {
        fieldEvaluations[fieldKey] = 'suggestion';
    });

    reviewItem.forEach(function(div) {
        div.style.backgroundColor = '';
    });
    if (selectedDiv) {
        selectedDiv.style.backgroundColor = '#F6F9FB';
    }

    clearInputFields();
    hideReviewerOptions();
    hideReviewerCommentOptions();
}

// Initialize the review buttons state on page load
/**
 * Switch to the category tab if needed
 */
function switchCategoryTab(category) {
  const currentTab = document.querySelector('.tab-pane.active'); // Get the currently active tab
  const tabIdForCategory = getCategoryToTabIdMapping()[category];
  if (currentTab.getAttribute('id') !== tabIdForCategory) {
    // The clicked field does not belong to the current tab, switch to the next tab
    const targetTab = document.getElementById(tabIdForCategory);
    if (targetTab) {
      // The target tab exists, click the tab link to switch to it
      targetTab.click();
    }
  }
}


/**
 * Function to provide the mapping of category to the correct tab ID
 */
function getCategoryToTabIdMapping() {
  // Define the mapping of category to tab ID
  const mapping = {
    'general': 'general-tab',
    'spatial': 'spatiotemporal-tab',
    'temporal': 'spatiotemporal-tab',
    'source': 'source-tab',
    'license': 'license-tab',
  };
  return mapping;
}


/**
 * Creates List of all fields from html elements
 */
function makeFieldList() {
  var fieldElements = [];
  $(".field").each(function() {
    fieldElements.push(this.id);
  });
  // alert(fieldElements[14]);
  return fieldElements;
}

/**
 * Clears User Input fields
 */
function clearInputFields() {
  const reviewControls = document.querySelector('.review__controls');
  if (reviewControls) {
    document.getElementById("valuearea").value = "";
    document.getElementById("commentarea").value = "";
  }
}

/**
 * Selects the HTML field element after the current one and clicks it
 */
function selectNextField() {
  var fieldList = makeFieldList();
  var next = fieldList.indexOf('field_' + selectedField) + 1;
  selectField(fieldList, next);
}

/**
 * Selects the HTML field element previous to the current one and clicks it
 */
function selectPreviousField() {
  var fieldList = makeFieldList();
  var prev = fieldList.indexOf('field_' + selectedField) - 1;
  selectField(fieldList, prev);
}

/**
 * Clicks a Field after checking it exists
 */
function selectField(fieldList, field) {
  if (field >= 0 && field < fieldList.length) {
    var element = fieldList[field];
    document.getElementById(element).click();
  }
}

/**
 * Saves selected state
 * @param {string} state Selected state
 */
function selectState(state) { // eslint-disable-line no-unused-vars
  selectedState = state;
  updateClientStateDict(fieldKey = selectedField, state = state);
  check_if_review_finished();
}

/**
 * Saves selected state the client added.
 * As the state_dict is generated on page load (in django view)
 * based on the stored review, these updates will not be sent to the backend.
 * @param {string} fieldKey Identifiere of the field
 * @param {string} state Selected state
 */
function updateClientStateDict(fieldKey, state) {
  state_dict = state_dict ?? {};
  if (fieldKey in state_dict) {
    // console.log(`Der Schlüssel '${fieldKey}' ist vorhanden.`);
    state_dict[fieldKey] = state;
  } else {
    // console.log(`Der Schlüssel '${fieldKey}' ist nicht vorhanden.`);
    state_dict[fieldKey] = state;
  }
}

function renderSummaryPageFields() {
  const categoriesMap = {};

  function addFieldToCategory(category, field) {
    if (!categoriesMap[category]) categoriesMap[category] = [];
    categoriesMap[category].push(field);
  }

  const fields = document.querySelectorAll('.field');
  fields.forEach(field => {
    const field_id = field.id.slice(6);
    const fieldValue = $(field).find('.value').text().trim();
    const fieldState = getFieldState(field_id);
    const fieldCategory = field.getAttribute('data-category');
    let fieldName = field_id.replace(/\./g, ' ');
    if (fieldCategory !== "general") {
      fieldName = fieldName.split(' ').slice(1).join(' ');
    }

    let fieldStatus = isEmptyValue(fieldValue) ? 'Empty' :
                      fieldState === 'ok' ? 'Accepted' :
                      fieldState === 'suggestion' ? 'Suggested' :
                      fieldState === 'rejected' ? 'Rejected' : 'Missing';

    addFieldToCategory(fieldCategory, { fieldName, fieldValue, fieldStatus });
  });

  const summaryContainer = document.getElementById("summary");
  summaryContainer.innerHTML = '';

  const tabsNav = document.createElement('ul');
  tabsNav.className = 'nav nav-tabs';

  const tabsContent = document.createElement('div');
  tabsContent.className = 'tab-content';

  let firstTab = true;

  for (const category in categoriesMap) {
    const tabId = `tab-${category}`;

    const navItem = document.createElement('li');
    navItem.className = 'nav-item';
    navItem.innerHTML = `<button class="nav-link${firstTab ? ' active' : ''}" data-bs-toggle="tab" data-bs-target="#${tabId}">${category}</button>`;
    tabsNav.appendChild(navItem);

    const tabPane = document.createElement('div');
    tabPane.className = `tab-pane fade${firstTab ? ' show active' : ''}`;
    tabPane.id = tabId;

    const fields = categoriesMap[category];
    const singleFields = [];
    const groupedFields = {};

    fields.forEach(field => {
      const words = field.fieldName.split(' ');
      if (words.length === 1) {
        singleFields.push(field);
      } else {
        const prefix = words[0];
        const rest = words.slice(1);
        const indices = rest.filter(word => !isNaN(word));
        const nameWithoutIndices = rest.filter(word => isNaN(word)).join(' ');

        if (!groupedFields[prefix]) groupedFields[prefix] = { indexed: {}, noIndex: [] };

        if (indices.length > 0) {
          const indexKey = indices.map(num => (parseInt(num, 10) + 1)).join('.');
          if (!groupedFields[prefix].indexed[indexKey]) groupedFields[prefix].indexed[indexKey] = [];
          groupedFields[prefix].indexed[indexKey].push({ ...field, fieldName: nameWithoutIndices });
        } else {
          groupedFields[prefix].noIndex.push({ ...field, fieldName: nameWithoutIndices });
        }
      }
    });

    if (singleFields.length > 0) {
      const table = document.createElement('table');
      table.className = 'table review-summary';
      table.innerHTML = `
        <thead><tr><th>Status</th><th>Field Name</th><th>Field Value</th></tr></thead>
        <tbody>${singleFields.map(f => `
          <tr>
            <td class="status ${f.fieldStatus.toLowerCase()}">${f.fieldStatus}</td>
            <td>${f.fieldName}</td>
            <td>${f.fieldValue}</td>
          </tr>`).join('')}
        </tbody>`;
      tabPane.appendChild(table);
    }

    if (Object.keys(groupedFields).length > 0) {
      const accordionContainer = document.createElement('div');
      accordionContainer.className = 'accordion';
      accordionContainer.id = `accordion-${category}`;

      let accordionIndex = 0;
      for (const prefix in groupedFields) {
        const accordionItem = document.createElement('div');
        accordionItem.className = 'accordion-item';
        const headingId = `heading-${category}-${accordionIndex}`;
        const collapseId = `collapse-${category}-${accordionIndex}`;

        const { noIndex, indexed } = groupedFields[prefix];

        let innerHTML = '';

        if (noIndex.length > 0) {
          innerHTML += `
            <table class="table table-sm table-bordered">
              <thead><tr><th>Status</th><th>Field Name</th><th>Field Value</th></tr></thead>
              <tbody>${noIndex.map(f => `
                <tr>
                  <td class="status ${f.fieldStatus.toLowerCase()}">${f.fieldStatus}</td>
                  <td>${f.fieldName}</td>
                  <td>${f.fieldValue}</td>
                </tr>`).join('')}
              </tbody>
            </table>`;
        }

        if (Object.keys(indexed).length > 0) {
          const subAccordionId = `subAccordion-${category}-${accordionIndex}`;
          innerHTML += `<div class="accordion" id="${subAccordionId}">`;

          Object.entries(indexed).forEach(([idx, idxFields], idxAccordionIndex) => {
            const idxHeadingId = `idxHeading-${category}-${accordionIndex}-${idxAccordionIndex}`;
            const idxCollapseId = `idxCollapse-${category}-${accordionIndex}-${idxAccordionIndex}`;

            const tabLabel = ['source', 'license'].includes(category) ? 'fields' : `${prefix} ${idx}`;

            innerHTML += `
              <div class="accordion-item">
                <h2 class="accordion-header" id="${idxHeadingId}">
                  <button class="accordion-button collapsed" data-bs-toggle="collapse" data-bs-target="#${idxCollapseId}">
                    ${tabLabel}
                  </button>
                </h2>
                <div id="${idxCollapseId}" class="accordion-collapse collapse" data-bs-parent="#${subAccordionId}">
                  <div class="accordion-body">
                    <table class="table table-sm table-bordered">
                      <thead><tr><th>Status</th><th>Field Name</th><th>Field Value</th></tr></thead>
                      <tbody>${idxFields.map(f => `
                        <tr>
                          <td class="status ${f.fieldStatus.toLowerCase()}">${f.fieldStatus}</td>
                          <td>${f.fieldName}</td>
                          <td>${f.fieldValue}</td>
                        </tr>`).join('')}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>`;
          });

          innerHTML += `</div>`;
        }

        accordionItem.innerHTML = `
          <h2 class="accordion-header" id="${headingId}">
            <button class="accordion-button collapsed" data-bs-toggle="collapse" data-bs-target="#${collapseId}">
              ${['source', 'license'].includes(category) ? 'fields name' : prefix}
            </button>
          </h2>
          <div id="${collapseId}" class="accordion-collapse collapse" data-bs-parent="#accordion-${category}">
            <div class="accordion-body">${innerHTML}</div>
          </div>`;

        accordionContainer.appendChild(accordionItem);
        accordionIndex++;
      }
      tabPane.appendChild(accordionContainer);
    }

    tabsContent.appendChild(tabPane);
    firstTab = false;
  }
  const viewsNavItem = document.createElement('li');
  viewsNavItem.className = 'nav-item';
  viewsNavItem.innerHTML = <button class="nav-link" data-bs-toggle="tab" data-bs-target="#tab-views">views</button>;


  tabsNav.appendChild(viewsNavItem);

  const viewsPane = document.createElement('div');
  viewsPane.className = 'tab-pane fade';
  viewsPane.id = 'tab-views';

  const allFields = Object.entries(categoriesMap).flatMap(([category, fields]) =>
    fields.map(f => ({...f, category}))
  );

  viewsPane.innerHTML =
    <table class="table review-summary">
      <thead>
        <tr><th>Status</th><th>Category</th><th>Field Name</th><th>Field Value</th></tr>
      </thead>
      <tbody>${allFields.map(f =>
        <tr>
          <td class="status ${f.fieldStatus.toLowerCase()}">${f.fieldStatus}</td>
          <td>${f.category}</td>
          <td>${f.fieldName}</td>
          <td>${f.fieldValue}</td>
        </tr>).join('')}
      </tbody>
    </table>;

  tabsContent.appendChild(viewsPane);
  summaryContainer.appendChild(tabsNav);
  summaryContainer.appendChild(tabsContent);
  updateTabProgressIndicatorClasses();
}

/**
 * Creates an HTML list of fields with their categories
 * @param {Array} fields Array of field objects
 * @returns {string} HTML list of fields
 */
function createFieldList(fields) {
  return `
    <ul>
      ${fields.map((field) => `<li>${field.fieldCategory}: ${field.fieldValue}</li>`).join('')}
    </ul>
  `;
}

// // Function to show the error toast
// function showErrorToast(liveToast) {
//   liveToast.show();
// }

function showToast(title, message, type) {
  var toast = document.getElementById('liveToast');
  var toastTitle = document.getElementById('toastTitle');
  var toastBody = document.getElementById('toastBody');

  // Update the toast's header and body based on the type
  if (type === 'error') {
    toast.classList.remove('bg-success');
    toast.classList.add('bg-danger');
  } else if (type === 'success') {
    toast.classList.remove('bg-danger');
    toast.classList.add('bg-success');
  }

  // Set the title and body text
  toastTitle.textContent = title;
  toastBody.textContent = message;

  var bsToast = new bootstrap.Toast(toast);
  bsToast.show();
}
/**
 * Saves field review to current review list
 */
function saveEntrances() {
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

function getFieldState(fieldKey) {
  if (state_dict && state_dict[fieldKey] !== undefined) {
    return state_dict[fieldKey];
  } else {
    // I don't like that this shows as an error in the console.log(`Cannot get state for fieldKey "${fieldKey}"
    // because it is not found in stateDict or stateDict itself is null.`);
    return null;
  }
}
/**
 * Checks if all fields are reviewed and activates submit button if ready
 */
/**
 * Returns a list of all fields and their values.
 * @returns {Array} List of objects with field names and values.
 */
function getAllFieldsAndValues() {
  const fields = document.querySelectorAll('.field');
  const fieldList = [];

  fields.forEach(field => {
    const fieldName = field.id.slice(6);
    const fieldValue = $(field).find('.value').text().replace(/\s+/g, ' ').trim();
    fieldList.push({ fieldName, fieldValue });
  });

  return fieldList;
}



/**
 * Checks if all fields are reviewed and activates submit button if ready
 */
function checkReviewComplete() {
  const fields = getAllFieldsAndValues();

  for (let field of fields) {
    const fieldState = getFieldState(field.fieldName);

    const reviewed = current_review["reviews"].find((review) => review.key === field.fieldName);

    if (!reviewed && fieldState !== 'ok' && fieldState !== 'rejected' && !isEmptyValue(field.fieldValue)) {
      $('#submit_summary').addClass('disabled');
      return;
    }
  }
  $('#submit_summary').removeClass('disabled');
  if (!clientSideReviewFinished) {
    showToast("Success", "You have reviewed all fields and can submit the review to get feedback!", 'success');
  }
}

function checkFieldStates() {
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


/**
 * Checks if all fields are accepted and activates award badge div to finish the review.
 * Also deactivates the submitbutton.
 */
function check_if_review_finished() {
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


/**
 * Shows reviewer Comment and Suggestion Input options
 */
function showReviewerOptions() {
  $("#reviewer_remarks").removeClass('d-none');
}
function showReviewerCommentsOptions() {
  $("#reviewer_comments").removeClass('d-none');
}

/**
 * Hides reviewer Comment and Suggestion Input options
 */
function hideReviewerOptions() {
  $("#reviewer_remarks").addClass('d-none');
}
function hideReviewerCommentOptions() {
  $("#reviewer_comments").addClass('d-none');
}



/**
 * Colors Field based on Reviewer input
 */
function updateFieldColor() {
  // Color ok/suggestion/rejected
  field_id = `#field_${selectedField}`.replaceAll(".", "\\.");
  // console.log(field_id)
  $(field_id).removeClass('field-ok');
  $(field_id).removeClass('field-suggestion');
  $(field_id).removeClass('field-rejected');
  $(field_id).addClass(`field-${selectedState}`);
}

/**
 * Colors Field based on Reviewer input
 */
function updateSubmitButtonColor() {
  // Color Save comment / new value
  $(submitButton).removeClass('btn-warning');
  $(submitCommentButton).removeClass('btn-warning');
  $(submitButton).removeClass('btn-danger');
  $(submitCommentButton).removeClass('btn-danger');
  if (selectedState === "suggestion") {
    $(submitButton).addClass('btn-warning');
  } else {
    $(submitCommentButton).addClass('btn-danger');
  }
}

/**
 * Hide and show revier controles once the user clicks the summary tab
 */
const summaryTab = document.getElementById('summary-tab');
const otherTabs = [
  document.getElementById('general-tab'),
  document.getElementById('spatiotemporal-tab'),
  document.getElementById('source-tab'),
  document.getElementById('license-tab'),
];
const reviewContent = document.querySelector(".review__content");
function updateTabClasses() {
  const tabNames = ['general', 'spatiotemporal', 'source', 'license'];
  for (let i = 0; i < tabNames.length; i++) {
    let tabName = tabNames[i];
    let tab = document.getElementById(tabName + '-tab');
    if (!tab) continue;

    let fields = Array.from(document.querySelectorAll('#' + tabName + ' .field'));

    let allReviewed = fields.every(field => {
      let fieldValue = $(field).find('.value').text().replace(/\s+/g, ' ').trim();
      let fieldState = getFieldState(field.id.replace('field_', ''));
      return isEmptyValue(fieldValue) || ['ok', 'suggest', 'rejected'].includes(fieldState);
    });

    if (allReviewed) {
      tab.classList.add('status');
      tab.classList.add('status--done');
    } else {
      tab.classList.add('status');
      tab.classList.remove('status--done');
    }
  }
}

window.addEventListener('DOMContentLoaded', function() {
  updateTabClasses();
  // updatePercentageDisplay() ;
});



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
  document.getElementById("percentageDisplay").textContent = calculateOkPercentage(state_dict);
}



function updateTabProgressIndicatorClasses() {
  const tabNames = ['general', 'spatiotemporal', 'source', 'license'];

  for (let i = 0; i < tabNames.length; i++) {
    let tabName = tabNames[i];
    let tab = document.getElementById(tabName + '-tab');
    if (!tab) continue;

    let fieldsInTab = Array.from(document.querySelectorAll('#' + tabName + ' .field'));
    let values = getAllFieldsAndValues();

    let allReviewed = fieldsInTab.every((field, index) => {
      let fieldValue = $(field).find('.value').text().replace(/\s+/g, ' ').trim();
      let fieldState = getFieldState(field.id.replace('field_', ''));
      return isEmptyValue(fieldValue) || ['ok', 'suggestion', 'rejected'].includes(fieldState);
    });

    if (allReviewed) {
      tab.classList.add('status--done');
    } else {
      tab.classList.remove('status--done');
    }
  }
}

summaryTab.addEventListener('click', function() {
  toggleReviewControls(false);
  reviewContent.classList.toggle("tab-pane--100");
});

// Event listener for clicking the other tabs
otherTabs.forEach(function(tab) {
  tab.addEventListener('click', function() {
    toggleReviewControls(true);
    reviewContent.classList.remove("tab-pane--100");
  });
});

/**
 * Function to toggle the review controls visibility
 */
function toggleReviewControls(show) {
  const reviewControls = document.querySelector('.review__controls');
  if (reviewControls) {
    reviewControls.style.display = show ? '' : 'none';
  }
}

peerReview(config);
