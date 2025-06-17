// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import React from 'react';

/**
 * Returns name from cookies
 * @param {string} name Key to look up in cookie
 * @returns {value} Cookie value
 */
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      var cookies = document.cookie.split(';');
      for (var i = 0; i < cookies.length; i++) {
        var cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === name + '=') {
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
const CSRFToken = () => {
    const csrftoken = getCsrfToken(); // Get the CSRF token using the getCsrfToken function
    return csrftoken; // Return the token as a string
};

export default CSRFToken;
