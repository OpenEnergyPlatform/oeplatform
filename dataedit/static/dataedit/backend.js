var OEP = {};

// backwards compatability for use in Recline
var recline = recline || {};
recline.Backend = recline.Backend || {};
recline.Backend.OEP = OEP;


/*

string (text): a string
number (double, float, numeric): a number including floating point numbers.
integer (int): an integer.
date: a date. The preferred format is YYYY-MM-DD.
time: a time without a date
date-time (datetime, timestamp): a date-time. It is recommended this be in ISO 8601 format of YYYY-MM- DDThh:mm:ssZ in UTC time.
boolean (bool)
binary: base64 representation of binary data.
geo_point: as per http://www.elasticsearch.org/guide/reference/mapping/geo-point-type.html. That is a field (in these examples named location) that has one of the following structures:
geojson: as per http://geojson.org/
array: an array
object (json): an object
any: value of field may be any type
*/

var typemap = {
    BIGINT: 'integer',
    BINARY: 'binary',
    BLOB: 'binary',
    BOOLEAN: 'boolean',
    BigInteger: 'integer',
    Boolean: 'boolean',
    CHAR: 'boolean',
    CLOB: 'binary',
    Concatenable: 'any',
    DATE: 'date',
    DATETIME: 'date-time',
    DECIMAL: 'number',
    Date: 'date',
    DateTime: 'date-time',
    Enum: 'any',
    FLOAT: 'number',
    Float: 'number',
    INT: 'integer',
    INTEGER: 'integer',
    Integer: 'integer',
    Interval: 'any',
    LargeBinary: 'binary',
    MatchType: 'any',
    NCHAR: 'string',
    NVARCHAR: 'string',
    Numeric: 'number',
    PickleType: 'any',
    REAL: 'number',
    SMALLINT: 'integer',
    SchemaType: 'any',
    SmallInteger: 'integer',
    String: 'string',
    TEXT: 'string',
    TIME: 'time',
    TIMESTAMP: 'date-time',
    Text: 'string',
    Time: 'time',
    TypeDecorator: 'any',
    TypeEnginBases: 'any',
    TypeEngine: 'any',
    Unicode: 'string',
    VARBINARY: 'binary',
    VARCHAR: 'string',
}


function show_comment(e, schema, table, id){
        e.stopPropagation();
        query = {
            from:{
                type:'table',
                table:'_'+table+'_cor',
                schema:schema},
            where:[condition_query('_id',id)]
        }
        var request = $.ajax({type: 'POST', url:'/api/v0/advanced/search', dataType:'json', data: {query: JSON.stringify(query)}});
        var dfd = new $.Deferred();

         request.done(function(results) {
                if (results.error) {
                    dfd.reject(results.error);
                }

                results = results.content.data.map(function(raw_row){
                    var row = {};
                    for(i=0; i<raw_row.length; ++i)
                    {
                        var key = results.content.description[i][0];
                        row[key] = raw_row[i];
                    }
                    return row;
                });
                if(results == undefined || results.length == 0){
                    alert("Comment not found");
                    dfd.reject("Comment not found");
                }
                else{
                    var value = results[0];
                    var $modal = bs_jQuery("#comment_modal");
                    bs_jQuery('#modal_method').text(value.method);
                    bs_jQuery('#modal_origin').text(value.origin);
                    bs_jQuery('#modal_assumption').text(value.assumption);
                    $modal.modal();

                    dfd.resolve({});
                }
        });

    return function(e){
        console.log(e.target);

    }
}

function translate_filter(obj){
    if(obj.type == "term"){
        return condition_query(obj.field, obj.term)
    }
    if(obj.type == "range"){
        return {
            type:'operator_binary',
            left: {
                type: 'column',
                column: obj.field,
            },
            right:{
                type:'operator_binary',
                left: {
                    type: 'value',
                    value: obj.from,
                },
                right: {
                    type: 'value',
                    value: obj.to
                },
                operator: 'AND'
            },
            operator: 'between'
        };
    }
}

function construct_comment_handler(schema, table){
    if(!schema.startsWith('_')){
        schema = '_' + schema
    }


    var grid_formatter = function (value, field, row){
        if(value==null)
            return "";
        if(field.id=='_comment')
        {
            if(value == null)
                return '';

            return '<a class="glyphicon glyphicon-info-sign" onclick="show_comment(event, &quot;' + schema +'&quot;, &quot;' + table + '&quot;, '+ value + ');"></a>';
        }
        if(field.id=='ref_id')
        {
            var ret = '<a href="/literature/entry/' + value + '">' + value + '</a>';
            return ret
        }
        return value;
    }

    return grid_formatter;
}

function construct_field(dataset){
    return function(el){
        var type;
        if(el.type in typemap)
            type=typemap[el.type];
        else
            type=el.type;
        var field = new recline.Model.Field({
            id: el.name,
            format: construct_comment_handler(dataset.schema, dataset.table),
            type:type,

          });
          /*if(el.name == '_comment'){
            field.editor = buildCommentEditor(dataset.schema, dataset.table);
          }*/
          field.renderer = construct_comment_handler(dataset.schema, dataset.table);
          return field;
    }
}


(function($, my) {
    my.__type__ = 'OEP-Backend'; // e.g. elasticsearch
    my.max_rows = 1000;
    // Initial load of dataset including initial set of records
    my.fetch = function(dataset){
        var query = {table: dataset.table, schema: dataset.schema}
        var request = $.ajax({url:'/api/v0/schema/' + dataset.schema + '/tables/' + dataset.table, type: "GET"});
        var dfd = new $.Deferred();



        request.done(function(results) {
            if (results.error) {
                dfd.reject(results.error);
            }
            var table_fields = [];
            var pk_fields = [];
            for(col in results.columns){
                table_fields.push(col)
            };
            for(con in results.constraints){
                if(con.constraint_type=='PRIMARY KEY') {
                    pk_fields.push(con)
                }
            };
            dfd.resolve({
                fields: table_fields,
                useMemoryStore: false,
            });
        });
        request.fail(function( jqXHR, textStatus ) {
            alert( "Request failed: " + textStatus );
        });

        return dfd.promise()
    };

    // Query the backend for records returning them in bulk.
    // This method will be used by the Dataset.query method to search the backend
    // for records, retrieving the results in bulk.
    my.query = function(queryObj, dataset){
        var query = {table: dataset.table, schema: dataset.schema}
        var request = $.ajax({url:'/api/v0/schema/' + dataset.schema + '/tables/' + dataset.table + '/columns/', type: "GET"});
        var dfd = new $.Deferred();
        request.done(function(fields) {
            $('#loading-indicator').show()

            if (fields.error) {
                dfd.reject(fields.error);
            }
            var table_fields = [];

            for(col in fields){
                fields[col].id = col
                table_fields.push(fields[col])
            };

            var field_map = {};

            for(i=0; i<table_fields.length; ++i)
            {
                field_map[table_fields[i].id] = get_field_query(table_fields[i]);
            }

            var table_query = {
                        type:'table',
                        schema: dataset.schema,
                        table: dataset.table
            };

            if(!unchecked){
                table_query.only = true;
            }
            table_query.type = 'table';
            var field_query = [];

            if(queryObj.fields){
                field_query = queryObj.fields.map(function (el){return fieldmap[el];
                            /*return {
                                    type: 'column',
                                    column: el
                            };*/
                    });
            }
            else
            {
                field_query = table_fields.map(get_field_query)
            }

            var query = {from : table_query, fields: field_query};



            if(query.limit > my.max_rows){
                query.limit = my.max_rows
                alert("You can fetch at most " + my.max_rows + " rows in a single request. Your request will be truncated!")
            }

            console.log(queryObj)

            if(queryObj.filters && queryObj.filters.length > 0){
                query.where = queryObj.filters.map(translate_filter)
            }

            var count_query= $.extend(true, {}, query);
            count_query.fields = [{
                type:'function',
                function:'count',
                operands: [{type:'star'}]
                }]

            if(queryObj.sort){
                query.order_by = queryObj.sort.map(function(obj){
                    return {
                        type:'column',
                        column: obj.field,
                        ordering: obj.order
                    };
                });
            }

            query.limit = queryObj.size;
            query.offset = queryObj.from;

            // This must be a POST-Request for now, even thought no changes should happen.
            // Reason is, that geo-data must be transformed to geo-JSON and function calls
            // are not available via get, yet.
            var request = $.when(
                $.ajax({type: 'POST', url:'/api/v0/advanced/search', dataType:'json', data: {csrfmiddlewaretoken: csrftoken, query: JSON.stringify(query)}}),
                $.ajax({type: 'POST', url:'/api/v0/advanced/search', dataType:'json', data: {csrfmiddlewaretoken: csrftoken, query: JSON.stringify(count_query)}})
            )
            request.done(function(results, counts) {
                $('#loading-indicator').hide();
                results = results[0];
                counts = counts[0];
                if (results.error) {
                    dfd.reject(results.error);
                }

                else
                {
                    var response = {
                        hits: results.data.map(function(raw_row){
                            var row = {};
                            for(i=0; i<raw_row.length; ++i)
                            {
                                var key = results.content.description[i][0];
                                row[key] = raw_row[i];
                            }
                            return row;
                        }),
                        total: counts.data[0][0],
                    }
                    dfd.resolve(response);
                }
            });

            request.fail(function( jqXHR, textStatus ) {
                alert( "Request failed: " + textStatus );
            });

        });



        request.fail(function( jqXHR, textStatus ) {
                alert( "Request failed: " + textStatus );
        });

        return dfd.promise()
    };

    my.save = function(changes, dataset){
        var dfd = new $.Deferred();
        var request = $.when(
                changes.creates.map(
                    insert_query(
                        dataset.attributes.schema,
                        dataset.attributes.table,
                        $("#commit-message").val()
                    )
                )
            ).then(
                changes.updates.map(
                    update_query(
                        dataset.attributes.schema,
                        dataset.attributes.table,
                        $("#commit-message").val()
                    )
                )
            );

        // We do not know the number of updates. Thus we set no arguments and
        // obtain them via black magic called javascript
        request.done(function()
        {
            for (var i=0; i<arguments.length; i++)
                if(arguments[i].error)
                    dfd.reject(arguments[i].error);
            dfd.resolve({})
        });

        request.fail(function( jqXHR, textStatus ) {
            alert( "Request failed: " + textStatus );
        });
    };

    function insert_query(schema, table, message)
    {
        return function(record){
            var query = {
                schema: schema,
                table: table,
                values: record.additions
            }

            query['message'] = message

            return $.ajax({type: 'POST',
                url:'/api/v0/advanced/insert', dataType:'json',
                data: {
                    query: JSON.stringify(query)
                }
            });
        }
    };

    function update_query(schema, table, message)
    {
        return function(record){

            var conditions = [];
            for(var col in record._previousAttributes){
                conditions.push(condition_query(col,record._previousAttributes[col]));
            }
            var query = {
                schema: schema,
                table: table,
                where: conditions,
                values: record.changed
            }

            query['message'] = message

            return $.ajax({type: 'POST',
                url:'/api/v0/advanced/update', dataType:'json',
                data: {
                    query: JSON.stringify(query)
                }
            });
        }
    };


}(jQuery, OEP));


