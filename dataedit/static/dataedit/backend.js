
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

function count_query(query){
    var jqxhr = $.ajax({
        type: 'POST',
        url:'/api/v0/advanced/search',
        dataType:'json',
        data: {
            csrfmiddlewaretoken: csrftoken,
            query: JSON.stringify(query)
        }
    })
}


function request_data(data, callback, settings){

    var base_query = {
        "from": {
            "type": "table",
            "schema": schema,
            "table": table
        }
    };
    var count_query_1 = JSON.parse(JSON.stringify(base_query));
    count_query_1["fields"] = [{
        type: "function",
        function: "count",
        operands: ["*"]
    }];
    var count_query_2 = JSON.parse(JSON.stringify(count_query_1));
    var select_query  = JSON.parse(JSON.stringify(base_query));
    select_query["order_by"] = data.order.map(function(c){
           return {
               type: "column",
               column: columns_list[c.column],
               ordering: c.dir
           }
        });
    select_query.offset = data.start;
    select_query.limit = data.length;
    var draw = Number(data.draw);
    var jqxhr = $.when(
        $.ajax({
            type: 'POST',
            url:'/api/v0/advanced/search',
            dataType:'json',
            data: {
                csrfmiddlewaretoken: csrftoken,
                query: JSON.stringify(count_query_1)
            }
        }),$.ajax({
            type: 'POST',
            url:'/api/v0/advanced/search',
            dataType:'json',
            data: {
                csrfmiddlewaretoken: csrftoken,
                query: JSON.stringify(count_query_2)
            }
        }),$.ajax({
            type: 'POST',
            url:'/api/v0/advanced/search',
            dataType:'json',
            data: {
                csrfmiddlewaretoken: csrftoken,
                query: JSON.stringify(select_query)
            }
        })
            ).done(function (response1, response2, response3) {
            callback({
                data:response3[0].data,
                draw: draw,
                recordsFiltered: response2[0].data[0][0],
                recordsTotal: response1[0].data[0][0]
            });
        }).fail(fail_handler);
}
columns_list = [];
load_table = function(schema, table, csrftoken){

    var jqxhr = $.ajax({
        url: '/api/v0/schema/'+schema+'/tables/'+table+'/columns',
    }).done(function(){
        var data = JSON.parse(jqxhr.responseText);
        var columns = Object.getOwnPropertyNames(data).map(function(colname){
            var str = '<th>' + colname + '</th>';
            $(str).appendTo('#datatable'+'>thead>tr');
            columns_list.push(colname);
            return {data: colname, name: colname};
        });
        $('#datatable').DataTable({
            ajax: request_data,
            serverSide: true,
            scrollY: true,
            scrollX: true,
            searching: false,
        });
    }).fail(fail_handler)







};
