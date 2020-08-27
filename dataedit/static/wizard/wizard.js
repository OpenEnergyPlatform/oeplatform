var Wizard = function(config) {

    var SCHEMA = 'model_draft';
    var API_VERSION = 'v0';
    var previewSizeRecords = 10;
    var csvColumnPrefix = "Column_";

    function getDomItem(name){
        var elem = $("#wizard-container").find('#wizard-' + name);
        if (!elem.length) throw "Element not found: #wizard-" + name
        return elem
    }

    function addColumn(columnDef){
        columnDef = columnDef || {};        
        var columns = getDomItem('columns');
        var n = columns.find('.wizard-column').length;        
        var column = getDomItem('column-template').clone().attr('id', 'wizard-column-' + n).appendTo(columns).removeClass('invisible')
        column.find('.wizard-column-name').val(columnDef.name);
        column.find('.wizard-column-type').val(columnDef.data_type);
        column.find('.wizard-column-nullable').prop("checked", columnDef.is_nullable);
        column.find('.wizard-column-pk').prop("checked", columnDef.is_pk);        
        column.find('.wizard-column-drop').bind('click', function(evnt){            
            evnt.currentTarget.closest('.wizard-column').remove()
        })
        column.find('.wizard-column-pk').bind('change', function(evnt){
            // if pk: set nullable to false
            var tgt = $(evnt.currentTarget);
            if (tgt.prop('checked')){
                tgt.closest('.wizard-column').find('.wizard-column-nullable').prop('checked', false);
            }
        })
        
    }

    function addColumnCsv(columnDef){
        columnDef = columnDef || {};        
        var columns = getDomItem('csv-columns');
        var n = columns.find('.wizard-csv-column').length;        
        var column = getDomItem('csv-column-template').clone().attr('id', 'wizard-csv-column-' + n).appendTo(columns).removeClass('invisible')        
        column.find('.wizard-csv-column-name').val(columnDef.name);
        column.find('.wizard-csv-column-name-new').bind('change', validateColumnMapping);
        column.find('.wizard-csv-column-preview').val(columnDef.preview);
        column.find('.wizard-csv-column-parse').bind('change', changeColumnParser).change();
    }

    function getColumnDefinition(colElement){
        return {
            name: colElement.find('.wizard-column-name').val(),
            data_type: colElement.find('.wizard-column-type').val(),
            is_nullable: colElement.find('.wizard-column-nullable').prop("checked"),
            is_pk: colElement.find('.wizard-column-pk').prop("checked")
        }
    }

    function validateColumnMapping(){
        console.log('TODO')
    }

    function getApiTableUrl(tablename){
        return "/api/" + API_VERSION + "/schema/" + SCHEMA + "/tables/" + tablename;
    }
    function getApiAdvancedUrl(path){
        return "/api/" + API_VERSION + "/advanced/" + path;
    }    

    function getApiRowsUrl(tablename){
        return getApiTableUrl(tablename) + "/rows/new";
    }

    function getWizardUrl(tablename){
        return "/dataedit/upload/" + SCHEMA + "/" + tablename; // TODO: get base url from django
    }
    function getErrorMsg(xhr){
        if (xhr.responseJSON && xhr.responseJSON.reason){
            return xhr.responseJSON.reason
        } else {
            return xhr.statusText
        }
    }

    function sendJson(method, url, data, async, success, error) {
        console.log(url)
        return $.ajax({
            url: url,
            headers: {
                'X-CSRFToken': getCsrfToken()
            },
            dataType: 'json',
            cache: false,
            contentType: "application/json; charset=utf-8",
            processData: false,
            data: JSON.stringify(data),
            type: method,
            async: async,
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

    function getCsrfToken(){
        // return Cookies.get('csrftoken');
        return getCookie('csrftoken');
    }






    
    /* bind functions */    
    getDomItem('column-add').bind('click', function(_evnt){addColumn();})
    getDomItem('table-create').bind('click', function(_evnt){
        /* post */

        var colDefs = [];
        var constraints = [];
        var pk = undefined; // NOTE: currently only single field PK
        getDomItem('columns').find('.wizard-column').each(function(_i, e){            
            var c = getColumnDefinition($(e));
            colDefs.push(c);
            if (c.is_pk){
                constraints.push({"constraint_type": "PRIMARY KEY", "constraint_parameter": c.name})
            }
        });
        
        var tablename = getDomItem('tablename').val();        
        var url = getApiTableUrl(tablename);
        var urlSuccess = getWizardUrl(tablename);

        var data = {
            query: {
                "columns": colDefs,
                "constraints": constraints            
            }
        }
        
        sendJson('PUT', url, data, true, function(_res){
            window.location = urlSuccess
        }, function(xhr){
            // TODO
            getErrorMsg(xhr)
        });        
    });

    /* load existing columns */
    if (config.table){
        getDomItem('tablename').val(config.table)
        for (var i=0; i<config.columns.length; i++){
            addColumn(config.columns[i])
        }        
    }
    
    function changeColumnParser(evt){
        var col = $(evt.currentTarget).closest('.wizard-csv-column');
        var text = col.find('.wizard-csv-column-preview').val();
        var parse = col.find('.wizard-csv-column-parse').val();        
        col.find('.wizard-csv-column-preview-parsed').val(parse + ": " + text);

    }
 
    function changeFileSettings(){
        var fileConf = {
            file: getDomItem('file'), // [0].files[0],
            encoding: getDomItem('encoding').find(":selected").val(),
            delimiter: getDomItem('delimiter').find(":selected").val(),
            header: getDomItem('header').prop("checked")
        };
        
        /* update example */

        getDomItem('csv-example').text(JSON.stringify(config));

        getDomItem('csv-columns').empty();        
        if (fileConf.file) {
            fileConf.file.parse({
                config: {
                    encoding: fileConf.encoding,
                    skipEmptyLines: true,
                    preview: previewSizeRecords + (fileConf.header ? 1 : 0),
                    delimiter: fileConf.delimiter,
                    complete: function(result, _file) {
                        // result = {data, errors, meta}                        
                        if (result.data.length) {
                                                        
                            var columns = [];
                            var nColumns = result.data[0].length;
                            var previewRows;
                            if (fileConf.header) {
                                for (var i = 0; i < nColumns; i++) {
                                    columns.push({ 'name': result.data[0][i] });
                                }
                                previewRows = result.data.slice(1, previewSizeRecords + 1);
                            } else {
                                for (var i = 0; i < nColumns; i++) {
                                    columns.push({ 'name': csvColumnPrefix + (i + 1) });
                                }
                                previewRows = result.data;
                            }
                            for (var i = 0; i < nColumns; i++) {
                                var previewColumn = [];
                                for (var j = 0; j < previewRows.length; j++) {
                                    previewColumn.push(previewRows[j][i]);
                                }
                                columns[i].preview = previewColumn.join(' | ');
                                addColumnCsv(columns[i]);
                            }
                        } else {
                             // no data                            
                        }
                    },
                    error: function(error) {
                        // TODO error
                        console.error(error)
                    },
                }
            });
        } else {
            // TODO no file
        }        
    }


    getDomItem('file').val("").bind('change', changeFileSettings);
    getDomItem("encoding").bind('change', changeFileSettings);
    getDomItem("delimiter").bind('change', changeFileSettings);
    getDomItem("header").bind('change', changeFileSettings);
    changeFileSettings();
    
    
    var context = {
        query: {
            schema: config.schema,
            table: config.table,
            fields: config.columns.map(function(e){return e.name}),
            values: undefined
        }
    };    
    sendJson('POST', getApiAdvancedUrl("connection/open"), undefined, true)
    .then(function(res){
        console.log(res)
        context.connection_id =  res.content.connection_id;        
        return sendJson('POST', getApiAdvancedUrl("cursor/open"), context, true)        
    })
    .then(function(res){
        console.log(res)
        context.cursor_id =  res.content.cursor_id;        
        context.query.values = []
        console.log(context)
        return sendJson('POST', getApiAdvancedUrl("insert"), context, true)
    })
    .then(function(res){
        console.log(res)
        return sendJson('POST', getApiAdvancedUrl("connection/commit"), context, true)
    })
    /*.then(function(){
        return sendJson('POST', getApiAdvancedUrl("cursor/close"), context, true)
    })
    */
    .then(function(res){
        console.log(res)
        return sendJson('POST', getApiAdvancedUrl("connection/close"), context, true)
    })
    .then(function(res){console.log("THEN", res)})
    .catch(function(err){
        console.error(getErrorMsg(err));
        if (context.connection_id) {
            sendJson('POST', getApiAdvancedUrl("connection/rollback"), context, true)
            .then(function(){
                return sendJson('POST', getApiAdvancedUrl("connection/close"), context, true)
            })
        }        
    })
    
    
    


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