"use strict";

var map;
var tile_layer;
var wkx = require('wkx');
var buffer = require('buffer');
var filters = [];
var table_container;
var query_builder;
var where;

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
    geo_columns: []
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
        map.eachLayer(function (layer) {
           if(layer !== tile_layer){map.removeLayer(layer)}
        });
        var geo_cols = get_selected_geo_columns();
        if(geo_cols !== null){
            var col_idxs = select_response[0].description.reduce(function(l, r, i){
                if(geo_cols.includes(r[0])){l.push(i);} return l;
            }, []);
            var bounds = [];
            for(var row_id in select_response[0].data){
                var row = select_response[0].data[row_id];
                var geo_values = col_idxs.map(function(i){
                    var buf = new buffer.Buffer(row[i], "hex");
                    var wkb = wkx.Geometry.parse(buf);
                    var gj = L.geoJSON(wkb.toGeoJSON());
                    gj.on("click", flash_handler(row_id));
                    gj.addTo(map);
                    return gj;
                });
                bounds.push(L.featureGroup(geo_values));
            }
            var b = L.featureGroup(bounds).getBounds();
            console.log(b);
            map.fitBounds(b);
        }

        // Get the div for the graph
        var plotly_div = $("#datagraph")[0];

        // Load column names to use in plot
        var x = "id"; // TODO: Load column from options
        var y = "id"; // TODO: Load column from options

        // Get ids of those columns
        var x_id = table_info.columns.indexOf(x);
        var y_id = table_info.columns.indexOf(y);

        // Extract data from query results
        var points = select_response[0].data.reduce(function(accumulator, row){
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

        callback({
            data: select_response[0].data,
            draw: draw,
            recordsFiltered: count_response[0].data[0][0],
            recordsTotal: table_info.rows
        });
    }).fail(fail_handler);
}

function flash_handler(i){
    return function (){
        var tr = table_container.row(i).node();
        $(tr).fadeOut(50).fadeIn(50);
    };
}


function load_graph(schema, table, csrftoken){

}


function load_table(schema, table, csrftoken) {

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


        for (var colname in column_response[0]){
            var str = '<th>' + colname + '</th>';
            $(str).appendTo('#datatable' + '>thead>tr');
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
        if(table_info.columns.includes("lan") && table_info.columns.includes("lon")){
            table_info.geo_columns.push(["lat", "lon"]);
        }
        if(table_info.columns.includes("geom")){
            table_info.geo_columns.push(["geom"]);
        }
        if(table_info.geo_columns.length>0){
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
            searching: true,
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
                operator: "equal",
                operands: [{type:"column", column: r.field}, r.value]
            };
        case "not_begins_with":
            return {
                type: "operator",
                operator: "equal",
                operands: [{type:"column", column: r.field}, r.value]
            };
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
                operator: "equal",
                operands: [{type:"column", column: r.field}, r.value]
            };
        case "not_ends_with":
            return {
                type: "operator",
                operator: "equal",
                operands: [{type:"column", column: r.field}, r.value]
            };
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
                operator: "IS",
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
function get_selected_geo_columns(){
    /**
     * This should load a selected column from some input element. Currently we
     * just take the first one.
     */
    if(table_info.geo_columns.length === 0){
        return null;
    } else {
        return table_info.geo_columns[0]
    }
}