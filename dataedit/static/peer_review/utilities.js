// SPDX-FileCopyrightText: 2025 Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later
import {getCsrfToken, selectedState} from "./peer_review.js";

export function updateFieldColor() {
  // Color ok/suggestion/rejected
  let field_id = `field_${selectedField}`;
  let safe_selector = `#${CSS.escape(field_id)}`;
  $(safe_selector).removeClass('field-ok');
  $(safe_selector).removeClass('field-suggestion');
  $(safe_selector).removeClass('field-rejected');
  $(safe_selector).addClass(`field-${selectedState}`);
}

export function getCookie(name) {
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


export function sendJson(method, url, data, success, error) {
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

export function isEmptyValue(value) {
    return value === "" || value === "None" || value === "[]";
}