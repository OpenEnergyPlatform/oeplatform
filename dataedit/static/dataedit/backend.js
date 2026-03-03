/* eslint-disable max-len */
/*
SPDX-FileCopyrightText: 2025 Pierre Francois <https://github.com/Bachibouzouk> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Kirann Bhavaraju <https://github.com/KirannBhavaraju> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-License-Identifier: AGPL-3.0-or-later
*/
/* eslint-enable max-len */

"use strict";

const MAX_ROWCOUNT_ORDER_BY = 100000;
/* table with more than that: disable filter and sort */

var map;
var tile_layer;
var wkx = require("wkx");
var buffer = require("buffer");
var filters = [];
var table_container;
var query_builder;
var where;
var view;

var type_maps = {
  "double precision": "double",
};

var valid_types = [
  "string",
  "integer",
  "double",
  "date",
  "time",
  "datetime",
  "boolean",
];

var table_info = {
  columns: [],
  columnTypes: {},
  rows: null,
  name: null,
};

function getCookie(name) {
  var cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    var cookies = document.cookie.split(";");
    for (var i = 0; i < cookies.length; i++) {
      var cookie = jQuery.trim(cookies[i]);
      // Does this cookie string begin with the name we want?
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

/**
 *
 * @param {str} colType
 * @returns {boolean}
 */
function columnTypeIsGeometry(colType) {
  var colTypeLower = colType.toLowerCase();
  if (colTypeLower.includes("geo")) {
    return true;
  }
  return false;
}

/**
 *
 * @param {str} colType
 * @returns {boolean}
 */
function columnTypeIsJson(colType) {
  var colTypeLower = colType.toLowerCase();
  if (colTypeLower.includes("json")) {
    return true;
  }
  return false;
}

/**
 *
 * @param {str} colType
 * @returns {boolean}
 */
function columnTypeIsSortable(colType) {
  if (columnTypeIsJson(colType) || columnTypeIsGeometry(colType)) {
    return false; /* cannot sort json/jsonb */
  }
  return true;
}

/**
 *
 * @param {*} query
 * @param {string} label
 * @returns {object}
 */
function queryCastToText(query, label) {
  var result = {
    type: "label",
    element: {
      type: "cast",
      source: query,
      as: "text",
    },
  };
  if (label) {
    result.label = label;
  }
  return result;
}

function fail_handler(jqXHR, exception) {
  var responseJson;
  try {
    // to parse response as json
    responseJson = JSON.parse(jqXHR.responseText);
  } catch (error) {
    responseJson = {};
  }

  var msg = "";
  if (jqXHR.status === 0) {
    msg = "Not connected.\n Verify Network.";
  } else if (jqXHR.status == 404) {
    msg = "Requested page not found. [404]";
  } else if (jqXHR.status == 500) {
    msg = "Internal Server Error [500].";
  } else if (exception === "parsererror") {
    msg = "Requested JSON parse failed.";
  } else if (exception === "timeout") {
    msg = "Time out error.";
  } else if (exception === "abort") {
    msg = "Ajax request aborted.";
  } else if (responseJson && responseJson.reason) {
    msg = responseJson.reason;
  } else {
    msg = "Uncaught Error.\n" + jqXHR.responseText;
  }
  $("#loading-indicator").hide();
  /* display message to user */
  showMessage(msg, "warning");
}

/**
 *
 * @param {string} textData
 * @returns {array}
 */
function customParseJSON(textData) {
  /* or should be use something like 1e9999 for infinity ? */
  textData = textData
    .replace(/\bNaN\b/g, "null")
    .replace(/-Infinity\b/g, "null") /*-Infinity before Infinity */
    .replace(/\bInfinity\b/g, "null");
  const jsonData = JSON.parse(textData);
  return jsonData;
}

/**
 * this function is called by the table widget to update displayed data,
 * like filtering, sorting, pagination, ...
 * @param {object} data
 * @param {function} callback
 * @param {object} settings
 */
function request_data(data, callback, settings) {
  $("#loading-indicator").show();
  var base_query = {
    from: {
      type: "table",
      table: table,
    },
  };
  var count_query = JSON.parse(JSON.stringify(base_query));
  count_query["fields"] = [
    {
      type: "function",
      function: "count",
      operands: ["*"],
    },
  ];
  count_query.where = where;
  var select_query = JSON.parse(JSON.stringify(base_query));

  select_query["order_by"] = data.order
    .map(function (c) {
      /* some types cannot be sorted by */
      const colName = table_info.columns[c.column];
      const colType = table_info.columnTypes[colName];

      if (!columnTypeIsSortable(colType)) {
        const castCol = queryCastToText(
          {
            type: "column",
            column: colName,
          },
          (colName.ordering = c.dir)
        );

        return castCol;
        /*
        showMessage(`Cannot order by column ${colName}(${colType})`, "warning");
        return undefined;
        */
      }

      return {
        type: "column",
        column: colName,
        ordering: c.dir,
      };
    })
    .filter((item) => item !== undefined);

  select_query["fields"] = [];
  for (var i in table_info.columns) {
    var colName = table_info.columns[i];
    const colType = table_info.columnTypes[colName];

    var query = {
      type: "column",
      column: colName,
    };

    if (columnTypeIsJson(colType)) {
      query = queryCastToText(query, colName);
    } else if (columnTypeIsGeometry(colType)) {
      query = {
        type: "label",
        label: colName,
        element: {
          type: "function",
          function: "ST_Transform",
          operands: [query, 4326],
        },
      };
    }

    select_query["fields"].push(query);
  }
  select_query.offset = data.start;
  select_query.limit = data.length;
  if (where !== null) {
    select_query.where = where;
  }

  const tableTooLarge = table_info.rows > MAX_ROWCOUNT_ORDER_BY;

  if (tableTooLarge) {
    showMessage(
      "Sorting and filtering in preview is disabled for very large tables",
      "warning"
    );
    select_query.where = undefined;
    select_query.order_by = undefined;
  }

  var draw = Number(data.draw);
  window.reverseUrl("api:advanced-search").then((urlSearch) => {
    $.when(
      tableTooLarge
        ? undefined
        : $.ajax({
            type: "POST",
            url: urlSearch,
            dataType: "json",
            data: {
              csrfmiddlewaretoken: csrftoken,
              query: JSON.stringify(count_query),
            },
          }),
      $.ajax({
        type: "POST",
        url: urlSearch,
        dataType: "text" /* use custom json parser for Infinity, NaN */,
        data: {
          csrfmiddlewaretoken: csrftoken,
          query: JSON.stringify(select_query),
        },
      })
    )
      .done(function (count_response, select_response) {
        $("#loading-indicator").hide();

        /* fix missing data (on successful query)
      NOTE: select_response is triple (data, status, response)
      */
        select_response[0] = customParseJSON(select_response[0]);

        select_response[0].data = select_response[0].data || [];

        if (view.type === "map" && map !== undefined) {
          build_map(select_response[0].data, select_response[0].description);
        } else if (view.type === "graph") {
          build_graph(select_response[0].data);
        }

        const recordsFiltered = tableTooLarge
          ? table_info.rows /* total row count */
          : count_response[0]
              .data[0][0]; /* correct row count of filtered data */

        callback({
          data: select_response[0].data,
          draw: draw,
          recordsFiltered: recordsFiltered,
          recordsTotal: table_info.rows,
        });
      })
      .fail(fail_handler);
  });
}

function build_map(data, description) {
  map.eachLayer(function (layer) {
    if (layer !== tile_layer) {
      map.removeLayer(layer);
    }
  });
  var geo_columns = get_selected_geo_columns();
  var maptype = get_maptype();

  var col_idxs = description.reduce(function (l, r, i) {
    if (geo_columns.includes(r[0])) {
      l.push(i);
    }
    return l;
  }, []);

  var geomItems = [];

  if (maptype == "geom") {
    var colIdxGeom = col_idxs[0]; /* only one */
    for (var row_id in data) {
      var row = data[row_id];
      var geo = row[colIdxGeom];
      if (geo !== null) {
        var buf = new buffer.Buffer(geo, "hex");
        var wkb = wkx.Geometry.parse(buf);
        var gj = L.geoJSON(wkb.toGeoJSON());
        gj.on("click", flash_handler(row_id));
        geomItems.push(gj);
      }
    }
  } else if (maptype == "latlon") {
    var colIdxLat = col_idxs[0];
    var colIdxLon = col_idxs[1];
    for (var row_id in data) {
      var row = data[row_id];
      var lat = row[colIdxLat];
      var lon = row[colIdxLon];
      if (lat !== null && lon !== null) {
        var gj = L.marker([lat, lon]);
        gj.on("click", flash_handler(row_id));
        geomItems.push(gj);
      }
    }
  }

  if (geomItems.length > 0) {
    geomItems.forEach((gj) => gj.addTo(map));
    var bounds = L.featureGroup(geomItems).getBounds();
    map.fitBounds(bounds);
  }
}

function get_selected_geo_columns() {
  if (view.options.hasOwnProperty("geom")) {
    return [view.options.geom];
  } else if (
    view.options.hasOwnProperty("lat") &&
    view.options.hasOwnProperty("lon")
  ) {
    return [view.options.lat, view.options.lon];
  } else {
    showMessage("Unrecognised map type", "warning");
  }
}

function get_maptype() {
  if (view.options.hasOwnProperty("geom")) {
    return "geom";
  } else if (
    view.options.hasOwnProperty("lat") &&
    view.options.hasOwnProperty("lon")
  ) {
    return "latlon";
  } else {
    showMessage("Unrecognised map type", "warning");
  }
}

function build_graph(data) {
  // Get the div for the graph
  var plotly_div = $("#datagraph")[0];

  // Load column names to use in plot
  var x = view.options.x;
  var y = view.options.y;

  // Get ids of those columns
  var x_id = table_info.columns.indexOf(x);
  var y_id = table_info.columns.indexOf(y);

  // Extract data from query results
  var points = data.reduce(
    function (accumulator, row) {
      accumulator[0].push(row[x_id]);
      accumulator[1].push(row[y_id]);
      return accumulator;
    },
    [[], []]
  );

  // Remove possible older plots
  Plotly.purge(plotly_div);

  // Plot it
  Plotly.plot(
    plotly_div,
    [
      {
        x: points[0],
        y: points[1],
      },
    ],
    {
      margin: { t: 0 },
      xaxis: {
        title: { text: x },
      },
      yaxis: {
        title: { text: y },
      },
    }
  );
}

function flash_handler(i) {
  return function () {
    var tr = table_container.row(i).node();
    $(tr).fadeOut(50).fadeIn(50);
  };
}

/**
 *
 * @param {string} table
 * @param {string} csrftoken
 * @param {object} current_view
 */
function load_view(table, csrftoken, current_view) {
  view = current_view;
  table_info.name = table;

  Promise.all([
    window.reverseUrl("api:advanced-search"),
    window.reverseUrl("api:table-columns", { table: table }),
    window.reverseUrl("api:approx-row-count", { table: table }),
  ]).then(([urlSearch, urlColumns, urlApproxRowCount]) => {
    $.when(
      $.ajax({
        url: urlColumns,
      }),
      $.ajax({
        type: "GET",
        url: urlApproxRowCount,
        dataType: "json",
        data: {
          csrfmiddlewaretoken: csrftoken,
        },
      })
    )
      .done(function (column_response, count_response) {
        for (var colname in column_response[0]) {
          var str = "<th>" + colname + "</th>";
          $(str).appendTo("#datatable" + ">thead>tr");
          table_info.columns.push(colname);
          var dt = column_response[0][colname]["data_type"];
          table_info.columnTypes[colname] = dt;
          var mapped_dt;
          if (dt in type_maps) {
            mapped_dt = type_maps[dt];
          } else {
            if (valid_types.includes(dt)) {
              mapped_dt = dt;
            } else {
              mapped_dt = "string";
            }
          }
          filters.push({ id: colname, type: mapped_dt });
        }
        if (view.type === "map") {
          map = L.map("map");
          tile_layer = L.tileLayer(
            "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            {
              attribution:
                "Kartendaten &copy; " +
                '<a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' +
                "Mitwirkende",
              useCache: true,
            }
          );
          tile_layer.addTo(map);
        }

        table_info.rows = count_response[0].data[0][0];
        table_container = $("#datatable").DataTable({
          ajax: request_data,
          serverSide: true,
          scrollY: true,
          scrollX: true,
          searching: false,
          search: {},
        });
        query_builder = $("#builder").queryBuilder({
          filters: filters,
        });
        $("#btn-set").on("click", apply_filters);
        $("#btn-download-view").on("click", parse_download);
      })
      .fail(fail_handler);
  });
}

function parse_download() {
  var base_query = {
    fields: [],
    from: {
      type: "table",
      table: table,
    },
  };
  var rules = $("#builder").queryBuilder("getRules");
  if (rules == null) {
    window.alert("Please check for invalid Rules");
    return;
  }
  base_query.where = parse_filter(rules);
  window.reverseUrl("api:advanced-search").then((urlSearch) => {
    $.ajax({
      type: "POST",
      url: urlSearch,
      dataType: "json",
      data: {
        csrfmiddlewaretoken: csrftoken,
        query: JSON.stringify(base_query),
      },
    }).done((response) => {
      var regex = new RegExp(/\[|\]/, "gmi");
      var temp = [];
      var head = [];
      response.content.description.forEach((col_id) => {
        head.push(col_id[0]);
      });
      temp.push(JSON.stringify(head).replace(regex, ""));
      temp.push("\n");
      response.data.forEach((element) => {
        temp.push(JSON.stringify(element).replace(regex, ""));
        temp.push("\n");
      });
      var responseBlob = new Blob(temp);
      var tempElement = document.createElement("a");
      tempElement.href = window.URL.createObjectURL(responseBlob);
      tempElement.download = "Partial_" + table + ".csv";
      tempElement.click();
      tempElement.remove();
    });
  });
}

function apply_filters() {
  var rules = $("#builder").queryBuilder("getRules");
  if (rules !== null) {
    where = parse_filter(rules);
    table_container.ajax.reload();
  }
}

function parse_filter(f) {
  return {
    type: "operator",
    operator: f.condition.toLowerCase(),
    operands: f.rules.map(parse_rule),
  };
}

function negate(q) {
  return {
    type: "operator",
    operator: "not",
    operands: [q],
  };
}

function parse_rule(r) {
  switch (r.operator) {
    case "equal":
      return {
        type: "operator",
        operator: "=",
        operands: [{ type: "column", column: r.field }, r.value],
      };
    case "not_equal":
      return negate({
        type: "operator",
        operator: "=",
        operands: [{ type: "column", column: r.field }, r.value],
      });
    case "in":
      return {
        type: "operator",
        operator: "in",
        operands: [{ type: "column", column: r.field }, r.value],
      };
    case "not_in":
      return negate({
        type: "operator",
        operator: "in",
        operands: [{ type: "column", column: r.field }, r.value],
      });
    case "less":
      return {
        type: "operator",
        operator: "<",
        operands: [{ type: "column", column: r.field }, r.value],
      };
    case "less_or_equal":
      return {
        type: "operator",
        operator: "<=",
        operands: [{ type: "column", column: r.field }, r.value],
      };
    case "greater":
      return {
        type: "operator",
        operator: ">",
        operands: [{ type: "column", column: r.field }, r.value],
      };
    case "greater_or_equal":
      return {
        type: "operator",
        operator: ">=",
        operands: [{ type: "column", column: r.field }, r.value],
      };
    case "between":
      return {
        type: "operator",
        operator: "and",
        operands: [
          {
            type: "operator",
            operator: "<",
            operands: [r.value[0], { type: "column", column: r.field }],
          },
          {
            type: "operator",
            operator: "<",
            operands: [{ type: "column", column: r.field }, r.value[1]],
          },
        ],
      };
    case "not_between":
      return negate({
        type: "operator",
        operator: "and",
        operands: [
          {
            type: "operator",
            operator: "<",
            operands: [r.value[0], { type: "column", column: r.field }],
          },
          {
            type: "operator",
            operator: "<",
            operands: [{ type: "column", column: r.field }, r.value[1]],
          },
        ],
      });
    case "begins_with":
      return {
        type: "operator",
        operator: "like",
        operands: [{ type: "column", column: r.field }, r.value + "%"],
      };
    case "not_begins_with":
      return negate({
        type: "operator",
        operator: "like",
        operands: [{ type: "column", column: r.field }, r.value + "%"],
      });
    case "contains":
      return {
        type: "operator",
        operator: "like",
        operands: [{ type: "column", column: r.field }, "%" + r.value + "%"],
      };
    case "not_contains":
      return negate({
        type: "operator",
        operator: "like",
        operands: [{ type: "column", column: r.field }, "%" + r.value + "%"],
      });
    case "ends_with":
      return {
        type: "operator",
        operator: "like",
        operands: [{ type: "column", column: r.field }, "%" + r.value],
      };
    case "not_ends_with":
      return negate({
        type: "operator",
        operator: "like",
        operands: [{ type: "column", column: r.field }, "%" + r.value],
      });
    case "is_empty":
      return {
        type: "operator",
        operator: "=",
        operands: [{ type: "column", column: r.field }, ""],
      };
    case "is_not_empty":
      return negate({
        type: "operator",
        operator: "=",
        operands: [{ type: "column", column: r.field }, ""],
      });
    case "is_null":
      return {
        type: "operator",
        operator: "is",
        operands: [{ type: "column", column: r.field }, null],
      };
    case "is_not_null":
      return negate({
        type: "operator",
        operator: "IS",
        operands: [{ type: "column", column: r.field }, null],
      });
  }
}

/**
 * create a message div in the django message container
 * @param {string} message
 * @param {string} level
 */
function showMessage(message, level) {
  level = level || "info";
  console.log(level, ":", message); /* also keep message in console */
  const container = document.getElementById("uiMessages");
  const div = document.createElement("div");
  div.innerHTML = `
    <div class="alert alert-${level} alert-dismissible fade show" role="alert">
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    <div>
  `;
  container.appendChild(div);
}
