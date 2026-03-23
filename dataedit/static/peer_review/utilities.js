// SPDX-FileCopyrightText: 2025 Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

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

export function getCsrfToken() {
  return getCookie("csrftoken");
}

export function sendJson(method, url, data, success, error) {
  var token = getCsrfToken();
  return $.ajax({
    url: url,
    type: method, 
    headers: {"X-CSRFToken": token},
    dataType: "json",
    cache: false,
    contentType: "application/json; charset=utf-8",
    processData: false,
    data: data,
    success: success,
    error: error
  });
}

export function isEmptyValue(value) {
    if (value === null || value === undefined) return true;
    
    // Convert to string and trim whitespace
    const s = String(value).trim();
    
    return (
        s === '' || 
        s === 'None' || 
        s === 'null' || 
        s === '[]' || 
        s === '{}'
    );
}

export function getErrorMsg(response) {
  try {
    if (response.responseJSON && response.responseJSON.error) {
        return 'Upload failed: ' + response.responseJSON.error;
    }
    var response_msg = 'Upload failed: ' + JSON.parse(response.responseText).error;
  } catch (e) {
    console.log(response);
    var response_msg = response.responseText || "Unknown error";
  }
  return response_msg;
}