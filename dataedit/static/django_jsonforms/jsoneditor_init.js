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

                /**
                 monkey patch a download button: TODO better way of adding controls to form
                */

                // create download button
                $('[data-schemaid="root"] h3 textarea').parent().append('<button type="button" id="json-editor-download", class="btn btn-secondary json-editor-btn-copy json-editor-btntype-copy"><span>Download</span></button>')

                // bind download function
                $('#json-editor-download').bind('click', function downloadMetadata(){
                    var json = editor.getValue();
                    // create data url
                    var json = JSON.stringify(json, null, 1);
                    blob = new Blob([json], {type: "application/json"}),
                    dataUrl = URL.createObjectURL(blob);
                    // create link
                    var a = document.createElement("a");
                    document.body.appendChild(a);
                    // assign url and click
                    a.style = "display: none";
                    a.href = dataUrl;
                    a.download = 'metadata.json';
                    a.click();
                    // cleanup
                    URL.revokeObjectURL(dataUrl);
                    a.parentNode.removeChild(a);
                })

                // create
                var convertDescriptionIntoPopover = function(){
                    // find all descriptions
                    $('[data-schemaid="root"] .form-group > p.form-text').each(function(i, e){
                        var description = $(e).text(); // get description text
                        // find all title elements and add description as popover
                        $(e).parent().find('.form-control-label')
                        .attr('data-content', description)
                        .attr('data-toggle', "popover")
                        .popover({
                            placement: 'top',
                            trigger: 'hover',
                            template: '<div class="popover"><div class="arrow"></div><div class="popover-body"></div></div>'
                        });
                        // popover with bootstrap: https://getbootstrap.com/docs/4.0/components/popovers/
                        $(e).hide() // hide original description
                    });
                }
                // update when click on button (because they create new form elements)
                $('[data-schemaid="root"] button').bind('click', convertDescriptionIntoPopover);
                convertDescriptionIntoPopover();

            }
        })
    });
})
