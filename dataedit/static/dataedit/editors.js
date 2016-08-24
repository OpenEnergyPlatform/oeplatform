function CommentEditor(args) {
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
                origin: undefined
                create = false,
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
}