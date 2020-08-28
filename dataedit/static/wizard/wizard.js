var Wizard = function(config) {

    var state = {
        /* constants */
        schema: 'model_draft',
        apiVersion: 'v0',
        previewSizeRecords: 10,
        exampleRows: 5,
        csvColumnPrefix: "Column_",
        uploadChunkSize: 5,
        newline: "\n", // we will remove \r manually if needed
        skipEmptyLines: "greedy", // https://www.papaparse.com/docs#csv-to-json

        /* django */
        canAdd: config.canAdd,
        columns: config.columns,
        table: config.table,
        nRows: config.nRows,

        /* upload */
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
    }

    /* available column parser */
    var columnParsers = {
        "parseFloat2": { parse: parseFloat2, label: "Number (Englisch)" },
        "parseFloatGerman": { parse: parseFloatGerman, label: "Number (German)" },
        "": { parse: function(x) { return x; }, label: "" }
    }

    /* get element from dom with wizard-prefix*/
    function getDomItem(name) {
        var elem = $("#wizard-container").find('#wizard-' + name);
        if (!elem.length) throw "Element not found: #wizard-" + name
        return elem
    }

    /* add a new column (create or load table)*/
    function addColumn(columnDef) {
        columnDef = columnDef || {};
        var columns = getDomItem('columns');
        var n = columns.find('.wizard-column').length;
        var column = getDomItem('column-template').clone().attr('id', 'wizard-column-' + n).appendTo(columns).removeClass('invisible')
        column.find('.wizard-column-name').val(columnDef.name);
        column.find('.wizard-column-type').val(columnDef.data_type);
        column.find('.wizard-column-nullable').prop("checked", columnDef.is_nullable);
        column.find('.wizard-column-pk').prop("checked", columnDef.is_pk);
        column.find('.wizard-column-drop').bind('click', function(evnt) {
            evnt.currentTarget.closest('.wizard-column').remove()
        })
        column.find('.wizard-column-pk').bind('change', function(evnt) {
            // if pk: set nullable to false
            var tgt = $(evnt.currentTarget);
            if (tgt.prop('checked')) {
                tgt.closest('.wizard-column').find('.wizard-column-nullable').prop('checked', false);
            }
        });
        // add column to preview table
        getDomItem('csv-preview').find('thead tr').append('<th>' + columnDef.name + '</th>')
    }

    /* add a new column (csv preview) */
    function addColumnCsv(columnDef) {
        columnDef = columnDef || {};
        /* try to find matching names */
        var columns = getDomItem('csv-columns');
        var n = columns.find('.wizard-csv-column').length;
        var column = getDomItem('csv-column-template').clone().attr('id', 'wizard-csv-column-' + n).appendTo(columns).removeClass('invisible')
        column.find('.wizard-csv-column-name').val(columnDef.name);
        column.find('.wizard-csv-column-name-new').val(columnDef.nameDB).bind('change', updateColumnMapping);
        column.find('.wizard-csv-column-parse').val("").bind('change', updateColumnMapping);
    }

    function getColumnDefinition(colElement) {
        return {
            name: colElement.find('.wizard-column-name').val(),
            data_type: colElement.find('.wizard-column-type').val(),
            is_nullable: colElement.find('.wizard-column-nullable').prop("checked"),
            is_pk: colElement.find('.wizard-column-pk').prop("checked")
        }
    }


    function getRandom(pool, minLength, maxLength){
        var length = Math.floor(Math.random() * (maxLength - minLength)) + minLength;
        var res = "";
        for (var i=0; i<length; i++){
            var j = Math.floor(Math.random() * pool.length);
            res += pool[j];
        }
        return res
    }

    function getExampleData(data_type, i, delimiter) {
        var values = ['???']; // fallback        
        if (/.*int/.exec(data_type) || /.*serial/.exec(data_type)) {
            values = [10, 342, 0, -892, 231, 51, 2, 5]
        } else if (/real/.exec(data_type) || /double/.exec(data_type)) {
            values = [0.1, -3.1, 1.5e-2, .34, -.821678, 234.3242]
        } else if (/numeric[ ]*\(([0-9]+),[ ]*([0-9]+)\)/.exec(data_type)) {
            var prec = parseInt(/numeric[ ]*\(([0-9]+),[ ]*([0-9]+)\)/.exec(data_type)[2]);
            values = ["-23.", "273.", "29.", "-55.", "."].map(function(x){return x + getRandom("1234567890000000", prec, prec)})
        } else if (/timestamp/.exec(data_type)) {
            values = ["2020-01-01 10:38:00", "1970-10-11 12:00:00", "1981-09-07 12:30:01"]
        } else if (/time/.exec(data_type)) {
            values = ["10:38:00", "12:00:00", "12:30:01"]
        } else if (/date/.exec(data_type)) {
            values = ["2020-01-01", "1970-10-11", "1981-09-07"]
        } else if (/text/.exec(data_type)) {
            values = ["lorem", "ipsum", "blablabla", "hello world", '"quoted' + delimiter + ' text with delimiter"']
        } else if (/character[ ]*\(([0-9]+)\)/.exec(data_type)) {
            var prec = parseInt(/character[ ]*\(([0-9]+)\)/.exec(data_type)[1]);
            return getRandom("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ", prec, prec)
        } else if (/varchar[ ]*\(([0-9]+)\)/.exec(data_type)) {
            var prec = parseInt(/varchar[ ]*\(([0-9]+)\)/.exec(data_type)[1]);
            // cap
            prec = Math.min(prec, 10);
            return getRandom("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ", 0, prec) 
        } else if (/bool/.exec(data_type)) {
            values = [true, false]
        } else{
            console.error(console.log(data_type))
        }
        i = i % values.length;
        return values[i];
    }

    function updateColumnMapping() {
        var name2idx = {}
        for (var i = 0; i < state.columns.length; i++) {
            name2idx[state.columns[i].name] = i;
            state.columns[i].idxCsv = undefined;
            state.columns[i].parse = function() { return null };
        }

        // update name mapping
        getDomItem('csv-columns').find('.wizard-csv-column').each(function(idxCsv, e) {
            //var name = $(e).find('.wizard-csv-column-name').val();
            var nameDB = $(e).find('.wizard-csv-column-name-new').val();
            var parseName = $(e).find('.wizard-csv-column-parse').val();
            var parseFun = columnParsers[parseName].parse;
            var idxDB = name2idx[nameDB];
            state.csvColumns[idxCsv].nameDB = nameDB
            state.csvColumns[idxCsv].idxDB = idxDB;
            state.csvColumns[idxCsv].parse = parseFun
            if (idxDB !== undefined) {
                state.columns[idxDB].idxCsv = idxCsv;
                state.columns[idxDB].parseName = parseName;
                state.columns[idxDB].parse = (function() {
                    var _i = idxCsv;
                    var _f = parseFun;
                    var _n = parseName;
                    return function(row) {
                        var v = row[_i];
                        var v2 = null;
                        try {
                            v2 = _f(v)
                        } catch (e) {
                            // TODO parsing errors
                            console.error(e)
                        }
                        return v2;
                    };
                })();
            }
            // todo warn if name but no index
        })
        state.rowMapper = function(row) {
            return state.columns.map(function(c) {
                v = c.parse(row);
                v = v === "" ? null : v // empty string to null
                return v;
            })
        }
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
        return "/dataedit/upload/" + state.schema + "/" + tablename; // TODO: get base url from django
    }

    function getErrorMsg(xhr) {
        var msg;
        if (xhr.responseJSON && xhr.responseJSON.reason) {
            msg = xhr.responseJSON.reason
        } else {
            msg = xhr.statusText
        }
        console.error(msg)
        return msg
    }

    function sendJson(method, url, data, success, error) {
        var token = getCsrfToken()
        console.log(method, url, data, data ? JSON.parse(data) : undefined)
        return $.ajax({
            url: url,
            headers: {
                'X-CSRFToken': token
            },
            data_type: 'json', // The type of data that you're expecting back
            cache: false,
            contentType: "application/json; charset=utf-8", // type of data sent to server
            processData: false,
            data: data,
            type: method,
            converters: { 'text json': function(data) { return data } },
            success: success,
            error: error
        });
    }


    function getCookie(name) { // https://docs.djangoproject.com/en/3.1/ref/csrf/
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

    function getCsrfToken() {
        // from cookie (this is a different token)
        var token1 = getCookie('csrftoken');
        // from input {% csrf_token %}
        //var token2 = $('input[name=csrfmiddlewaretoken]').val();
        // from script {{ csrf_token }}
        //var token3 = csrftoken;
        return token1;
    }


    function parseFloat2(v) {
        /* don't actually return float, keep the string and let the database parse it */
        // v = v.replace(',', ''); // remove thousand sep            
        var v2 = parseFloat(v);
        if (isNaN(v2)) {
            throw 'Error parsing value to number: ' + v
        }
        return v2;
    }

    function parseFloatGerman(v) {
        // v = v.replace('.', ''); // remove thousand sep
        v = v.replace(',', '.');
        return parseFloat2(v);
    }


    function updatePreview() {
        var tbody = getDomItem('csv-preview').find('tbody');
        tbody.empty();
        var rows = state.previewRows.map(state.rowMapper);
        rows.map(function(row) {
            var tr = $('<tr>').appendTo(tbody);
            row.map(function(v) {
                if (v == null || v == undefined) {
                    $('<td class="wizard-td-null">').appendTo(tr);
                } else {
                    $('<td>' + v + '</td>').appendTo(tr);
                }
            });
        });

    }

    function updateFile() {
        state.file = getDomItem('file'); // [0].files[0],
        state.encoding = getDomItem('encoding').find(":selected").val();
        state.delimiter = getDomItem('delimiter').find(":selected").val();
        state.header = getDomItem('header').prop("checked");
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
            var delim = state.delimiter || ","; // in case of "auto", use default ","
            if (state.header) {
                exampleText += state.columns.map(function(c) { return c.name }).join(delim) + '\n';
            }
            for (var i = 0; i < state.exampleRows; i++) {
                exampleText += state.columns.map(function(c) { return getExampleData(c.data_type, i, delim) }).join(delim) + '\n';
            }
        }
        getDomItem('csv-example').text(exampleText);
    }

    function changeFileSettings() {
        updateFile();
        state.csvColumns = [];
        /* update example */
        updateExample()
        getDomItem('csv-columns').empty();
        if (state.file) {
            state.file.parse({
                config: {
                    encoding: state.encoding,
                    skipEmptyLines: state.skipEmptyLines,
                    preview: state.previewSizeRecords + (state.header ? 1 : 0),
                    delimiter: state.delimiter,
                    newline: state.newline,
                    complete: function(result, _file) {
                        // result = {data, errors, meta}                        
                        if (result.data.length) {
                            removeNewline(result.data)
                            var nColumns = result.data[0].length;
                            if (state.header) {
                                for (var i = 0; i < nColumns; i++) {
                                    state.csvColumns.push({
                                        'name': result.data[0][i],
                                        'nameDB': findColumnName(result.data[0][i])
                                    });
                                }
                                state.previewRows = result.data.slice(1, state.previewSizeRecords + 1);
                            } else {
                                for (var i = 0; i < nColumns; i++) {
                                    state.csvColumns.push({
                                        'name': state.csvColumnPrefix + (i + 1),
                                        'nameDB': state.columns.length > i ? state.columns[i].name : undefined
                                    });
                                }
                                state.previewRows = result.data;
                            }
                            // add columns                            
                            for (var i = 0; i < nColumns; i++) {
                                addColumnCsv(state.csvColumns[i]);
                            }
                        } else {
                            // TODO no data                            
                        }
                        updateColumnMapping();
                    },
                    error: function(error) {
                        // TODO error updateColumnMapping();?
                        console.error(error)
                    },
                }
            });
        } else {
            // TODO no file
        }

    }

    function parseContent(key, str) {
        var pat = new RegExp('"' + key + '":[ ]*([0-9]+)');
        var val = pat.exec(str)[1]; // first match is all, second is first group in ()
        return val
    }

    function createContext(insertValues) {
        var c = '{"connection_id": ' + state.connection_id
        if (state.cursor_id) {
            c = c + ', "cursor_id": ' + state.cursor_id
        }
        if (insertValues) {
            var query = {
                schema: state.schema,
                table: state.table,
                fields: state.columns ? state.columns.map(function(e) { return e.name }) : undefined,
                values: insertValues
            }
            c = c + ', "query": ' + JSON.stringify(query)
        }
        c = c + '}';
        return c

    }

    function removeNewline(arr) {
        // remove \r from last column
        arr.map(function(row) {
            row[row.length - 1] = row[row.length - 1].replace('\r', '')
        })
    }





    function rollback() {
        if (state.connection_id) {
            sendJson('POST', getApiAdvancedUrl("connection/rollback"), createContext())
                .then(function() {
                    return sendJson('POST', getApiAdvancedUrl("connection/close"), createContext())
                });
        }
    }

    function csvUpload() {
        updateFile();
        if (!state.file) return;
        state.csvParser = null;
        state.connection_id = null;
        state.cursor_id = null;
        state.uploadProgressBytes = 0;
        state.skippedHeader = state.header ? false : true; // only if csv has header
        state.fileSizeBytes = state.file[0].files[0].size;
        state.uploadedRows = 0;

        sendJson('POST', getApiAdvancedUrl("connection/open"))
            .then(function(res) {
                state.connection_id = parseContent("connection_id", res);
                return sendJson('POST', getApiAdvancedUrl("cursor/open"), createContext())
            })
            .then(function(res) {
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
                            state.uploadProgressBytes = data.meta.cursor;
                            removeNewline(data.data)

                            if (data.errors.length > 0) {
                                // TODO: warnings?
                            }

                            if (data.data.length > 0 && !state.skippedHeader) { // can be empty if chunk is too
                                state.skippedHeader = true;
                                data.data = data.data.slice(1); // remove first line
                            }

                            if (data.data.length > 0) { // can be empty if chunk is too                                 

                                state.csvParser = parser
                                state.csvParser.pause()



                                var insertData = data.data.map(state.rowMapper);

                                // TODO: deal with data.meta, data.errors
                                sendJson('POST', getApiAdvancedUrl("insert"), createContext(insertData)).then(function(res) {
                                    var nRows = JSON.parse(res).content.rowcount;
                                    state.uploadedRows += nRows

                                    state.csvParser.resume()
                                }).catch(rollback);
                            }

                        },
                        complete: function() {
                            // commit
                            sendJson('POST', getApiAdvancedUrl("connection/commit"), createContext())
                                .then(function() {
                                    return sendJson('POST', getApiAdvancedUrl("connection/close"), createContext())
                                });
                        },
                        error: function(error) {
                            // TODO error
                            rollback()
                            console.error(error)
                        },
                    }
                });

            });
    }


    function createTable() {
        /* post */
        var colDefs = [];
        var constraints = [];
        getDomItem('columns').find('.wizard-column').each(function(_i, e) {
            var c = getColumnDefinition($(e));
            colDefs.push(c);
            if (c.is_pk) {
                constraints.push({ "constraint_type": "PRIMARY KEY", "constraint_parameter": c.name })
            }
        });
        var tablename = getDomItem('tablename').val();
        var url = getApiTableUrl(tablename) + '/'; // needed for put
        var urlSuccess = getWizardUrl(tablename);
        var data = {
            query: {
                "columns": colDefs,
                "constraints": constraints
            }
        }
        sendJson('PUT', url, JSON.stringify(data)).then(function() {
            window.location = urlSuccess
        }).catch(function(err) {
            getErrorMsg(err);
        });


    }



    (function init() {
        /*add column parser options*/
        var cParseDiv = getDomItem('csv-column-template').find('.wizard-csv-column-parse');
        Object.keys(columnParsers).map(function(k) {
                cParseDiv.append('<option value="' + k + '">' + columnParsers[k].label + '</option>')
            })
            /* load existing columns */
        if (state.table) {
            getDomItem('tablename').val(state.table)
            for (var i = 0; i < state.columns.length; i++) {
                addColumn(state.columns[i])
            }
        }
        /*bind logic */
        getDomItem('column-add').bind('click', function() { addColumn(); })
        getDomItem('table-create').bind('click', createTable);
        getDomItem('file').val("").bind('change', changeFileSettings);
        getDomItem("encoding").bind('change', changeFileSettings);
        getDomItem("delimiter").bind('change', changeFileSettings);
        getDomItem("header").bind('change', changeFileSettings);
        getDomItem("table-upload").bind('click', csvUpload);

        changeFileSettings();
    })();

    return {
        //reset: reset,
        state: state
    }

};