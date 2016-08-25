function request_dump(schema, table, revision){

        var dfd = new $.Deferred();
        var div = $('#revision_request')[0]
        var request = $.ajax({url:table+"/"+revision+'/request',  type: "GET"});
        div.innerHTML=('Your request is pending... <div class="sk-circle">'
              + '<div class="sk-circle1 sk-child"></div>'
              + '<div class="sk-circle2 sk-child"></div>'
              + '<div class="sk-circle3 sk-child"></div>'
              + '<div class="sk-circle4 sk-child"></div>'
              + '<div class="sk-circle5 sk-child"></div>'
              + '<div class="sk-circle6 sk-child"></div>'
              + '<div class="sk-circle7 sk-child"></div>'
              + '<div class="sk-circle8 sk-child"></div>'
              + '<div class="sk-circle9 sk-child"></div>'
              + '<div class="sk-circle10 sk-child"></div>'
              + '<div class="sk-circle11 sk-child"></div>'
              + '<div class="sk-circle12 sk-child"></div>'
              + '</div>')
        request.done(function(results) {
            if (results.error) {
                dfd.reject(results.error);
            }
            else
                div.innerHTML= '<a class="btn btn-success" href="'+table+'/'+revision+'/download">Download</a>';
        });
        request.fail(function( jqXHR, textStatus ) {
            alert( "Request failed: " + textStatus );
        });

        return dfd.promise()
}