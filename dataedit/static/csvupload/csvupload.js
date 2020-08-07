var CSVUpload = function(config) {

    var state = {
        encoding: 'utf-8',
        separator: ',',
        header: true,
        columns: [],
        file: null,
        text: '',
        table: [],
        data: [],
        nParsingErrors: 0,
        nPreview: 10,
        success: null,
    }

    var GENERIC_COL_PREFIX = 'column_';

    function updateEncoding() {
        if (state.file) {
            var reader = new FileReader();
            reader.readAsText(state.file, state.encoding);
            reader.onload = function(event) {
                state.text = event.target.result;
                updateSeparator();
            }
        } else {
            state.text = '';
            updateSeparator();
        }
    }

    function updateSeparator() {
        if (state.text) {
            state.table = $.csv.toArrays(state.text, {
                "separator": state.separator
            });
        } else {
            state.table = []
        }
        updateHeader();
    }

    function updateColumnParser() {
        for (var i = 0; i < state.columns.length; i++) {
            var $th = $($('#csvupload-columns th')[i]);
            var name = $th.find('input').val();
            var parseName = $th.find('select').val();
            var parse = parser[parseName] || parseStr
            state.columns[i].name = name;
            state.columns[i].parse = parse;
        }
        updateColumns();
    }

    function updateHeader() {
        state.columns = [];
        $('#csvupload-columns').empty();
        var nRows = state.table.length;
        var nCols = 0;
        if (nRows) {
            nCols = state.table[0].length;
            for (var i = 0; i < nCols; i++) {
                var name = state.header ? state.table[0][i] : GENERIC_COL_PREFIX + (i + 1)
                state.columns.push({
                    'name': name,
                    'parse': parseStr
                });
                var $inpName = $('<div><input type="text" value="' + name + '"/></div>');
                var $inpParse = $('<div><select class="form-control form-control-sm"><option value="parseStr"></option><option value="parseFloat2">Zahl (englisch)</option><option value="parseFloatGerman">Zahl (deutsch)</option></select></div>');
                $inpParse.bind('change', function() {
                    updateColumnParser();
                });
                $inpName.bind('change', function() {
                    updateColumnParser();
                });
                var $th = $('<th></th>');
                var $div = $('<div class="form-group"></div>');
                $div.append($inpName).append($inpParse);
                $th.append($div);
                $('#csvupload-columns').append($th);
            }
        }
        updatePreview();
        updateColumns();
    }

    function parseStr(v) {
        return v;
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

    var parser = {
        parseFloat2: parseFloat2,
        parseFloatGerman: parseFloatGerman
    }

    function updateColumns() {
        var nRows = state.table.length;
        var nCols = state.columns.length;
        state.data = []
        state.nParsingErrors = 0;
        for (var i = state.header ? 1 : 0; i < nRows; i++) {
            var rowOut = {};
            var rowIn = state.table[i];
            for (var j = 0; j < nCols; j++) {
                var col = state.columns[j];
                var v = rowIn[j];
                if (!v) {
                    v = null;
                } else {
                    try {
                        v = col.parse(v);
                    } catch (err) {
                        state.nParsingErrors += 1;
                        v = null
                    }
                }
                rowOut[col.name] = v;
            }
            state.data.push(rowOut);
        }

        $('#csvupload-submit').prop("disabled", state.data.length > 0 ? false : true);

        updatePreview2();
    }

    function updatePreview2() {
        var html = '';
        var nCols = state.columns.length;
        for (var i = 0; i < state.data.length && i < state.nPreview; i++) {
            html += '<tr>'
            var row = state.data[i];
            for (var j = 0; j < nCols; j++) {
                var f = state.columns[j].name;
                var v = row[f];
                if (v == null) {
                    v = "";
                }
                html += '<td>' + v + '</td>';
            }
            html += '</tr>'
        }
        $('#csvupload-preview2').html(html);

        if (state.nParsingErrors > 0) {
            var msg = 'Warnung: Anzahl Zellen, mit ungültigen Textwert: ' + state.nParsingErrors
            setMessage(msg, 'warning');
        } else {
            setMessage();
        }



    }

    function updatePreview() {
        var n = state.nPreview + (state.header ? 1 : 0);
        var text = state.text.split("\n").slice(0, n).join('\n');
        var html = '<pre>' + text + '</pre>'
        $('#csvupload-preview').html(html);
    }

    function isAPIAvailable() {
        // Check for the various File API support.
        return (window.File && window.FileReader && window.FileList && window.Blob);
    }

    function reset() {
        $('#csvupload-file').val("");
        state.file = null;
        updateEncoding()
    }

    function post() {
        setMessage('<span class="spinner-border" role="status"></span> Upload ...', 'primary')

        $.ajax({
            url: config.postURL,
            headers: {
                'X-CSRFToken': config.csrftoken
            },
            dataType: 'json',
            cache: false,
            contentType: "application/json; charset=utf-8",
            processData: false,
            data: JSON.stringify({ 'query': state.data }),
            type: 'post',
            success: function(responseJson) {
                setMessage('Upload erfolgreich', 'success');
                state.success = true;
            },
            error: function(xhr, ajaxOptions, thrownError) {
                state.success = false;
                var message;
                try {
                    message = JSON.parse(xhr.responseText);
                    message = message.detail || message.reason
                } catch (err) {
                    message = xhr.statusText || thrownError;
                }
                setMessage('Upload Fehler: ' + message, 'danger');
            }
        });
    }

    function setMessage(msg, status) {
        $('#csvupload-alert').removeClass();
        $('#csvupload-alert').html(msg || '');
        if (msg) {
            $('#csvupload-alert').addClass('alert alert-' + status).html(msg);
        }
    }

    function init() {

        if (isAPIAvailable()) {
            $('#csvupload-file').val("").bind('change', function(evt) {
                state.file = $(evt.target)[0].files[0];
                updateEncoding()
            });

            $("#csvupload-encoding").val(state.encoding).bind('change', function(evt) {
                state.encoding = $(evt.target).find(":selected").val();
                updateEncoding()
            });

            $("#csvupload-separator").val(state.separator).bind('change', function(evt) {
                state.separator = $(evt.target).find(":selected").val();
                updateSeparator()
            });

            $("#csvupload-header").prop("checked", state.header).bind('change', function(evt) {
                state.header = $(evt.target).prop("checked")
                updateHeader()
            });

            $("#csvupload-submit").bind('click', function(evt) {
                post();
            });

            $("#csvupload-show").bind('click', function(evt) {
                reset();
                $('#csvupload-form').modal('show');
            });

            $("#csvupload-close").bind('click', function(evt) {
                $('#csvupload-form').modal('hide');
                if (state.success) {
                    location.reload();
                }

            });

        } else {
            $('#csvupload-show').prop('title', 'Funktion in diesem Browser nicht verfügbar').prop("disabled", true);
        }


    }

    init();

    return {
        reset: reset,
        state: state
    }

};