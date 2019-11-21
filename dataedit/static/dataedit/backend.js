function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function fail_handler(jqXHR, exception) {
    var msg = '';
    if (jqXHR.status === 0) {
        msg = 'Not connected.\n Verify Network.';
    } else if (jqXHR.status == 404) {
        msg = 'Requested page not found. [404]';
    } else if (jqXHR.status == 500) {
        msg = 'Internal Server Error [500].';
    } else if (exception === 'parsererror') {
        msg = 'Requested JSON parse failed.';
    } else if (exception === 'timeout') {
        msg = 'Time out error.';
    } else if (exception === 'abort') {
        msg = 'Ajax request aborted.';
    } else {
        msg = 'Uncaught Error.\n' + jqXHR.responseText;
    }
    console.log(msg);
}

function request_data(data, callback, settings) {

    $("#loading-indicator").show();

    var base_query = {
        "from": {
            "type": "table",
            "schema": schema,
            "table": table
        }
    };
    var count_query = JSON.parse(JSON.stringify(base_query));
    count_query["fields"] = [{
        type: "function",
        function: "count",
        operands: ["*"]
    }];
    var select_query = JSON.parse(JSON.stringify(base_query));
    select_query["order_by"] = data.order.map(function (c) {
        return {
            type: "column",
            column: table_info.columns[c.column],
            ordering: c.dir
        }
    });
    select_query.offset = data.start;
    select_query.limit = data.length;
    var draw = Number(data.draw);
    $.when(
        $.ajax({
            type: 'POST',
            url: '/api/v0/advanced/search',
            dataType: 'json',
            data: {
                csrfmiddlewaretoken: csrftoken,
                query: JSON.stringify(count_query)
            }
        }), $.ajax({
            type: 'POST',
            url: '/api/v0/advanced/search',
            dataType: 'json',
            data: {
                csrfmiddlewaretoken: csrftoken,
                query: JSON.stringify(select_query)
            }
        })
    ).done(function (count_response, select_response) {
        $("#loading-indicator").hide();
        callback({
            data: select_response[0].data,
            draw: draw,
            recordsFiltered: count_response[0].data[0][0],
            recordsTotal: table_info.rows
        });
    }).fail(fail_handler);
}

var table_info = {
    columns: [],
    rows: null,
    name: null,
    schema: null
};

load_table = function (schema, table, csrftoken) {

    table_info.name = table;
    table_info.schema = schema;
    var count_query = {
        from: {
            type: "table",
            schema: schema,
            table: table
        },
        fields: [{
            type: "function",
            function: "count",
            operands: ["*"]
        }]
    };
    $.when(
        $.ajax({
            url: '/api/v0/schema/' + schema + '/tables/' + table + '/columns',
        }), $.ajax({
            type: 'POST',
            url: '/api/v0/advanced/search',
            dataType: 'json',
            data: {
                csrfmiddlewaretoken: csrftoken,
                query: JSON.stringify(count_query)
            }
        })
    ).done(function (column_response, count_response) {
        Object.getOwnPropertyNames(column_response[0]).forEach(function (colname) {
            var str = '<th>' + colname + '</th>';
            $(str).appendTo('#datatable' + '>thead>tr');
            table_info.columns.push(colname);
            return {data: colname, name: colname};
        });
        table_info.rows = count_response[0].data[0][0];
        $('#datatable').DataTable({
            ajax: request_data,
            serverSide: true,
            scrollY: true,
            scrollX: true,
            searching: false
        });
    }).fail(fail_handler)
};
