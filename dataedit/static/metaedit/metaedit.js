var MetaEdit = function(config) {

    /*
    TODO: consolidate functions (same as in wizard and other places)
    */

    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== "") {
            var cookies = document.cookie.split(";");
            for (var i = 0; i < cookies.length; i++) {
                var cookie = $.trim(cookies[i]);
                if (cookie.substring(0, name.length + 1) === name + "=") {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function getCsrfToken() {
        var token1 = getCookie("csrftoken");
        return token1;
    }

    function sendJson(method, url, data, success, error) {
        var token = getCsrfToken();
        return $.ajax({
            url: url,
            headers: { "X-CSRFToken": token },
            data_type: "json",
            cache: false,
            contentType: "application/json; charset=utf-8",
            processData: false,
            data: data,
            type: method,
            success: success,
            error: error
        });
    }

    function fixProblems(json) {
        // TODO use schema validator, like https://github.com/korzio/djv ?

        // MUST have ID
        json["id"] = json["id"] || config.table;

        // MUST have one resource with name == id == tablename
        json["resources"] = json["resources"] || [{}];
        json["resources"][0]["name"] = json["resources"][0]["name"] || config.table;

        // auto set / correct columns
        json["resources"][0]["schema"] = json["resources"][0]["schema"] || {};
        json["resources"][0]["schema"]["fields"] = json["resources"][0]["schema"]["fields"] || [];
        var fieldsByName = {};
        json["resources"][0]["schema"]["fields"].map(function(field){
            fieldsByName[field.name] = field
        })

        json["resources"][0]["schema"]["fields"] = [];
        config.columns.map(function(column){
            var field = fieldsByName[column.name] || {name: column.name};
            field.type = field.type || column.data_type;
            json["resources"][0]["schema"]["fields"].push(field);
        })

        return json
    }

    function getErrorMsg(x) {
        try {
            x = 'Upload failed: ' + JSON.parse(x.responseJSON).reason;
        } catch (e) {
            x = x.statusText;
        }
        return x;
    }

    function convertDescriptionIntoPopover() {
        config.form.find('.form-group > .form-text').each(function(i, e) {
            var description = $(e).text(); // get description text
            // find all title elements and add description as popover
            $(e).parent().find('label')
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

    function bindButtons() {
        // download
        $('#metaedit-download').bind('click', function downloadMetadata() {
            var json = config.editor.getValue();
            // create data url
            json = JSON.stringify(json, null, 1);
            blob = new Blob([json], { type: "application/json" }),
                dataUrl = URL.createObjectURL(blob);
            // create link
            var a = document.createElement("a");
            document.body.appendChild(a);
            // assign url and click
            a.style = "display: none";
            a.href = dataUrl;
            a.download = config.table + '.metadata.json';
            a.click();
            // cleanup
            URL.revokeObjectURL(dataUrl);
            a.parentNode.removeChild(a);
        });

        // submit
        $('#metaedit-submit').bind('click', function sumbmitMetadata() {
            $('#metaedit-submitting').removeClass('d-none');
            var json = config.editor.getValue();
            json = fixProblems(json);
            json = JSON.stringify(json);
            sendJson("POST", config.url_api_meta, json).then(function() {
                window.location = config.url_view_table;
            }).catch(function(err) {
                // TODO evaluate error, show user message
                $('#metaedit-submitting').addClass('d-none');
                alert(getErrorMsg(err))
            });
        });

        // Cancel
        $('#metaedit-cancel').bind('click', function cancel() {
            window.location = config.url_view_table;
        })

    }

    (function init() {
        $('#metaedit-loading').removeClass('d-none');

        config.form = $('#metaedit-form');

        $.when(
            $.getJSON(config.url_api_meta),
            $.getJSON('/static/metaedit/oem_v_1_4_0.json')
        ).done(function(data, schema) {
            data = fixProblems(data[0]);
            schema = schema[0];

            /*  https://github.com/json-editor/json-editor */
            options = {
                startval: data,
                schema: schema,
                theme: 'bootstrap4',
                disable_collapse: true,
                disable_properties: true,
                compact: true,
                disable_array_reorder: true,
                disable_edit_json: false,
                required_by_default: true,
                remove_empty_properties: true,
            }

            config.editor = new JSONEditor(config.form[0], options);
            config.mainEditBox = config.form.find('.je-object__controls').first();

            /* patch labels */
            config.mainEditBox.find('.json-editor-btntype-save').text('Apply');
            config.mainEditBox.find('.json-editor-btntype-copy').text('Copy to Clipboard');
            config.mainEditBox.find('.json-editor-btntype-cancel').text('Close');
            config.mainEditBox.find('.json-editor-btntype-editjson').text('Edit raw JSON');


            bindButtons();
            convertDescriptionIntoPopover();

            // update when click on button (because they create new form elements)
            config.form.find('button').bind('click', convertDescriptionIntoPopover);

            $('#metaedit-loading').addClass('d-none');
            $('#metaedit-icon').removeClass('d-none');
            $('#metaedit-controls').removeClass('d-none');

        });

    })();

    return config;

}