var OEP = {};

// backwards compatability for use in Recline
var recline = recline || {};
recline.Backend = recline.Backend || {};
recline.Backend.OEP = OEP;

(function($, my) {
    my.__type__ = 'OEP-Backend'; // e.g. elasticsearch
    my.max_rows = 1000;
    // Initial load of dataset including initial set of records
    my.fetch = function(dataset){
        var query = {table: dataset.table, schema: dataset.schema}
        var request = $.ajax({url:"/api/get_columns/", data: {'query':JSON.stringify(query)}, dataType:'json', method: "POST"});
        var dfd = new $.Deferred();
        request.done(function(results) {
            if (results.error) {
                dfd.reject(results.error);
            }

            dfd.resolve({
                fields: results.content.map(function(el){return el.name;}),
                useMemoryStore: false
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
        var query = {
            limit: queryObj.size,
            offset: queryObj.from,
            from: [{
                type:'table',
                schema: dataset.schema,
                table: dataset.table
            }],
        };
        if(query.limit > my.max_rows){
            query.limit = my.max_rows
            alert("You can fetch at most " + my.max_rows + " rows in a single request. Your request will be truncated!")
        }

        if(queryObj.fields){
            query.fields = fields.map(function (el){
                        return {
                            expression:{
                                type: 'column',
                                column: el
                            }
                        }
                ;})
        }


        var request = $.when(
            $.ajax({type: 'POST', url:'/api/search', dataType:'json', data: {query: JSON.stringify(query)}}),
            $.ajax({type: 'POST', url:'/api/count', dataType:'json', data: {query: JSON.stringify(query)}})
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
                        row = {};
                        for(i=0; i<raw_row.length; ++i)
                        {
                            row[results.content.description[i][0]] = raw_row[i];
                        }
                        return row;
                    }),
                    total: counts.content[0][0],
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


