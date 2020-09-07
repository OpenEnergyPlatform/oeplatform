$('document').ready(function() {

    // Get value from either a json string or url pointing to a json file
    function process(value) {
        var isjson=true;
        var result;

        try {
          result = JSON.parse(value);
        } catch(e) {
          isjson=false;
        }

        if (isjson) {
          return result;
        } else {
          return $.getJSON(value)
            .then(function (response) {
                return response;
            });
        }
    }

    $('.editor_holder').each(function() {
        // Get the DOM Element
        var element = $(this).get(0);

        var options_text = $(this).attr('options')
        var schema_text = $(this).attr('schema')

        var schema = process(schema_text);
        var options = process(options_text);

        var name = $(this).attr('name');
        var hidden_identifier = 'input[name=' + name + ']';
        var initial = $(hidden_identifier).val();

        // Check if editor is within form
        var form = $(this).closest('form')

        //Wait for any ajax requests to complete
        $.when(schema, options).done(function(schemaresult, optionsresult) {
            optionsresult.form_name_root = name;

            // Pass initial value though to editor
            if (initial) {
                optionsresult.startval = JSON.parse(initial);
            }

            optionsresult.schema = schemaresult;
            // console.log(options);
            var editor = new JSONEditor(element, optionsresult);

            if (form) {
                $(form).submit(function() {
                    // Set the hidden field value to the editors value
                    $(hidden_identifier).val(JSON.stringify(editor.getValue()));
                    // Disable the editor so it's values wont be submitted
                    editor.disable();
                })
            }
        })
    });
})
