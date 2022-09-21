
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
        json["title"] = "Metadata for " + config.table


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
                    // This is callback functions for the "autocomplete" editor
                    // In the schema you refer to the callback function by key
                    // Note: 1st parameter in callback is ALWAYS a reference to the current editor.
                    // So you need to add a variable to the callback to hold this (like the
                    // "jseditor_editor" variable in the examples below.)

                    // Setup API calls
                    "search_za": function search(jseditor_editor, input) {

                      var url = "http://localhost:9274/lookup-application/api/search?query=" + input

                      return new Promise(function (resolve) {
                          fetch(url, {
                            mode: 'cors',
                            headers: {
                              'Access-Control-Allow-Origin':'*'
                            }
                          }).then(function (response) {
                              return response.json();
                          }).then(function (data) {
                              resolve(data);
                          });
                      });

                      // The above code returns an error because of 'CORS policy'

                      // JUST FOR TESTING THE UI, THE BELOW CODE RETURNS A VALID OUTPUT

                      // return [{"score":["531.92145"],"definition":["A <B>wind<\/B> rotor (or <B>wind<\/B> turbine) is a turbine that converts the <B>wind's<\/B> kinetic energy into rotational energy."],"altLabel":["<B>wind<\/B> turbine"],"label":["<B>wind<\/B> rotor"],"type":["http://www.w3.org/2002/07/owl#Class"],"resource":["http://openenergy-platform.org/ontology/oeo/OEO_00000448"]},{"score":["457.99576"],"definition":["A <B>wind<\/B> energy converting unit is a power generating unit that uses <B>wind<\/B> energy."],"altLabel":["<B>wind<\/B> turbine"],"label":["<B>wind<\/B> energy converting unit"],"type":["http://www.w3.org/2002/07/owl#Class"],"resource":["http://openenergy-platform.org/ontology/oeo/OEO_00000044"]},{"score":["397.43134"],"definition":["<B>Wind<\/B> is a process of air naturally moving."],"label":["<B>wind<\/B>"],"type":["http://www.w3.org/2002/07/owl#Class"],"resource":["http://openenergy-platform.org/ontology/oeo/OEO_00000043"]},{"score":["343.0877"],"definition":["A <B>wind<\/B> farm is a power plant that has <B>wind<\/B> energy converting units as parts."],"label":["<B>wind<\/B> farm"],"type":["http://www.w3.org/2002/07/owl#Class"],"resource":["http://openenergy-platform.org/ontology/oeo/OEO_00000447"]},{"score":["337.30008"],"definition":["<B>Wind<\/B> energy is the kinetic energy of moving air."],"label":["<B>wind<\/B> energy"],"type":["http://www.w3.org/2002/07/owl#Class"],"resource":["http://openenergy-platform.org/ontology/oeo/OEO_00000446"]},{"score":["304.696"],"definition":["An onshore <B>wind<\/B> farm is a <B>wind<\/B> farm that is build on land."],"label":["onshore <B>wind<\/B> farm"],"type":["http://www.w3.org/2002/07/owl#Class"],"resource":["http://openenergy-platform.org/ontology/oeo/OEO_00000311"]},{"score":["301.77304"],"definition":["<B>Wind<\/B> energy transformation is an energy transformation that converts <B>wind<\/B> energy to electrical energy."],"label":["<B>wind<\/B> energy transformation"],"type":["http://www.w3.org/2002/07/owl#Class"],"resource":["http://openenergy-platform.org/ontology/oeo/OEO_00020043"]},{"score":["301.77304"],"definition":["An offshore <B>wind<\/B> farm is a <B>wind<\/B> farm that is build in a body of water, usually the ocean."],"label":["offshore <B>wind<\/B> farm"],"type":["http://www.w3.org/2002/07/owl#Class"],"resource":["http://openenergy-platform.org/ontology/oeo/OEO_00000308"]},{"score":["46.99225"],"definition":["Rotor diameter is a quality of a <B>wind<\/B> energy converting unit that measures the diameter of the <B>wind<\/B> rotor."],"label":["rotor diameter"],"type":["http://www.w3.org/2002/07/owl#Class"],"resource":["http://openenergy-platform.org/ontology/oeo/OEO_00020144"]},{"score":["43.72599"],"definition":["Hub height is a quality of a <B>wind<\/B> energy converting unit that measures the distance between surface and centre-line of the <B>wind<\/B> rotor."],"label":["hub height"],"type":["http://www.w3.org/2002/07/owl#Class"],"resource":["http://openenergy-platform.org/ontology/oeo/OEO_00140000"]},{"score":["17.99287"],"definition":["Origin is a quality of a portion of matter or energy based on where it comes from. It is inherited from its primary sources."],"comment":[" electrical energy, the electrical energy inherits the fossil origin.\n* <B>Wind<\/B> energy has renewable origin"],"label":["origin"],"type":["http://www.w3.org/2002/07/owl#Class"],"resource":["http://openenergy-platform.org/ontology/oeo/OEO_00000316"]},{"score":["4.612715"],"definition":["A GUI (Graphical user interface)  is a software interface allowing users to communicate with a software application through a graphical <B>window<\/B>."],"label":["GUI"],"type":["http://www.w3.org/2002/07/owl#Class"],"resource":["http://openenergy-platform.org/ontology/oeo/OEO_00000202"]},{"score":["2.2452862"],"definition":[" of <B>wire<\/B> for an interval of one second will induce an electromotive force of one volt."],"label":["weber"],"type":["http://www.w3.org/2002/07/owl#Class"],"resource":["http://purl.obolibrary.org/obo/UO_0000226"]},{"score":["2.1938653"],"definition":[" objects, standardized by the International Organization for Standardization (ISO).\nsource: https://en.wikipedia.org/<B>wiki<\/B>/Digital_object_identifier"],"altLabel":["digital object identifier"],"label":["DOI"],"type":["http://www.w3.org/2002/07/owl#Class"],"resource":["http://openenergy-platform.org/ontology/oeo/OEO_00000133"]},{"score":["1.9723274"],"definition":["A portion of matter is an aggregate of material entities that have a state of matter."],"comment":["<B>wiki<\/B> page: https://github.com/OpenEnergyPlatform/ontology/<B>wiki<\/B>/Explanation-on-mass-nouns"],"label":["portion of matter"],"type":["http://www.w3.org/2002/07/owl#Class"],"resource":["http://openenergy-platform.org/ontology/oeo/OEO_00000331"]},{"score":["1.8189514"],"definition":[") for the definition. Free text indicate / attribute source(s) for the definition. EXAMPLE: Author Name, URI, MeSH Term C04, PUBMED ID, <B>Wiki<\/B> uri on 31.01.2007"],"label":["definition source"],"type":["http://www.w3.org/2002/07/owl#AnnotationProperty"],"resource":["http://purl.obolibrary.org/obo/IAO_0000119"]},{"score":["1.793046"],"definition":["A transformer is an electricity grid component that passively transfers electrical energy from one electrical circuit to another."],"comment":["Source: https://en.wikipedia.org/<B>wiki<\/B>/Transformer"],"label":["transformer"],"type":["http://www.w3.org/2002/07/owl#Class"],"resource":["http://openenergy-platform.org/ontology/oeo/OEO_00000420"]},{"score":["1.6580219"],"definition":[" to exceed them, without human intervention. The category also includes all grassland from <B>wild<\/B> lands"],"label":["CRF sector (IPCC 2006): grassland"],"type":["http://openenergy-platform.org/ontology/oeo/OEO_00010035","http://www.w3.org/2002/07/owl#NamedIndividual"],"resource":["http://openenergy-platform.org/ontology/oeo/OEO_00010191"]},{"score":["0.6975789"],"definition":["A label for a class or property that can be used to refer to the class or property instead of the preferred rdfs:label. Alternative labels should be used to indicate community- or context-specific labels, abbreviations, shorthand forms and the like."],"comment":["Consider re-defing to: An alternative name for a class or property which can mean the same thing as the preferred name (semantically equivalent, narrow, broad or related)."," and ambiguous terms as well. See https://github.com/OpenEnergyPlatform/ontology/<B>wiki<\/B>/Handling-ambiguous-terms"],"label":["alternative label","alternative term"],"type":["http://www.w3.org/2002/07/owl#AnnotationProperty"],"resource":["http://purl.obolibrary.org/obo/IAO_0000118"]}]

                    },
                    "renderResult_za": function(jseditor_editor, result, props) {
                        return ['<li ' + props + '>',
                            '<div class="eiao-object-snippet">' + result.label + ' <small>' + result.resource + '<small></div>',
                            '</li>'].join('');
                    },
                    "getResultValue_za": function getResultValue(jseditor_editor, result) {
                        return result.label;
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

            });
        }
    })();

    return config;

}
