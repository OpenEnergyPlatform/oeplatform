var DataEdit = function(table, schema) {

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
        $('#dataview-confirm-delete').modal('hide');
        setStatusCreate("primary", true, "deleting table...");
        var tablename = table;
        var url = getApiTableUrl(tablename) + "/";
        var urlSuccess = '/dataedit/schemas';
        sendJson("DELETE", url).then(function() {
            setStatusCreate("success", true, "ok, reloading page...");
            window.location = urlSuccess;
        }).catch(function(err) {
            setStatusCreate("danger", false, getErrorMsg(err));
        });
    }

    // bind buttons
    /* delete table */
    $("#dataview-table-delete").bind("click", function() {
        $('#dataview-confirm-delete').modal('show');
    });
    $("#dataview-confirm-delete-cancel").bind("click", function() {
        $('#dataview-confirm-delete').modal('hide');
    });
    $("#dataview-confirm-delete-delete").bind("click", deleteTable);


     /***************************************
     * Helper functions to use the API
     ***************************************/
    function getApiTableUrl(tablename) {
        return "/api/" + state.apiVersion + "/schema/" + state.schema + "/tables/" + tablename;
    }

    function getErrorMsg(x) {
        try {
          x = 'Upload failed: ' + JSON.parse(x.responseJSON).reason;
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
          headers: {"X-CSRFToken": token},
          data_type: "json",
          cache: false,
          contentType: "application/json; charset=utf-8",
          processData: false,
          data: data,
          type: method,
          converters: {
            "text json": function(data) {
              return data;
            },
          },
          success: success,
          error: error,
        });
    }
    

}

