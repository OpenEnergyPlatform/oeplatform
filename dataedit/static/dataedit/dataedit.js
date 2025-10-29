// SPDX-FileCopyrightText: 2025 Johann Wagner <https://github.com/johannwagner>  © Otto-von-Guericke-Universität Magdeburg
// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
//
// SPDX-License-Identifier: AGPL-3.0-or-later

const { data } = require("jquery");

var DataEdit = function (table, schema) {
  var state = {
    schema: schema,
    apiVersion: "v0",
  };

  function setStatusCreate(alertCls, spin, msg) {
    var e = $("#dataedit-table-create-msg");
    e.removeClass();
    e.addClass("text-" + alertCls);
    e.find(".message").text(msg);
    if (spin) {
      e.find(".spinner").removeClass("invisible");
    } else {
      e.find(".spinner").addClass("invisible");
    }
  }

  /**
   * delete table
   */
  function deleteTable() {
    $("#dataview-confirm-delete").modal("hide");
    setStatusCreate("primary", true, "deleting table...");
    var tablename = table;

    Promise.all([
      window.reverseUrl("api:api_table", { schema: "data", table: tablename }),
      window.reverseUrl("dataedit:topic-list"),
    ]).then(([urlTable, urlTopics]) => {
      sendJson("DELETE", urlTable)
        .then(function () {
          setStatusCreate("success", true, "ok, reloading page...");
          /* redirect to topic page*/
          window.location = urlTopics;
        })
        .catch(function (err) {
          setStatusCreate("danger", false, getErrorMsg(err));
        });
    });
  }

  // bind buttons
  /* delete table */
  $("#dataview-table-delete").bind("click", function () {
    $("#dataview-confirm-delete").modal("show");
  });
  $("#dataview-confirm-delete-cancel").bind("click", function () {
    $("#dataview-confirm-delete").modal("hide");
  });
  $("#dataview-confirm-delete-delete").bind("click", deleteTable);

  /** *************************************
   * Helper functions to use the API
   ***************************************/

  function getErrorMsg(x) {
    try {
      x = "Upload failed: " + JSON.parse(x.responseJSON).reason;
    } catch (e) {
      x = x.statusText;
    }
    return x;
  }

  function getCsrfToken() {
    var token1 = getCookie("csrftoken");
    return token1;
  }

  function sendJson(method, url, data, success, error) {
    var token = getCsrfToken();
    return $.ajax({
      url: url,
      headers: { "X-CSRFToken": token },
      data_type: "json",
      cache: false,
      contentType: "application/json; charset=utf-8",
      processData: false,
      data: data,
      type: method,
      converters: {
        "text json": function (data) {
          return data;
        },
      },
      success: success,
      error: error,
    });
  }
};
