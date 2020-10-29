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

    function getApiMetaUrl(schema, tablename) {
        var apiVersion = "v0";
        return "/api/" + apiVersion + "/schema/" + schema + "/tables/" + tablename + "/meta/"; // must have trailing slash
    }

    function getTableUrl(schema, tablename) {
        return "/dataedit/view/" + schema + "/" + tablename;
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

    function validate(json) {
        // TODO use schema validator, like https://github.com/korzio/djv
        return json
    }

    function initialize(json) {
        json = json || {};
        return null;
    }

    function _todo() {

        // create download button
        $('[data-schemaid="root"] h3 textarea').parent().append('<button type="button" id="json-editor-download", class="btn btn-secondary json-editor-btn-copy json-editor-btntype-copy"><span>Download</span></button>')

        // bind download function
        $('#json-editor-download').bind('click', function downloadMetadata() {
            var json = editor.getValue();
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
            a.download = 'metadata.json';
            a.click();
            // cleanup
            URL.revokeObjectURL(dataUrl);
            a.parentNode.removeChild(a);
        })


        var buttonRow = $('<div class="">').appendTo('form');
        // Submit
        $('<div class="btn btn-primary">Submit</div>').bind('click', function submit() {
                var url = getApiMetaUrl(config.schema, config.table);
                var urlSuccess = getTableUrl(config.schema, config.table);
                var json = editor.getValue();
                json = validate(json);
                json = JSON.stringify(json);
                sendJson("POST", url, json).then(function() {
                    window.location = urlSuccess;
                }).catch(function(err) {
                    // TODO evaluate error, show user message
                    console.error(err)
                });
            }).appendTo(buttonRow)
            // Cancel
        $('<div class="btn btn-primary">Cancel</div>').bind('click', function cancel() {
            var urlCancel = getTableUrl(config.schema, config.table);
            window.location = urlCancel
        }).appendTo(buttonRow)

        // create popovers instead of descriptions
        var convertDescriptionIntoPopover = function() {
                // find all descriptions
                $('[data-schemaid="root"] .form-group > p.form-text').each(function(i, e) {
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

    (function init() {
        config.form = $('#metaedit-form');

        $.when(
            $.getJSON(config.url_api_meta),
            $.getJSON('/static/metaedit/oem_v_1_4_0.json')
        ).done(function(schema, data) {
            options = {
                startval: data[0],
                schema: schema[0],
                form_name_root: 'NAME',
                theme: 'bootstrap4',
                disable_collapse: true,
                disable_properties: true,
                compact: true,
                disable_array_reorder: true
            }
            console.log(options);

            config.editor = new JSONEditor(config.form[0], options);

        });


    })();

    return config;

}