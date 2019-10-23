function buildCommentEditor(schema, table){
    function CommentEditor(args) {
        var $input;
        var defaultValue;
        var scope = this;
        var current_value = null;

        this.init = function () {
          $input = $("<INPUT type=text class='editor-text' />")
              .appendTo(args.container)
              .on("keydown.nav", function (e) {
                if (e.keyCode === $.ui.keyCode.LEFT || e.keyCode === $.ui.keyCode.RIGHT) {
                  e.stopImmediatePropagation();
                }
              })
              .focus()
              .select();
        };

        this.destroy = function () {
          $input.remove();
        };

        this.focus = function () {
          $input.focus();
        };

        this.getValue = function () {
          return $input.val()._id;
        };

        this.setValue = function (val) {
          $input.val(val._id);
        };

        this.loadValue = function (item) {
            var val = null;
            if(item[args.column.field]){
                current_value = item[args.column.field]
                val = current_value
            }
            $input.val(val);
            $input[0].defaultValue = current_value;
            $input.select();

        };

        this.serializeValue = function () {
          return $input.val()._id;
        };

        this.applyValue = function (item, state) {
            var query = {};
            query.fields = [
                {id:'_id', attributes:{type:'text'}},
                {id:'method', attributes:{type:'text'}},
                {id:'origin', attributes:{type:'text'}},
                {id:'assumption', attributes:{type:'text'}}].map(get_field_query);

            query.from = [{
                type:'table',
                schema: '_' + schema,
                table: '_' + table +'_cor'
            }];

            query.where = [condition_query('_id', state)]

          var request = $.ajax({type: 'POST', url:'/api/v0/advanced/search', dataType:'json', data: {query: JSON.stringify(query)}})

          var dfd = new $.Deferred();
          request.done(function(results) {

            res = results.content.data.map(function(raw_row){
                var row = {};
                for(i=0; i<raw_row.length; ++i)
                {
                    var key = results.content.description[i][0];
                    row[key] = raw_row[i];
                }
                return row;
            })
            if(res && res != undefined && res.length > 0){
                console.log(res[0]);
                item[args.column.field] = res[0];
            }
            else
                alert(state + " is not a valid comment id");
          });

          request.fail(function( jqXHR, textStatus ) {
                alert( "Request failed: " + textStatus );
            });

        };

        this.isValueChanged = function () {
          return (!($input.val() == "" && defaultValue == null)) && ($input.val()._id != defaultValue._id);
        };

        this.validate = function () {
          if (args.column.validator) {
            var validationResults = args.column.validator($input.val());
            if (!validationResults.valid) {
              return validationResults;
            }
          }

          return {
            valid: true,
            msg: null
          };
        };

        this.init();
    }
    return CommentEditor;
}
/*function CommentEditor(args) {
    var $input;
    var defaultValue;
    var scope = this;
    this.init = function () {
      $container = document.createElement('div');
      $container.className = "editor_frame";
      $container.innerHTML = ('<span class="lead">Enter an existing id</span>'
           + '<div class="form-group">'
               + '<label for="id">Id:</label>'
               + '<input type="number" class="form-control" id="id" name="id">'
           + '</div>'
           + '<hr>'
           + '<span class="lead"> or edit the current entry manually</span>'
           + '<div>'
               + '<div class="form-group">'
                   + '<label for="change_all">Create new entry:</label>'
                   + '<select id="change_all" name="change_all">'
                     + '<option> Create new entry </option>'
                     + '<option> Edit current entry </option>'
                   + '</select>'
               + '</div>'
               + '<div class="form-group">'
                   + '<label for="origin">Origin:</label>'
                   + '<input type="text" class="form-control" id="origin" name="origin">'
               + '</div>'
               + '<div class="form-group">'
                   + '<label for="method">Method:</label>'
                   + '<input type="text" class="form-control" id="method" name="method">'
               + '</div>'

           + '</div>');

      var btn_success = document.createElement('button');
      btn_success.className = "btn btn-success";
      btn_success.innerHTML = "OK";
      btn_success.addEventListener("click", this.save);
      $container.appendChild(btn_success);

      var btn_cancel = document.createElement('button');
      btn_cancel.className = "btn btn-danger";
      btn_cancel.innerHTML = "Cancel";
      btn_cancel.addEventListener("click", this.cancel);
      $container.appendChild(btn_cancel);



      args.container.appendChild($container);
      $id = ($($container).find("[name=id]")[0]);
      $method = ($($container).find("[name=method]")[0]);
      $origin = ($($container).find("[name=origin]")[0]);
      $change_all = ($($container).find("[name=change_all]")[0]);
    };

    this.save = function () {
      args.commitChanges();
    };

    this.cancel = function () {
      args.cancelChanges();
    };

    this.destroy = function () {
      $container.remove();
      delete $container;
    };

    this.focus = function () {
      $container.focus();
    };

    this.getValue = function () {
        return {
            method:$method.val(),
            origin:$origin.val()
        };
    };

    this.setValue = function (val) {
      $input.val(val);
    };

    this.loadValue = function (item) {
      if(item._comment.id == null){
        $method.value = "";
        $origin.value = "";
        $change_all.parentNode.className = 'hidden';
      }
      else{
          $change_all.parentNode.className = '';
          $id.value = item._comment.id;
          $method.value = item._comment.method;
          $origin.value = item._comment.origin;
      }
    };

    this.serializeValue = function () {
      return {method: $method.value, origin: $origin.value, id: $id.value};
    };

    this.applyValue = function (item, state) {
      item[args.column.field] = state;
    };

    this.isValueChanged = function () {
        if($id.value != null){
            return {
                id: $id.value,
                method: undefined,
                origin: undefined,
                create: false,
            }
        }
        else
            return {
                id: null,
                method: $method.value,
                origin: $origin.value,
                create: $change_all.checked
            }
    };

    this.validate = function () {

      return {
        valid: true,
        msg: null
      };

      if (args.column.validator) {
        var validationResults = args.column.validator($input.val());
        if (!validationResults.valid) {
          return validationResults;
        }
      }

      return {
        valid: true,
        msg: null
      };
    };

    this.init();
}*/


function EmptyEditor(args) {
    var $value;
    var defaultValue;
    var scope = this;
    this.init = function () {
    };

    this.save = function () {
    };

    this.cancel = function () {
    };

    this.destroy = function () {
    };

    this.focus = function () {
    };

    this.getValue = function () {
        return {
        };
    };

    this.setValue = function (val) {
    };

    this.loadValue = function (item) {
    };


    this.applyValue = function (item, state) {
      item[args.column.field] = state;
    };

    this.isValueChanged = function () {
        return false
    };

    this.validate = function () {

      return {
        valid: true,
        msg: null
      };
    }

    this.init();
}


function get_field_query(field){
    var column_query = {
        type: 'column',
        column: field.id
    };

    if (field.data_type.startsWith('geometry')) {
       // transform coordinates from whatever format they're in
       //   into epsg 4326, i.e. latitude and longitude
        column_query = {
            type: "function",
            function: "ST_Transform",
            operands: [column_query, {type: "value", value: 4326}],
            as: field.id
        };
        // convert geo-data in readable geo-json
        column_query = {
            type: 'function',
            function: 'ST_AsGeoJSON',
            operands: [column_query],
            as: field.id
        };
    }
    return column_query;
}

function condition_query(key, value)
{
    return {
        type:'operator_binary',
        left: {
            type: 'column',
            column: key,
        },
        right: {
            type: 'value',
            value: value
        },
        operator: '='
    };
}
