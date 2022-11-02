
// e.preventDefault(), e.stopPropagation(), t.saveJSON()


var MetaEdit = function (config) {
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


    function fixSchema(json) {
        /* recursively remove null types */
        function fixRecursive(elem) {
            Object.keys(elem).map(function (key) {
                var prop = elem[key];
                prop.title = prop.title || key[0].toLocaleUpperCase() + key.slice(1)
                if (prop.type == 'array') {
                    //prop.items = prop.items || {};
                    prop.items.title = prop.items.title || key[0].toLocaleUpperCase() + key.slice(1); // missing title, otherwise the form label is just "item 1, ..."
                    fixRecursive({ "": prop.items });
                } else if (prop.type == 'object') {
                    //prop.properties = prop.properties || {};
                    fixRecursive(prop.properties);
                } else if (typeof prop.type == 'object') {
                    // find and remove "null"
                    var index = prop.type.indexOf("null");
                    if (index >= 0) {
                        prop.type.splice(index, 1);
                    }
                    // if only one type --> str
                    if (prop.type.length == 1) {
                        prop.type = prop.type[0];
                    }
                }
            })
        }
        fixRecursive(json.properties);

        // make some readonly
        json.properties.id.readonly = true;
        json.properties.resources.items.properties.schema.properties.fields.items.properties.name.readonly = true;
        json.properties.resources.items.properties.schema.properties.fields.items.properties.type.readonly = true;

        // hide some
        json.properties.resources.items.properties.profile.options = { hidden: true };
        json.properties.resources.items.properties.encoding.options = { hidden: true };
        json.properties.resources.items.properties.dialect.options = { hidden: true };
        json.properties.review.options = { hidden: true };
        json.properties.metaMetadata.options = { hidden: true };

        // add formats
        json.properties.publicationDate.format = 'date';
        json.properties.temporal.properties.referenceDate.format = 'date';
        json.properties.context.properties.homepage.format = 'url';

        json["options"] = {
            "disable_edit_json": false, // show only for entire form
        }

        if (config.standalone == false) {
            json["title"] = "Metadata for " + config.table
        } else {
            json["title"] = "Create new Metadata"
        }


        return json
    }

    function fixData(json) {


        // MUST have ID
        json["id"] = json["id"] || config["url_table_id"];

        // MUST have one resource with name == id == tablename
        json["resources"] = json["resources"] || [{}];
        json["resources"][0]["name"] = json["resources"][0]["name"] || config.table;

        // auto set / correct columns
        json["resources"][0]["schema"] = json["resources"][0]["schema"] || {};
        json["resources"][0]["schema"]["fields"] = json["resources"][0]["schema"]["fields"] || [];
        var fieldsByName = {};
        json["resources"][0]["schema"]["fields"].map(function (field) {
            fieldsByName[field.name] = field
        })

        json["resources"][0]["schema"]["fields"] = [];
        config.columns.map(function (column) {
            var field = fieldsByName[column.name] || { name: column.name };
            field.type = field.type || column.data_type;
            json["resources"][0]["schema"]["fields"].push(field);
        })


        // add empty value for all missing so they show up in editor
        // these will be removed at the end
        function fixRecursive(schemaProps, elemObject, path) {
            // is object ?
            if (typeof elemObject != 'object' || $.isArray(elemObject)) {
                return;
            }
            // for each key: fill missing (recursively)
            Object.keys(schemaProps).map(function (key) {
                var prop = schemaProps[key];
                //console.log(path + '.' + key, prop.type)
                if (prop.type == 'object') {
                    elemObject[key] = elemObject[key] || {};
                    fixRecursive(prop.properties, elemObject[key], path + '.' + key);
                }
                else if (prop.type == 'array') {
                    elemObject[key] = elemObject[key] || [];
                    // if non empty array
                    if ($.isArray(elemObject[key]) && elemObject[key].length > 0) {
                        elemObject[key].map(function (elem, i) {
                            fixRecursive(prop.items.properties, elem, path + '.' + key + '.' + i);
                        })
                    }
                }
                else { // value
                    if (elemObject[key] === undefined) {
                        //console.log('adding empty value: ' + path + '.' + key)
                        elemObject[key] = null;
                    }
                }

            });
        }

        fixRecursive(config.schema.properties, json, 'root')

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
        function convert(descr, label) {
            var description = $(descr).text(); // get description text
            if (description && label) {
                label
                    .attr('data-content', description)
                    .attr('title', label.text())
                    .attr('data-toggle', "popover")
                    .popover({
                        placement: 'top',
                        trigger: 'hover',
                        template: '<div class="popover"><div class="arrow"></div><div class="popover-body"></div></div>'
                    });
                descr.addClass('d-none')
            }
        }

        // headings
        config.form.find('.card-title').parent().find('>p').not('.d-none').each(function (i, e) {
            convert($(e), $(e).parent().find('>.card-title>label'))
        });

        // inputs
        config.form.find('.form-group>.form-text').not('.d-none').each(function (_i, e) {
            convert($(e), $(e).parent().find('>label'))
        });

        // remove button groups
        config.form.find('.btn-group').removeClass('btn-group');


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
            json = fixData(json);
            json = JSON.stringify(json);
            sendJson("POST", config.url_api_meta, json).then(function () {
                window.location = config.url_view_table;
            }).catch(function (err) {
                // TODO evaluate error, show user message
                $('#metaedit-submitting').addClass('d-none');
                alert(getErrorMsg(err))
            });
        });

        // Cancel
        $('#metaedit-cancel').bind('click', function cancel() {
            window.location = config.cancle_url;
        })

    }

    (function init() {

        $('#metaedit-loading').removeClass('d-none');

        config.form = $('#metaedit-form');

        // check if the editor should be initialized with metadata from table or as standalone withou any initial data
        if (config.standalone == false) {
            $.when(
                $.getJSON(config.url_api_meta),
                $.getJSON('/static/metaedit/schema.json'),
            ).done(function (data, schema) {
                config.schema = fixSchema(schema[0]);
                config.initialData = fixData(data[0]);


                 /*  https://github.com/json-editor/json-editor */
                options = {
                    startval: config.initialData,
                    schema: config.schema,
                    theme: 'bootstrap4',
                    iconlib: 'fontawesome5',
                    mode: 'form',
                    compact: true,
                    remove_button_labels: true,
                    disable_collapse: true,
                    prompt_before_delete: false,
                    object_layout: "normal",
                    disable_properties: false,
                    disable_edit_json: true,
                    disable_array_delete_last_row: true,
                    disable_array_delete_all_rows: true,
                    disable_array_reorder: true,
                    array_controls_top: true,
                    no_additional_properties: true,
                    required_by_default: false,
                    remove_empty_properties: true, // don't remove, otherwise the metadata will not pass the validation on the server
                }

                config.editor = new JSONEditor(config.form[0], options);

                /* patch labels */
                var mainEditBox = config.form.find('.je-object__controls').first();
                mainEditBox.find('.json-editor-btntype-save').text('Apply');
                mainEditBox.find('.json-editor-btntype-copy').text('Copy to Clipboard');
                mainEditBox.find('.json-editor-btntype-cancel').text('Close');
                mainEditBox.find('.json-editor-btntype-editjson').text('Edit raw JSON');

                bindButtons();

                convertDescriptionIntoPopover();
                // check for new items in dom
                (new MutationObserver(function (_mutationsList, _observer) {
                    convertDescriptionIntoPopover()
                })).observe(config.form[0], { attributes: false, childList: true, subtree: true });

                // all done
                $('#metaedit-loading').addClass('d-none');
                $('#metaedit-icon').removeClass('d-none');
                $('#metaedit-controls').removeClass('d-none');

                // TODO catch init error


                window.JSONEditor.defaults.callbacks = {
                "autocomplete": {
                    "search_name": function search(jseditor_editor, input) {

                      var url = "/api/v0/oeo-search?query=" + input

                      return new Promise(function (resolve) {
                          fetch(url, {
                            mode: 'cors',
                            headers: {
                              'Access-Control-Allow-Origin':'*'
                            }
                          }).then(function (response) {
                              return response.json();
                          }).then(function (data) {
                              resolve(data["docs"]);
                          });
                      });

                    },
                    "renderResult_name": function(jseditor_editor, result, props) {
                        return ['<li ' + props + '>',
                            '<div class="eiao-object-snippet">' + result.label + '<small>' + '<span style="color:green">' + ' : ' + result.definition + '</span></div>',
                            '</li>'].join('');
                    },
                    "getResultValue_name": function getResultValue(jseditor_editor, result) {
                        selected_value = String(result.label).replaceAll("<B>", "").replaceAll("</B>", "");

                        let path = String(jseditor_editor.path).replace("name", "path");
                        let path_uri = config.editor.getEditor(path);
                        path_uri.setValue(String(result.resource));

                        return selected_value;
                    }
                }
              };



            });

        } else {
            $.when(
                $.getJSON('/static/metaedit/schema.json'),
            ).done(function (schema) {
                config.schema = fixSchema(schema);

                standalone_options = {
                    schema: config.schema,
                    theme: 'bootstrap4',
                    iconlib: 'fontawesome5',
                    mode: 'form',
                    compact: true,
                    remove_button_labels: true,
                    disable_collapse: true,
                    prompt_before_delete: false,
                    object_layout: "normal",
                    disable_properties: false,
                    disable_edit_json: true,
                    disable_array_delete_last_row: true,
                    disable_array_delete_all_rows: true,
                    disable_array_reorder: true,
                    array_controls_top: true,
                    no_additional_properties: true,
                    required_by_default: false,
                    remove_empty_properties: true, // don't remove, otherwise the metadata will not pass the validation on the server
                }
                config.editor = new JSONEditor(config.form[0], standalone_options);

                 /* patch labels */
                var mainEditBox = config.form.find('.je-object__controls').first();
                mainEditBox.find('.json-editor-btntype-save').text('Apply');
                mainEditBox.find('.json-editor-btntype-copy').text('Copy to Clipboard');
                mainEditBox.find('.json-editor-btntype-cancel').text('Close');
                mainEditBox.find('.json-editor-btntype-editjson').text('Edit raw JSON');

                bindButtons();

                convertDescriptionIntoPopover();
                // check for new items in dom
                (new MutationObserver(function (_mutationsList, _observer) {
                    convertDescriptionIntoPopover()
                })).observe(config.form[0], { attributes: false, childList: true, subtree: true });

                // all done
                $('#metaedit-loading').addClass('d-none');
                $('#metaedit-icon').removeClass('d-none');
                $('#metaedit-controls').removeClass('d-none');

                // TODO catch init error
                
                window.JSONEditor.defaults.callbacks = {
                    "autocomplete": {
                        "search_name": function search(jseditor_editor, input) {
    
                          var url = "/api/v0/oeo-search?query=" + input
    
                          return new Promise(function (resolve) {
                              fetch(url, {
                                mode: 'cors',
                                headers: {
                                  'Access-Control-Allow-Origin':'*'
                                }
                              }).then(function (response) {
                                  return response.json();
                              }).then(function (data) {
                                  resolve(data["docs"]);
                              });
                          });
    
                        },
                        "renderResult_name": function(jseditor_editor, result, props) {
                            return ['<li ' + props + '>',
                                '<div class="eiao-object-snippet">' + result.label + '<small>' + '<span style="color:green">' + ' : ' + result.definition + '</span></div>',
                                '</li>'].join('');
                        },
                        "getResultValue_name": function getResultValue(jseditor_editor, result) {
                            selected_value = String(result.label).replaceAll("<B>", "").replaceAll("</B>", "");
    
                            let path = String(jseditor_editor.path).replace("name", "path");
                            let path_uri = config.editor.getEditor(path);
                            path_uri.setValue(String(result.resource));
    
                            return selected_value;
                        }
                    }
                  };
    
    
            });
        }
    })();


    return config;

}
