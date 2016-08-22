var OEP = {};

// backwards compatability for use in Recline
var recline = recline || {};
recline.Backend = recline.Backend || {};
recline.Backend.OEP = OEP;


function grid_formatter(value, field, row){
    if(value==null)
        return "";
    if(field.id=='_comment')
    {
        var el = document.createElement('div');
        el.innerHTML = ('<div id="modal' + row['id'] + '" class="modal fade" role="dialog">'
              + '<div class="modal-dialog">'
                + '<div class="modal-content">'
                  + '<div class="modal-header">'
                    + '<button type="button" class="close" data-dismiss="modal">&times;</button>'
                    + '<h4 class="modal-title">Comment</h4>'
                  + '</div>'
                  + '<div class="modal-body">'
                    + '<p> Method: '+ row.method +'</p>'
                    + '<p> Origin: '+ row.origin +'</p>'
                    + '<p> Assumption: '+ row.assumption +'</p>'
                  + '</div>'
                  + '<div class="modal-footer">'
                    + '<button type="button" class="btn btn-default" data-dismiss="modal">Close</button>'
                  + '</div>'
                + '</div>'

              + '</div>'
            + '</div>)');
        document.body.appendChild(el);
        return '<a data-toggle="modal" data-target="#modal' + row['id'] + '"><span class="glyphicon glyphicon-info-sign"></span></a>';
    }
    if(field.id=='ref_id')
    {
        var ret = '<a href="/literature/entry/' + value + '">' + value + '</a>';
        return ret
    }
    return value;
}

function construct_field(el){
    var field = new recline.Model.Field({
        id: el.name,
        format: grid_formatter,
        type: el.type,
      });
      field.renderer = grid_formatter;
      return field;
}

function get_field_query(field){
    column_query = {
        type: 'column',
        column: field.id
    };

    if(field.attributes.type.startsWith('geometry')){
        column_query = {
            type: 'function',
            function: 'ST_AsGeoJSON',
            operands: [column_query],
            as:field.id
        };
    }
    return column_query;
}

table_fields = [];
pk_fields = [];
(function($, my) {
    my.__type__ = 'OEP-Backend'; // e.g. elasticsearch
    my.max_rows = 1000;
    // Initial load of dataset including initial set of records
    my.fetch = function(dataset){
        var query = {table: dataset.table, schema: dataset.schema}
        var request = $.when($.ajax({url:"/api/get_columns/", data: {'query':JSON.stringify(query)}, dataType:'json', type: "POST"}),
                             $.ajax({type: 'POST', url:'/api/get_pk_constraint', dataType:'json', data: {query: JSON.stringify(query)}}));
        var dfd = new $.Deferred();
        request.done(function(results, pks) {
            if (results.error) {
                dfd.reject(results.error);
            }
            pks = pks[0];
            results = results[0];
            table_fields = results.content.map(construct_field);
            pk_fields = pks.content.constrained_columns;
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
        console.log(queryObj.from + " - " + queryObj.size)
        var query = {};
        var table_query = {
                    type:'table',
                    schema: dataset.schema,
                    table: dataset.table
        };
        var field_query = table_fields.map(get_field_query);
        var id = null;

        if(pk_fields){
            id = pk_fields[0]
        }

        if(dataset.has_row_comments){
            query.from = [{
                type: 'join',
                left: table_query,
                right:{
                    type:'table',
                    schema: dataset.schema,
                    table: "_" + dataset.table +"_cor"
                },
                join_type: 'left join',
                on: {
                    type: 'operator_binary',
                    left: {
                        type: 'column',
                        column: '_comment'
                    },
                    operator: '=',
                    right: {
                        type: 'column',
                        column: '_id'
                    }
                }
            }];
        }
        else
        {
            query.from = [table_query];
        }


        if(query.limit > my.max_rows){
            query.limit = my.max_rows
            alert("You can fetch at most " + my.max_rows + " rows in a single request. Your request will be truncated!")
        }



        if(queryObj.fields){
            query.fields = fields.map(function (el){
                        return {
                                type: 'column',
                                column: el
                        }
                ;})
        }
        else{
            query.fields = field_query;
        }

        var count_query= $.extend(true, {}, query);
        count_query.fields = [{
            type:'function',
            function:'count',
            operands: [{type:'star'}]
            }]


        query.limit = queryObj.size;
        query.offset = queryObj.from;

        if (id != null)
            query.order_by = [{
                type:'column',
                column: id}];

        var request = $.when(
            $.ajax({type: 'POST', url:'/api/search', dataType:'json', data: {query: JSON.stringify(query)}}),
            $.ajax({type: 'POST', url:'/api/search', dataType:'json', data: {query: JSON.stringify(count_query)}})
        )
        var dfd = new $.Deferred();
        request.done(function(results, counts) {
            results = results[0];
            counts = counts[0];
            if (results.error) {
                dfd.reject(results.error);
            }

            else
            {
                response = {
                    hits: results.content.data.map(function(raw_row){
                        var row = {};
                        for(i=0; i<raw_row.length; ++i)
                        {
                            var key = results.content.description[i][0];
                            row[key] = raw_row[i];
                        }
                        return row;
                    }),
                    total: counts.content.data[0][0],
                }
                dfd.resolve(response);
            }
        });

        request.fail(function( jqXHR, textStatus ) {
            alert( "Request failed: " + textStatus );
        });

        return dfd.promise()
    };
    // Save changes to the backend
    // save: function(changes, dataset)
}(jQuery, OEP));


