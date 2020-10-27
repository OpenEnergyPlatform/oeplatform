"use strict";

var map;
var tile_layer;
var wkx = require('wkx');
var buffer = require('buffer');
var filters = [];
var table_container;
var query_builder;
var where;
var view;

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

var table_info = {
    columns: [],
    rows: null,
    name: null,
    schema: null,
};

var geo_datatypes = [
    "point", "polygon", "polygonwithhole", "collection", "linestring"
];

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
    count_query.where = where;
    var select_query = JSON.parse(JSON.stringify(base_query));
    select_query["order_by"] = data.order.map(function (c) {
        return {
            type: "column",
            column: table_info.columns[c.column],
            ordering: c.dir
        }
    });
    select_query["fields"] = [];
    for(var i in table_info.columns){
        var col = table_info.columns[i];
        var query = {
            type: "column",
            column: col
        };
        if(col == "geom"){
            query = {
                type: "label",
                label: "geom",
                element :{
                    type: "function",
                    function: "ST_Transform",
                    operands: [
                        query,
                        4326
                    ]
                }
            }
        }
        select_query["fields"].push(query);
    }
    select_query.offset = data.start;
    select_query.limit = data.length;
    if(where !== null){
        select_query.where = where;
    }
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
        if(map !== undefined) {
            build_map(select_response[0].data, select_response[0].description)
        }

        if(view.type === "map") {
            build_map(select_response[0].data, select_response[0].description);
        } else if(view.type === "graph") {
            build_graph(select_response[0].data);
        }
        callback({
            data: select_response[0].data,
            draw: draw,
            recordsFiltered: count_response[0].data[0][0],
            recordsTotal: table_info.rows
        });
    }).fail(fail_handler);
}

function build_map(data, description){
    map.eachLayer(function (layer) {
        if(layer !== tile_layer){map.removeLayer(layer)}
    });
    var geo_columns = get_selected_geo_columns();
    var col_idxs = description.reduce(function (l, r, i) {
        if (geo_columns.includes(r[0])) {
            l.push(i);
        }
        return l;
    }, []);
    var bounds = [];
    for (var row_id in data) {
        var row = data[row_id];
        var geo_values = col_idxs.map(function (i) {
            if(row[i] !== null) {
                var buf = new buffer.Buffer(row[i], "hex");
                var wkb = wkx.Geometry.parse(buf);
                var gj = L.geoJSON(wkb.toGeoJSON());
                gj.on("click", flash_handler(row_id));
                gj.addTo(map);
                return gj;
            }
        });
        bounds.push(L.featureGroup(geo_values.filter(x => !!x)));
    }
    var b = L.featureGroup(bounds).getBounds();
    map.fitBounds(b);
}

function get_selected_geo_columns(){
    if(view.options.hasOwnProperty("geom")){
        return [view.options.geom];
    } else if (view.options.hasOwnProperty("lat") && view.options.hasOwnProperty("lon")){
        return [view.options.lat, view.options.lon];
    }
    else {
        console.log("Unrecognised map type")
    }
}

function build_graph(data){
    // Get the div for the graph
    var plotly_div = $("#datagraph")[0];

    // Load column names to use in plot
    var x = view.options.x;
    var y = view.options.y;

    // Get ids of those columns
    var x_id = table_info.columns.indexOf(x);
    var y_id = table_info.columns.indexOf(y);

    // Extract data from query results
    var points = data.reduce(function(accumulator, row){
        accumulator[0].push(row[x_id]);
        accumulator[1].push(row[y_id]);
        return accumulator}, [[],[]]);

    // Remove possible older plots
    Plotly.purge(plotly_div);

    // Plot it
    Plotly.plot(
        plotly_div,
        [{
          x: points[0],
          y: points[1]
        }],
        {
          margin: {t: 0},
          xaxis: {
            title: {text: x}
          },
          yaxis: {
            title: {text: y}
          }
        }
    );
}

function flash_handler(i){
    return function (){
        var tr = table_container.row(i).node();
        $(tr).fadeOut(50).fadeIn(50);
    };
}


function load_graph(schema, table, csrftoken){

}


function load_view(schema, table, csrftoken, current_view) {
    view = current_view;
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
        }),
        $.ajax({
            type: 'POST',
            url: '/api/v0/advanced/search',
            dataType: 'json',
            data: {
                csrfmiddlewaretoken: csrftoken,
                query: JSON.stringify(count_query)
            }
        }),
        $.ajax({ // get metadata for column description / units
            url: '/api/v0/schema/' + schema + '/tables/' + table + '/meta'
        })
    ).done(function (column_response, count_response, meta) {
        var columnDescription = {}; // name -> description
        meta[0]['resources'][0]['schema']['fields'].map(function(fld){
            columnDescription[fld.name] = fld.description || "";
            if (fld.unit) {
                if (columnDescription[fld.name]) {
                    columnDescription[fld.name] += '<hr>'
                }
                columnDescription[fld.name] += 'Unit: ' + fld.unit
            }
        });
        for (var colname in column_response[0]){
            // add description popover
            var popover = columnDescription[colname];
            if (popover) {
                popover = 'title="' + colname + '" data-content="' + popover + '" data-toggle="popover" data-html="true"';
            }
            var str = '<th ' + popover + '>' + colname + '</th>';
            $(str).appendTo('#datatable' + '>thead>tr')
            .popover({ trigger: "hover", placement: "left"}); // activate popover
            table_info.columns.push(colname);
            var dt = column_response[0][colname]["data_type"];
            var mapped_dt;
            if(dt in type_maps) {
                mapped_dt = type_maps[dt];
            } else {
                if(valid_types.includes(dt)) {
                    mapped_dt = dt;
                } else {
                    mapped_dt = "string";
                }
            }
            filters.push({id: colname, type: mapped_dt});
        }
        if(view.type === "map"){
            map = L.map('map');
            tile_layer = L.tileLayer(
                'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    'attribution':  'Kartendaten &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> Mitwirkende',
                    'useCache': true
                }
            );
            tile_layer.addTo(map);
        }

        table_info.rows = count_response[0].data[0][0];
        table_container = $('#datatable').DataTable({
            ajax: request_data,
            serverSide: true,
            scrollY: true,
            scrollX: true,
            searching: false,
            search: {}
        });
        query_builder = $('#builder').queryBuilder({
            filters: filters
        });
        $('#btn-set').on('click', apply_filters);

    }).fail(fail_handler)
}

function apply_filters(){
    var rules = $('#builder').queryBuilder('getRules');
    if(rules !== null) {
        where = parse_filter(rules);
        table_container.ajax.reload();
    }
}

function parse_filter(f){
    return {
        type: "operator",
        operator: f.condition.toLowerCase(),
        operands: f.rules.map(parse_rule)
    }
}

function negate(q){
    return {
        type: "operator",
        operator: "not",
        operands: [q]
    }
}

function parse_rule(r){
    switch(r.operator) {
        case "equal":
            return {
                type: "operator",
                operator: "=",
                operands: [{type:"column", column: r.field}, r.value]
            };
        case "not_equal":
            return negate({
                type: "operator",
                operator: "=",
                operands: [{type:"column", column: r.field}, r.value]
            });
        case "in":
            return {
                type: "operator",
                operator: "in",
                operands: [{type:"column", column: r.field}, r.value]
            };
        case "not_in":
            return negate({
                type: "operator",
                operator: "in",
                operands: [{type:"column", column: r.field}, r.value]
            });
        case "less":
            return {
                type: "operator",
                operator: "<",
                operands: [{type:"column", column: r.field}, r.value]
            };
        case "less_or_equal":
            return {
                type: "operator",
                operator: "<=",
                operands: [{type:"column", column: r.field}, r.value]
            };
        case "greater":
            return {
                type: "operator",
                operator: ">",
                operands: [{type:"column", column: r.field}, r.value]
            };
        case "greater_or_equal":
            return {
                type: "operator",
                operator: ">=",
                operands: [{type:"column", column: r.field}, r.value]
            };
        case "between":
            return {
                type: "operator",
                operator: "and",
                operands:
                    [
                        {
                            type: "operator",
                            operator: "<",
                            operands: [r.value[0], {type:"column", column: r.field}]
                        }, {
                            type: "operator",
                            operator: "<",
                            operands: [{type:"column", column: r.field}, r.value[1]]
                    }]
            };
        case "not_between":
            return negate({
                type: "operator",
                operator: "and",
                operands:
                    [
                        {
                            type: "operator",
                            operator: "<",
                            operands: [r.value[0], {type:"column", column: r.field}]
                        }, {
                            type: "operator",
                            operator: "<",
                            operands: [{type:"column", column: r.field}, r.value[1]]
                    }]
            });
        case "begins_with":
            return {
                type: "operator",
                operator: "like",
                operands: [{type:"column", column: r.field}, r.value+"%"]
            };
        case "not_begins_with":
            return negate({
                type: "operator",
                operator: "like",
                operands: [{type:"column", column: r.field}, r.value+"%"]
            });
        case "contains":
            return {
                type: "operator",
                operator: "in",
                operands: [{type:"column", column: r.field}, r.value]
            };
        case "not_contains":
            return negate({
                type: "operator",
                operator: "in",
                operands: [{type:"column", column: r.field}, r.value]
            });
        case "ends_with":
            return {
                type: "operator",
                operator: "like",
                operands: [{type:"column", column: r.field}, "%"+r.value]
            };
        case "not_ends_with":
            return negate({
                type: "operator",
                operator: "like",
                operands: [{type:"column", column: r.field}, "%"+r.value]
            });
        case "is_empty":
            return {
                type: "operator",
                operator: "=",
                operands: [{type:"column", column: r.field}, '']
            };
        case "is_not_empty":
            return negate({
                type: "operator",
                operator: "=",
                operands: [{type:"column", column: r.field}, '']
            });
        case "is_null":
            return {
                type: "operator",
                operator: "is",
                operands: [{type:"column", column: r.field}, null]
            };
        case "is_not_null":
            return negate({
                type: "operator",
                operator: "IS",
                operands: [{type:"column", column: r.field}, null]
            });
    }
}

var type_maps = {
    "double precision": "double",
};

var valid_types = ["string", "integer", "double", "date", "time", "datetime", "boolean"];
