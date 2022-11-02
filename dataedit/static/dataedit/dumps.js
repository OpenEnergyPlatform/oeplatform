function request_dump(schema, table) {
  var dfd = new $.Deferred();
  var div = $('#revision_request_'+ schema + table)[0];
  var request = $.ajax({url: table+'/request', type: "POST"});
  div.innerHTML=('Your request is pending... <div class="sk-circle">' +
              '<div class="sk-circle1 sk-child"></div>' +
              '<div class="sk-circle2 sk-child"></div>' +
              '<div class="sk-circle3 sk-child"></div>' +
              '<div class="sk-circle4 sk-child"></div>' +
              '<div class="sk-circle5 sk-child"></div>' +
              '<div class="sk-circle6 sk-child"></div>' +
              '<div class="sk-circle7 sk-child"></div>' +
              '<div class="sk-circle8 sk-child"></div>' +
              '<div class="sk-circle9 sk-child"></div>' +
              '<div class="sk-circle10 sk-child"></div>' +
              '<div class="sk-circle11 sk-child"></div>' +
              '<div class="sk-circle12 sk-child"></div>' +
              '</div>');
  request.done(function(results) {
    if (results.error) {
      dfd.reject(results.error);
    } else {
      div.innerHTML= '<a class="btn btn-success" href="'+table+'/'+'/download">Download</a>';
    }
  });
  request.fail(function( jqXHR, textStatus ) {
    alert( "Request failed: " + textStatus );
  });

  return;
}

function request_dump_only(schema, table) {
  var csrftoken = getCookie('csrftoken');
  var div = $('#revision_request_'+ schema + table)[0];
  var button = $('#request')[0];
  button.disabled = true;
  button.class = '';
  div.innerHTML=('Your request is pending... <div class="sk-circle">' +
              '<div class="sk-circle1 sk-child"></div>' +
              '<div class="sk-circle2 sk-child"></div>' +
              '<div class="sk-circle3 sk-child"></div>' +
              '<div class="sk-circle4 sk-child"></div>' +
              '<div class="sk-circle5 sk-child"></div>' +
              '<div class="sk-circle6 sk-child"></div>' +
              '<div class="sk-circle7 sk-child"></div>' +
              '<div class="sk-circle8 sk-child"></div>' +
              '<div class="sk-circle9 sk-child"></div>' +
              '<div class="sk-circle10 sk-child"></div>' +
              '<div class="sk-circle11 sk-child"></div>' +
              '<div class="sk-circle12 sk-child"></div>' +
              '</div>');
  var dfd = new $.Deferred();
  var request = $.ajax({url: 'download', dataType: 'json', data: {csrfmiddlewaretoken: csrftoken}, type: "POST"});
  request.done(function() {
    location.reload();
  });
  request.fail(function( jqXHR, textStatus ) {
    alert( "Request failed: " + textStatus );
  });

  return dfd.promise();
}

function getCookie(name) {
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
