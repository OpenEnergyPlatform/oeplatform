"use strict";

var Wizard = function(config) {
    var state = {
        schema: "model_draft",
        apiVersion: "v0",
        previewSizeRecords: 10,
        exampleRows: 5,
        csvColumnPrefix: "Column_",
        uploadChunkSize: 1024 * 1024,
        newline: "\n",
        skipEmptyLines: "greedy",
        canAdd: config.canAdd,
        columns: config.columns,
        table: config.table,
        nRows: config.nRows,
        connection_id: null,
        cursor_id: null,
        previewRows: null,
        csvParser: null,
        csvColumns: null,
        rowMapper: null,
        skippedHeader: null,
        uploadProgressBytes: null,
        fileSizeBytes: null,
        uploadedRows: null,
        fileName: null,
        cancel: null,
    };

    var columnParsers = {
        "parseFloatCommaDecimal": { parse: parseFloatCommaDecimal, label: "Number with comma as decimal" },
        "": {
            parse: function(x) {
                return x;
            },
            label: ""
        }
    };


    function getDomItem(name) {
        var elem = $("#wizard-container").find("#wizard-" + name);
        if (!elem.length) {
            console.error("Element not found: #wizard-" + name);
        }
        return elem;
    }


    function addColumn(columnDef) {
        columnDef = columnDef || {};
        var columns = getDomItem("columns");
        var n = columns.find(".wizard-column").length;
        var column = getDomItem("column-template").clone().attr("id", "wizard-column-" + n).appendTo(columns).removeClass("invisible");
        column.find(".wizard-column-name").val(columnDef.name);
        column.find(".wizard-column-type").val(columnDef.data_type);
        column.find(".wizard-column-nullable").prop("checked", columnDef.is_nullable);
        column.find(".wizard-column-pk").prop("checked", columnDef.is_pk);
        column.find(".wizard-column-drop").bind("click", function(evnt) {
            evnt.currentTarget.closest(".wizard-column").remove();
        });
        column.find(".wizard-column-pk").bind("change", function(evnt) {
            var tgt = $(evnt.currentTarget);
            if (tgt.prop("checked")) {
                tgt.closest(".wizard-column").find(".wizard-column-nullable").prop("checked", false);
            }
        });

        if (columnDef.name) {
            getDomItem("csv-preview").find("thead tr").append("<th>" + columnDef.name + "</th>");
        }

    }

    function addColumnCsv(columnDef) {
        columnDef = columnDef || {};
        var columns = getDomItem("csv-columns");
        var n = columns.find(".wizard-csv-column").length;
        var column = getDomItem("csv-column-template").clone().attr("id", "wizard-csv-column-" + n).appendTo(columns).removeClass("invisible");
        column.find(".wizard-csv-column-name").val(columnDef.name);
        column.find(".wizard-csv-column-name-new").val(columnDef.nameDB).bind("change", updateColumnMapping);
        column.find(".wizard-csv-column-parse").val("").bind("change", updateColumnMapping);
    }

    function getColumnDefinition(colElement) {
        return { name: colElement.find(".wizard-column-name").val(), data_type: colElement.find(".wizard-column-type").val(), is_nullable: colElement.find(".wizard-column-nullable").prop("checked"), is_pk: colElement.find(".wizard-column-pk").prop("checked") };
    }

    function getExampleData(data_type, i, delimiter) {
        function getRandom(pool, minLength, maxLength) {
            var length = Math.floor(Math.random() * (maxLength - minLength)) + minLength;
            var res = "";
            for (var i = 0; i < length; i++) {
                var j = Math.floor(Math.random() * pool.length);
                res += pool[j];
            }
            return res;
        }
        var values;
        if (/.*int/.exec(data_type) || /.*serial/.exec(data_type)) {
            values = [10, 342, 0, -892, 231, 51, 2, 5];
        } else if (/(real|double|float)/.exec(data_type)) {
            values = [0.1, -3.1, 1.5e-2, .34, -.821678, 234.3242];
        } else if (/numeric[ ]*\(([0-9]+),[ ]*([0-9]+)\)/.exec(data_type)) {
            var prec = parseInt(/numeric[ ]*\(([0-9]+),[ ]*([0-9]+)\)/.exec(data_type)[2]);
            values = ["-23.", "273.", "29.", "-55.", "."].map(function(x) {
                return x + getRandom("1234567890000000", prec, prec);
            });
        } else if (/timestamp/.exec(data_type)) {
            values = ["2020-01-01 10:38:00", "1970-10-11 12:00:00", "1981-09-07 12:30:01"];
        } else if (/time/.exec(data_type)) {
            values = ["10:38:00", "12:00:00", "12:30:01"];
        } else if (/date/.exec(data_type)) {
            values = ["2020-01-01", "1970-10-11", "1981-09-07"];
        } else if (/varchar[ ]*\(([0-9]+)\)/.exec(data_type)) {
            var prec = parseInt(/varchar[ ]*\(([0-9]+)\)/.exec(data_type)[1]);
            prec = Math.min(prec, 16);
            values = ["lorem", "ipsum", "dolor", "hello world"];
            values = values.map(function(t) {
                var l = Math.floor(Math.random() * prec);
                return t.slice(0, l);
            });
        } else if (/char[ ]*\(([0-9]+)\)/.exec(data_type)) {
            var prec = parseInt(/char[ ]*\(([0-9]+)\)/.exec(data_type)[1]);
            return getRandom("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ", prec, prec);
        } else if (/bool/.exec(data_type)) {
            values = [true, false];
        } else if (/text|varchar|char/.exec(data_type)) {
            values = ["Lorem ipsum dolor sit amet", "consectetur adipiscing elit", "sed do eiusmod tempor incididunt"];
        }

        if (values === undefined) {
            values = ['<no_example>'];
            console.log('no example for type: ' + data_type)
        }
        i = i % values.length;
        return values[i];
    }

    function updateColumnMapping() {
        var name2idx = {};
        for (var i = 0; i < state.columns.length; i++) {
            name2idx[state.columns[i].name] = i;
            state.columns[i].idxCsv = undefined;
            state.columns[i].parse = function() {
                return null;
            };
        }
        getDomItem("csv-columns").find(".wizard-csv-column").each(function(idxCsv, e) {
            var nameDB = $(e).find(".wizard-csv-column-name-new").val();
            var parseName = $(e).find(".wizard-csv-column-parse").val();
            var parseFun = columnParsers[parseName].parse;
            var idxDB = name2idx[nameDB];
            state.csvColumns[idxCsv].nameDB = nameDB;
            state.csvColumns[idxCsv].idxDB = idxDB;
            state.csvColumns[idxCsv].parse = parseFun;
            if (idxDB !== undefined) {
                state.columns[idxDB].idxCsv = idxCsv;
                state.columns[idxDB].parseName = parseName;
                state.columns[idxDB].parse = function() {
                    var _i = idxCsv;
                    var _f = parseFun;
                    var _n = parseName;
                    return function(row) {
                        var v = row[_i];
                        var v2 = null;
                        try {
                            v2 = _f(v);
                        } catch (e$0) {
                            console.error(e$0);
                        }
                        return v2;
                    };
                }();
            }
        });
        state.rowMapper = function(row) {
            return state.columns.map(function(c) {
                var v = c.parse(row);
                v = v === "" ? null : v;
                return v;
            });
        };
        updatePreview();
    }

    function getApiTableUrl(tablename) {
        tablename = tablename || state.table;
        return "/api/" + state.apiVersion + "/schema/" + state.schema + "/tables/" + tablename;
    }

    function getApiAdvancedUrl(path) {
        return "/api/" + state.apiVersion + "/advanced/" + path;
    }

    function getWizardUrl(tablename) {
        tablename = tablename || state.table;
        return "/dataedit/wizard/" + state.schema + "/" + tablename;
    }

    function getErrorMsg(x) {
        if (x.responseJSON && x.responseJSON.reason) {
            x = x.responseJSON.reason;
        } else {
            if (x.statusText) {
                x = x.statusText;
            }
        }
        return x;
    }

    function sendJson(method, url, data, success, error) {
        var token = getCsrfToken();
        console.log(method, url, data, data ? JSON.parse(data) : undefined);
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
                "text json": function(data) {
                    return data;
                }
            },
            success: success,
            error: error
        });
    }

    function getCookie(name) {
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

    function getCsrfToken() {
        var token1 = getCookie("csrftoken");
        return token1;
    }

    function parseFloat2(v) {
        var v2 = parseFloat(v);
        if (isNaN(v2)) {
            throw "Error parsing value to number: " + v;
        }
        return v2;
    }

    function parseFloatCommaDecimal(v) {
        v = v.replace(".", "");
        v = v.replace(",", ".");
        return parseFloat2(v);
    }

    function updatePreview() {
        var tbody = getDomItem("csv-preview").find("tbody");
        tbody.empty();
        var rows = state.previewRows.map(state.rowMapper);
        rows.map(function(row) {
            var tr = $("<tr>").appendTo(tbody);
            row.map(function(v) {
                if (v == null || v == undefined) {
                    $('<td class="wizard-td-null">').appendTo(tr);
                } else {
                    $("<td>" + v + "</td>").appendTo(tr);
                }
            });
        });
    }

    function updateFile() {
        state.file = getDomItem("file");
        state.encoding = getDomItem("encoding").find(":selected").val();
        state.delimiter = getDomItem("delimiter").find(":selected").val();
        state.header = getDomItem("header").prop("checked");
        if (state.file && state.file[0] && state.file[0].files && state.file[0].files[0]) {
            state.fileSizeBytes = state.file[0].files[0].size;
            state.fileName = state.file[0].files[0].name;
            getDomItem("file-label").text(state.fileName + " (" + state.fileSizeBytes + " bytes)");
        } else {
            state.fileSizeBytes = null;
            state.fileName = null;
            state.file = null;
            getDomItem("file-label").text("");
        }
    }

    function findColumnName(name) {
        name = name.toLowerCase();
        for (var i = 0; i < state.columns.length; i++) {
            if (state.columns[i].name.toLowerCase() == name) {
                return state.columns[i].name;
            }
        }
    }

    function updateExample() {
        var exampleText = "";
        if (state.columns) {
            var delim = state.delimiter || ",";

            if (state.header) {
                exampleText += state.columns.map(function(c) {
                    return c.name;
                }).join(delim) + "\n";
            }
            for (var i = 0; i < state.exampleRows; i++) {
                exampleText += state.columns.map(function(c) {
                    return getExampleData(c.data_type, i, delim);
                }).join(delim) + "\n";
            }
        }
        getDomItem("csv-example").text(exampleText);
    }

    function changeFileSettings() {
        updateFile();
        state.csvColumns = [];
        updateExample();
        getDomItem("csv-columns").empty();
        getDomItem("csv-text").text('');
        if (state.file) {
            state.file.parse({
                config: {
                    encoding: state.encoding,
                    skipEmptyLines: state.skipEmptyLines,
                    preview: state.previewSizeRecords + (state.header ? 1 : 0),
                    delimiter: state.delimiter,
                    newline: state.newline,
                    complete: function(result, _file) {
                        if (result.data.length) {
                            removeNewline(result.data);
                            getDomItem("csv-text").text(result.data.map(function(row) { return row.join(result.meta.delimiter) }).join('\n'));
                            var nColumns = result.data[0].length;
                            if (state.header) {
                                for (var i = 0; i < nColumns; i++) {
                                    state.csvColumns.push({ "name": result.data[0][i], "nameDB": findColumnName(result.data[0][i]) });
                                }
                                state.previewRows = result.data.slice(1, state.previewSizeRecords + 1);
                            } else {
                                for (var i = 0; i < nColumns; i++) {
                                    state.csvColumns.push({ "name": state.csvColumnPrefix + (i + 1), "nameDB": state.columns.length > i ? state.columns[i].name : undefined });
                                }
                                state.previewRows = result.data;
                            }
                            for (var i = 0; i < nColumns; i++) {
                                addColumnCsv(state.csvColumns[i]);
                            }
                        } else {}
                        updateColumnMapping();
                    },
                    error: function(error) {
                        console.error(error);
                    },
                }
            });
        } else {}
    }

    function parseContent(key, str) {
        var pat = new RegExp('"' + key + '":[ ]*([0-9]+)');
        var val = pat.exec(str)[1];
        return val;
    }

    function createContext(insertValues) {
        var c = '{"connection_id": ' + state.connection_id;
        if (state.cursor_id) {
            c = c + ', "cursor_id": ' + state.cursor_id;
        }
        if (insertValues) {
            var query = {
                schema: state.schema,
                table: state.table,
                fields: state.columns ? state.columns.map(function(e) {
                    return e.name;
                }) : undefined,
                values: insertValues
            };
            c = c + ', "query": ' + JSON.stringify(query);
        }
        c = c + "}";
        return c;
    }

    function removeNewline(arr) {
        arr.map(function(row) {
            row[row.length - 1] = row[row.length - 1].replace("\r", "");
        });
    }

    function rollback(message) {
        message = message || "upload failed";
        if (state.connection_id) {
            var ctx = createContext();
            state.connection_id = null;
            sendJson("POST", getApiAdvancedUrl("connection/rollback"), ctx).then(function() {
                return sendJson("POST", getApiAdvancedUrl("connection/close"), ctx);
            }).then(function() {
                setStatusUpload('danger', false, message)
                resetUpload()
            });
        }
    }

    function cancelUpload() {
        setStatusUpload('danger', true, "cancel upload...");
        state.cancel = true;
    }

    function csvUpload() {
        updateFile();
        if (!state.file) {
            return;
        }
        state.csvParser = null;
        state.connection_id = null;
        state.cursor_id = null;
        state.uploadProgressBytes = 0;
        state.skippedHeader = state.header ? false : true;
        state.uploadedRows = 0;
        state.cancel = false;
        getDomItem("table-upload").hide();
        getDomItem("table-upload-cancel").show();
        setStatusUpload('primary', 0, "starting upload...");
        sendJson("POST", getApiAdvancedUrl("connection/open")).then(function(res) {
            state.connection_id = parseContent("connection_id", res);
            return sendJson("POST", getApiAdvancedUrl("cursor/open"), createContext());
        }).then(function(res) {
            state.cursor_id = parseContent("cursor_id", res);
            state.file.parse({
                config: {
                    encoding: state.encoding,
                    skipEmptyLines: state.skipEmptyLines,
                    preview: state.previewSizeRecords + (state.header ? 1 : 0),
                    delimiter: state.delimiter,
                    newline: state.newline,
                    chunkSize: state.uploadChunkSize,
                    chunk: function(data, parser) {
                        if (state.cancel) {
                            rollback("cancel");
                            return;
                        }
                        state.uploadProgressBytes = data.meta.cursor;
                        removeNewline(data.data);
                        if (data.data.length > 0 && !state.skippedHeader) {
                            state.skippedHeader = true;
                            data.data = data.data.slice(1);
                        }
                        if (data.data.length > 0) {
                            state.csvParser = parser;
                            state.csvParser.pause();
                            var insertData = data.data.map(state.rowMapper);
                            console.log(insertData, data.data, data.meta)
                            sendJson("POST", getApiAdvancedUrl("insert"), createContext(insertData)).then(function(res) {
                                if (state.cancel) {
                                    rollback("cancel");
                                    return;
                                }
                                var nRows = JSON.parse(res).content.rowcount;
                                state.uploadedRows += nRows;
                                var p = state.uploadProgressBytes / state.fileSizeBytes * 100;
                                p = p || 0;
                                p = Math.round(p);
                                var status = p + "% rows: " + state.uploadedRows;
                                setStatusUpload('primary', p, status);
                                state.csvParser.resume();
                            }).catch(function(err) {
                                rollback(getErrorMsg(err));
                            });
                        }
                    },
                    complete: function() {
                        if (state.cancel) {
                            rollback("cancel");
                            return;
                        }
                        setStatusUpload('primary', 100, "finishing upload...");
                        sendJson("POST", getApiAdvancedUrl("connection/commit"), createContext()).then(function() {
                            return sendJson("POST", getApiAdvancedUrl("connection/close"), createContext());
                        }).then(function() {
                            setStatusUpload('success', false, "upload ok");
                            resetUpload();
                        });
                    },
                    error: function(error) {
                        rollback(getErrorMsg(error));
                    },
                }
            });
        }).catch(function(err) {
            console.error("catch", err);
        });
    }

    function createTable() {
        setStatusCreate("primary", true, "creating table...");

        var colDefs = [];
        var constraints = [];
        getDomItem("columns").find(".wizard-column").each(function(_i, e) {
            var c = getColumnDefinition($(e));
            colDefs.push(c);
            if (c.is_pk) {
                constraints.push({ "constraint_type": "PRIMARY KEY", "constraint_parameter": c.name });
            }
        });
        var tablename = getDomItem("tablename").val();
        var url = getApiTableUrl(tablename) + "/";
        var urlSuccess = getWizardUrl(tablename);
        var data = { query: { "columns": colDefs, "constraints": constraints } };
        sendJson("PUT", url, JSON.stringify(data)).then(function() {
            setStatusCreate("success", true, "ok, reloading page...");
            window.location = urlSuccess;
        }).catch(function(err) {
            setStatusCreate("danger", false, getErrorMsg(err));
        });
    }

    function resetUpload() {
        state.cancel = null;
        getDomItem("table-upload").show();
        getDomItem("table-upload-cancel").hide();
    }

    function showCreate() {
        getDomItem("container-upload").collapse("hide");
        getDomItem("container-create").collapse("show");
        getDomItem("container-upload").find(".btn").hide();
        getDomItem("container-upload").find("input").prop("readonly", true);
    }

    function showUpload() {
        getDomItem("container-create").collapse("hide");
        getDomItem("container-upload").collapse("show");
        getDomItem("container-create").find(".btn").hide();
        getDomItem("container-create").find("input").prop("readonly", true);
        getDomItem("container-create").find("input,select,.combobox-container").not('[type=text]').prop("disabled", true);
        if (!state.canAdd) {
            setStatusUpload('danger', false, 'You have no permission to upload to this table');
            getDomItem("container-upload").find(".btn").hide();
            getDomItem("container-upload").find("input").prop("readonly", true);
            getDomItem("container-upload").find("input,select,.combobox-container").not('[type=text]').prop("disabled", true);
        }
    }

    function setStatusCreate(alertCls, spin, msg) {
        var e = $('#wizard-table-create-msg');
        e.removeClass();
        e.addClass('alert alert-' + alertCls);
        e.find('.message').text(msg)
        if (spin) {
            e.find('.spinner').removeClass('invisible')
        } else {
            e.find('.spinner').addClass('invisible')
        }
    }

    function setStatusUpload(alertCls, progress, msg) {
        var e = $('#wizard-table-upload-msg');
        e.removeClass();
        if (!alertCls) {
            e.hide()
            return;
        } else {
            e.show()
        }
        var p = e.find('.progress');
        e.addClass('alert alert-' + alertCls);
        e.find('.message').text(msg)
        if (progress === true) {
            e.find('.spinner').show()
            p.hide();
        } else {
            e.find('.spinner').hide()
            if (progress !== false) {
                p.show();
                p.find('.progress-bar').css('width', progress + '%')
            } else {
                p.hide();
            }
        }
    }

    (function init() {
        var cParseDiv = getDomItem("csv-column-template .wizard-csv-column-parse");
        Object.keys(columnParsers).map(function(k) {
            cParseDiv.append('<option value="' + k + '">' + columnParsers[k].label + "</option>");
        });
        getDomItem("column-add").bind("click", function() {
            addColumn();
        });
        getDomItem("table-create").bind("click", createTable);
        getDomItem("file").bind("change", changeFileSettings);
        getDomItem("encoding").bind("change", changeFileSettings);
        getDomItem("delimiter").bind("change", changeFileSettings);
        getDomItem("header").bind("change", changeFileSettings);
        getDomItem("table-upload").bind("click", csvUpload);
        getDomItem("table-upload-cancel").bind("click", cancelUpload);


        changeFileSettings();
        resetUpload();

        if (state.table) {
            getDomItem("tablename").val(state.table);
            for (var i = 0; i < state.columns.length; i++) {
                addColumn(state.columns[i]);
            }

            var cN = getDomItem("csv-column-template .wizard-csv-column-name-new");
            cN.append('<option selected></option>')
            state.columns.map(function(c) {
                cN.append('<option>' + c.name + '</option>')
            })

            showUpload();
        } else {
            showCreate();
        }
    })();

    $('#wizard-loading').hide();


    return { state: state };
};