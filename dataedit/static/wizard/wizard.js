var Wizard = function(config) {

    

    var state = {
        file: undefined,
        //columns: [],
        previewRows: [],


        uploadInProgress: false,
        uploadProgress: 0,
        uploadHeaderSkipped: false,
        uploadedRows: 0,
        uploadBatch: [],

        encoding: 'utf-8',
        delimiter: '',
        header: true,
        colPrexix: 'column_',

        previewSizeRecords: 10,
        batchSizeRecords: 100,

        /* user config */
        //csrfToken: config.csrfToken,
        csrfToken: getCsrfToken(),
        
        schema: config.schema,
        table: config.table,
        can_add: config.can_add,
        columns: config.columns,

        $wrapper: $('#' + config.wrapperId),
        $dialog: $('#' + config.wrapperId + ' #wizard-dialog'),
        $file: $('#' + config.wrapperId + ' #wizard-file'),
    }

    console.log('Wizard', state)

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

    function getCsrfToken(){
        // return Cookies.get('csrftoken');
        return getCookie('csrftoken');
    }

    function getTableUrl(){
        return "/api/v0/schema/" + state.schema + "/tables/" + state.table
    }

    function getNewRowsUrl(){
        return getTableUrl() + "/rows/new"
    }


    function getColumns() {
        return new Promise(function(resolve, reject){
            $.ajax({
                url: getTableUrl(),
                headers: {
                    'X-CSRFToken': state.csrfToken
                },
                cache: false,
                processData: false,
                type: 'get',
                async: true,
                success: function(res){
                    // sort by ordinal_position
                    var names =  Object.keys(res.columns);
                    var columns = [];
                    for (var i=0; i<names.length; i++){
                        var col = res.columns[names[i]];
                        col.name = names[i];
                        columns[i] = col;
                        /*
                        character_maximum_length: null​​
                        character_octet_length: null
                        column_default: "nextval('model_draft.table1_id_seq'::regclass)"
                        data_type: "bigint"
                        datetime_precision: null
                        dtd_identifier: "1"
                        interval_precision: null
                        interval_type: null
                        is_nullable: false
                        is_updatable: true
                        maximum_cardinality: null
                        name: "id"
                        numeric_precision: 64
                        numeric_precision_radix: 2
                        numeric_scale: 0
                        ordinal_position: 1
                        */
                    }
                    console.log(columns)
                    resolve(columns)
                },
                error: function(res){
                    reject('Could not load column info.')
                }
            });
        });
    }
    
  


    function init(){        
        console.log('Wizard init');        
        state.$wrapper.removeClass('d-none'); // show        
        state.$wrapper.find('#wizard-btn-show').bind('click', function(evt) {
            console.log('start');
        });        
    }    


    //hasWritePermission().then(getColumns).then(init).catch(function(x){console.error(x)});

    function setUploadState() {
        var disabled = !(state.file && state.columns && !state.uploadInProgress);
        state.$dialog.find('#wizard-submit').prop("disabled", disabled);
    }

    function disableInputs() {
        state.$dialog.find('.modal-body :input').prop("disabled", true);
    }

    function enableInputs() {
        state.$dialog.find('.modal-body :input').prop("disabled", false);
    }

    function __init() {
        state.$dialog.find('#wizard-file').val("").bind('change', function(evt) {
            state.file = $(evt.target)[0].files[0];
            update()
        });

        state.$dialog.find("#wizard-encoding").val(state.encoding).bind('change', function(evt) {
            state.encoding = $(evt.target).find(":selected").val();
            update()
        });

        state.$dialog.find("#wizard-separator").val(state.separator).bind('change', function(evt) {
            state.delimiter = $(evt.target).find(":selected").val();
            update()
        });

        state.$dialog.find("#wizard-header").prop("checked", state.header).bind('change', function(evt) {
            state.header = $(evt.target).prop("checked")
            update()
        });

        state.$dialog.find("#wizard-submit").bind('click', function(_evt) {
            upload();
            console.log('done')
        });

        state.$dialog.find("#wizard-show").bind('click', function(_evt) {
            reset();
            state.$dialog.modal('show');
        });

        state.$dialog.find("#wizard-close").bind('click', function(_evt) {
            state.$dialog.modal('hide');
            if (state.uploadProgress == 100) {
                location.reload();
            }
        });
    }


    function update() {
        if (state.file) {
            state.columns = [];
            state.previewRows = [];
            state.$file.parse({
                config: {
                    encoding: state.encoding,
                    skipEmptyLines: true,
                    preview: state.previewSizeRecords + (state.header ? 1 : 0),
                    delimiter: state.delimiter,
                    complete: function(results, file) {
                        if (results.data.length) {
                            var nColumns = results.data[0].length;
                            if (state.header) {
                                for (var i = 0; i < nColumns; i++) {
                                    state.columns.push({ 'name': results.data[0][i] });
                                }
                                state.previewRows = results.data.slice(1, state.previewSizeRecords + 1);
                            } else {
                                for (var i = 0; i < nColumns; i++) {
                                    state.columns.push({ 'name': state.colPrexix + (i + 1) });
                                }
                                state.previewRows = results.data;
                            }
                            updatePreviewTable()
                        } else { // no data
                            setMessage('no data', 'error')
                            reset()
                        }
                    },
                    error: function(error) {
                        setMessage(error, 'error')
                        reset()
                    },
                }
            });
        } else {
            // no file
            reset()
        }
    }


    function updateColumnMapping() {
        var $cols = state.$dialog.find('#wizard-preview-table tbody tr')
        for (var i = 0; i < state.columns.length; i++) {
            var $r = $($cols[i]);
            var mapper = $r.find('.colum-mapper').val();
            var parseName = $r.find('.colum-parser').val();
            state.columns[i].nameNew = mapper;
            state.columns[i].parse = parser[parseName];
        }

        // TODO: report status

        setUploadState();
    }

    function updatePreviewTable() {
        var $thead = $('<thead>');
        var $tbody = $('<tbody>');

        var $r;
        var $c;

        // header
        if (state.columns.length) {
            $r = $('<tr></tr>');
            $r.append('<th>column name input</th>')
            $r.append('<th>column name table</th>')
            $r.append('<th>column conversion</th>')
            $r.append('<th colspan="' + state.previewRows.length + '">data preview</th>')
            $thead.append($r);
        }

        // body
        // columns (each in one row)
        for (i = 0; i < state.columns.length; i++) {
            $r = $('<tr></tr>');
            $r.append('<td>' + state.columns[i].name + '</td>')

            var $inpName = $('<input class="colum-mapper" type="text" value="' + name + '"/>');
            var $inpParse = $('<select class="colum-parser form-control form-control-sm"><option value="parseStr"></option><option value="parseFloat2">Number (Englisch)</option><option value="parseFloatGerman">Number (German)</option></select>');
            $inpName.bind('change', function() {
                updateColumnMapping()
            });
            $inpParse.bind('change', function() {
                updateColumnMapping()
            });

            $c = $('<td>');
            $c.append($inpName)
            $r.append($c)

            $c = $('<td>');
            $c.append($inpParse)
            $r.append($c)

            for (j = 0; j < state.previewRows.length; j++) {
                $r.append('<td>' + state.previewRows[j][i] + '</td>')
            }
            $tbody.append($r);
        }

        state.$dialog.find('#wizard-preview-table').empty().append($thead, $tbody);
        updateColumnMapping();


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
        parseFloatGerman: parseFloatGerman,
        parseStr: parseStr,
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

        $('#wizard-submit').prop("disabled", state.data.length > 0 ? false : true);

        updatePreview2();
    }



    function resetFile() {
        state.file = undefined
        state.columns = []
        state.previewRows = []
        state.$file.val("");
        updatePreviewTable();
    }

    function resetUpload() {
        state.uploadedRows = 0
        state.uploadInProgress = false
        state.uploadHeaderSkipped = false
        state.uploadProgress = 0
        $('#wizard-progress .progress-bar').css('width', state.uploadProgress + '%');
        state.uploadBatch = []
        enableInputs();
    }

    function reset() {
        resetFile()
        resetUpload()
        setMessage();
    }


    function setMessage(msg, status) {
        if (status == 'info') status = 'success';
        if (status == 'warning') status = 'warning';
        if (status == 'error') status = 'danger';
        $('#wizard-alert').removeClass();
        $('#wizard-alert').html(msg || '');
        if (msg) {
            $('#wizard-alert').addClass('alert alert-' + status).html(msg);
        }
    }

    function uploadBatch() {
        console.log('upload')
        var res = $.ajax({
            url: state.postURL,
            headers: {
                'X-CSRFToken': state.csrfToken
            },
            dataType: 'json',
            cache: false,
            contentType: "application/json; charset=utf-8",
            processData: false,
            data: JSON.stringify({ 'query': state.uploadBatch }),
            type: 'post',
            async: false, // important!
            success: function(_responseJson) {
                console.log('success')
                    // TODO
                console.log(_responseJson);
                // progress bar

                $('#wizard-progress .progress-bar').css('width', state.uploadProgress + '%');

            },
            error: function(xhr, _ajaxOptions, thrownError) {
                console.log('error')
                var message;
                try {
                    message = JSON.parse(xhr.responseText);
                    message = message.detail || message.reason
                } catch (err) {
                    message = xhr.statusText || thrownError;
                }
                // TODO
                console.error(message)
                $('#wizard-progress .progress-bar').css('width', state.uploadProgress + '%');
            }
        });


        state.uploadBatch = [];
    }

    function parseRecord(r) {
        if (r.length == 1 && r[0] === "") { // empty
            return undefined;
        } else if (r.length != state.columns.length) {
            // TODO warning: different columns
        }
        var r2 = {};
        for (var i = 0; i < state.columns.length; i++) {
            var col = state.columns[i];
            if (col.nameNew) {
                var v;
                v = r[i];
                if (v !== undefined) {
                    v = col.parse(v);
                    r2[col.nameNew] = v
                }
            }
        }
        return r2
    }

    function upload() {
        resetUpload()
        state.uploadInProgress = true;

        // TODO: begin transaction

        new Promise((resolve, reject) => {
            state.$file.parse({
                config: {
                    delimiter: state.delimiter,
                    encoding: state.encoding,
                    newline: state.newline,
                    skipEmptyLines: true,
                    header: false, // we do it manually
                    step: function(results, _parser) {
                        if (results.errors.length > 0 || results.data.length === 0) {
                            // TODO
                        } else {
                            var record = results.data;
                            if (state.header && !state.uploadHeaderSkipped) {
                                state.uploadHeaderSkipped = true
                            } else {
                                record = parseRecord(record);
                                if (record) {
                                    state.uploadBatch.push(record);
                                    if (state.uploadBatch.length >= state.batchSizeRecords) {
                                        state.uploadProgress = results.meta.cursor * 100 / state.file.size;
                                        console.log('before upload')
                                        uploadBatch()
                                        console.log('after upload')
                                    }
                                }
                            }
                        }

                    },
                    complete: function(_results, _file) {
                        if (state.uploadBatch.length >= 0) {
                            state.uploadProgress = 100;
                            uploadBatch()
                        }
                        state.uploadInProgress = false;

                        // TODO: commit transaction
                        resolve('OK')
                    },
                    error: function(error, _file) {
                        // TODO: rollback transaction
                        //resetUpload()
                        reject(error)
                    },
                }
            });
        });
        console.log('ready')

    }




    //init();
    //reset();

    return {
        //reset: reset,
        state: state
    }

};