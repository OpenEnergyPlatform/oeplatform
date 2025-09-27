// SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
// SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
//
// SPDX-License-Identifier: AGPL-3.0-or-later

// e.preventDefault(), e.stopPropagation(), t.saveJSON()

var MetaEdit = (config) => {
  /*
    TODO: consolidate functions (same as in wizard and other places)
    */

  const $ = window.$ // Declare $ variable
  const JSONEditor = window.JSONEditor // Declare JSONEditor variable
  const htmx = window.htmx // Declare htmx variable
  const createUrl = window.createUrl // Declare createUrl variable

  function getCookie(name) {
    var cookieValue = null
    if (document.cookie && document.cookie !== "") {
      var cookies = document.cookie.split(";")
      for (var i = 0; i < cookies.length; i++) {
        var cookie = typeof $ !== "undefined" ? $.trim(cookies[i]) : cookies[i].trim()
        if (cookie.substring(0, name.length + 1) === name + "=") {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
          break
        }
      }
    }
    return cookieValue
  }

  function getCsrfToken() {
    var token1 = getCookie("csrftoken")
    return token1
  }

  function sendJson(method, url, data, success, error) {
    var token = getCsrfToken()
    if (typeof $ === "undefined") {
      console.error("jQuery is required for AJAX requests")
      return Promise.reject("jQuery not available")
    }
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
      error: error,
    })
  }

  function fixSchema(json) {
    /* recursively remove null types */
    function fixRecursive(elem) {
      Object.keys(elem).map((key) => {
        var prop = elem[key]
        prop.title = prop.title || key[0].toLocaleUpperCase() + key.slice(1)
        if (prop.type == "array") {
          // prop.items = prop.items || {};
          prop.items.title = prop.items.title || key[0].toLocaleUpperCase() + key.slice(1) // missing title, otherwise the form label is just "item 1, ..."
          fixRecursive({ "": prop.items })
        } else if (prop.type == "object") {
          // prop.properties = prop.properties || {};
          fixRecursive(prop.properties)
        } else if (typeof prop.type == "object") {
          // find and remove "null"
          var index = prop.type.indexOf("null")
          if (index >= 0) {
            prop.type.splice(index, 1)
          }
          // if only one type --> str
          if (prop.type.length == 1) {
            prop.type = prop.type[0]
          }
        }
      })
    }
    fixRecursive(json.properties)

    // make some readonly
    if (config.standalone == false) {
      json.properties["@id"].readOnly = false
      json.properties.resources.items.properties.schema.properties.fields.items.properties.name.readOnly = true
      json.properties.resources.items.properties.schema.properties.fields.items.properties.type.readOnly = true
    } else {
      json.properties["@context"].options = { hidden: true }
      json.properties["@id"].readOnly = false
      json.properties.resources.items.properties["@id"].readOnly = false
      json.properties.resources.items.properties.path.readOnly = false
      json.properties.resources.items.properties.schema.properties.fields.items.properties.nullable.readOnly = false
      json.properties.resources.items.properties.schema.properties.fields.items.properties.name.readOnly = false
      json.properties.resources.items.properties.schema.properties.fields.items.properties.type.readOnly = false
    }

    // remove some: TODO: but make sure fields are not lost
    // json.properties.resources.items.properties.embargoPeriod = false;

    // hide some
    json.properties.resources.items.properties.embargoPeriod.options = { hidden: true }
    json.properties.resources.items.properties.type.options = { hidden: true }
    json.properties.resources.items.properties.encoding.options = { hidden: true }
    json.properties.resources.items.properties.dialect.options = { hidden: true }
    // json.properties.resources.items.properties.review.options = {hidden: true};
    json.properties.metaMetadata.options = { hidden: true }

    // add formats
    // json.properties.context.properties.homepage.format = 'url'; // uri or url???

    json["options"] = {
      disable_edit_json: false, // show only for entire form
    }

    if (config.standalone == false) {
      json["title"] = "Metadata for the Dataset: " + config.table
    } else {
      json["title"] = "Create new Metadata for your Dataset"
    }

    // add names to resources categories
    json.properties.resources.items.basicCategoryTitle = "General"

    return json
  }

  function fixData(json) {
    json = json || {}

    // Required top-level fields
    json["@context"] =
      json["@context"] ||
      "https://raw.githubusercontent.com/OpenEnergyPlatform/oemetadata/production/oemetadata/latest/context.json"

    json.metaMetadata = json.metaMetadata || {}
    if (!json.metaMetadata.metadataVersion) {
      json.metaMetadata.metadataVersion = "OEMetadata-2.0.4"
    }

    // Ensure one resource
    json.resources = json.resources || [{}]
    const resource = json.resources[0]
    resource.name = resource.name || config.table
    resource.path = resource.path || config.url_table_id

    // Ensure schema object exists
    resource.schema = resource.schema || {}
    resource.schema.fields = resource.schema.fields || []

    // Rebuild fields with merging and renaming
    const existingFields = resource.schema.fields
    const fieldMap = new Map()

    // Add existing fields to a map for quick lookup
    existingFields.forEach((field) => {
      if (field.name) fieldMap.set(field.name, field)
    })

    // Prepare updated fields array
    const updatedFields = config.columns.map((col) => {
      const existing = fieldMap.get(col.name) || {}

      return {
        name: col.name,
        type: col.data_type || existing.type || null,
        description: existing.description ?? null,
        unit: existing.unit ?? null,
        nullable: existing.nullable !== undefined ? existing.nullable : true,
      }
    })

    // Set updated field list (removes stale fields)
    resource.schema.fields = updatedFields

    // Fill missing top-level fields recursively based on schema
    function fillMissingFromSchema(schemaProps, target) {
      Object.entries(schemaProps).forEach(([key, prop]) => {
        if (target[key] === undefined) {
          if (prop.type === "object") {
            target[key] = {}
            if (prop.properties) {
              fillMissingFromSchema(prop.properties, target[key])
            }
          } else if (prop.type === "array") {
            target[key] = []
            if (prop.items?.type === "object" && prop.items.properties) {
              const obj = {}
              fillMissingFromSchema(prop.items.properties, obj)
              target[key].push(obj)
            }
          } else {
            target[key] = null
          }
        } else if (prop.type === "object" && typeof target[key] === "object" && prop.properties) {
          fillMissingFromSchema(prop.properties, target[key])
        } else if (prop.type === "array" && Array.isArray(target[key]) && prop.items?.properties) {
          target[key].forEach((item) => {
            if (typeof item === "object") {
              fillMissingFromSchema(prop.items.properties, item)
            }
          })
        }
      })
    }

    fillMissingFromSchema(config.schema.properties, json)
    // Fix boundingBox in each resource if needed
    if (Array.isArray(json.resources)) {
      json.resources.forEach((resource) => {
        const bboxPath = resource?.spatial?.extent?.boundingBox
        if (!Array.isArray(bboxPath) || bboxPath.length !== 4 || bboxPath.some((val) => typeof val !== "number")) {
          if (!resource.spatial) resource.spatial = {}
          if (!resource.spatial.extent) resource.spatial.extent = {}
          resource.spatial.extent.boundingBox = [0, 0, 0, 0] // fallback valid default
        }
      })
    }

    return json
  }

  function getErrorMsg(x) {
    try {
      x = "Upload failed: " + JSON.parse(x.responseJSON).reason
    } catch (e) {
      x = x.statusText
    }
    return x
  }

  // Function to recursively convert empty strings to null
  function convertEmptyStringsToNull(obj) {
    for (var key in obj) {
      if (obj.hasOwnProperty(key)) {
        if (typeof obj[key] === "string" && obj[key] === "") {
          obj[key] = null
        } else if (typeof obj[key] === "object") {
          convertEmptyStringsToNull(obj[key])
        }
      }
    }
  }

  function bindButtons() {
    if (typeof $ === "undefined") {
      console.error("jQuery is required for button binding")
      return
    }

    // download
    $("#metaedit-download").bind("click", function downloadMetadata() {
      var json = config.editor.getValue()
      convertEmptyStringsToNull(json)
      console.log(json)
      json = JSON.stringify(json, null, 1)
      var blob = new Blob([json], { type: "application/json" })
      var dataUrl = URL.createObjectURL(blob)
      var a = document.createElement("a")
      document.body.appendChild(a)
      a.style = "display: none"
      a.href = dataUrl
      a.download = config.table + ".metadata.json"
      a.click()
      URL.revokeObjectURL(dataUrl)
      a.parentNode.removeChild(a)
    })

    // submit
    $("#metaedit-submit").bind("click", function sumbmitMetadata() {
      $("#metaedit-submitting").removeClass("d-none")
      var json = config.editor.getValue()
      convertEmptyStringsToNull(json)
      json = fixData(json)
      json = JSON.stringify(json)
      sendJson("POST", config.url_api_meta, json)
        .then(() => {
          window.location = config.url_view_table
        })
        .catch((err) => {
          $("#metaedit-submitting").addClass("d-none")
          alert(getErrorMsg(err))
        })
    })

    // Cancel
    $("#metaedit-cancel").bind("click", function cancel() {
      window.location = config.cancle_url
    })
  }
  ;(function init() {
    if (typeof $ === "undefined") {
      console.error("jQuery is required for MetaEdit initialization")
      return
    }

    $("#metaedit-loading").removeClass("d-none")

    config.form = $("#metaedit-form")

    if (config.standalone == false) {
      $.when($.getJSON(config.url_api_meta), $.getJSON("/static/metaedit/schema.json")).done((data, schema) => {
        config.schema = fixSchema(schema[0])
        config.initialData = fixData(data[0])

        var options = {
          startval: config.initialData,
          schema: config.schema,
          theme: "bootstrap5",
          iconlib: "fontawesome5",
          mode: "form",
          compact: true,
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
          remove_empty_properties: false,
          show_errors: "interaction",
        }

        if (typeof JSONEditor === "undefined") {
          console.error("JSONEditor is required but not available")
          return
        }

        config.editor = new JSONEditor(config.form[0], options)

        var mainEditBox = config.form.find(".je-object__controls").first()
        mainEditBox.find(".json-editor-btntype-save").text("Apply")
        mainEditBox.find(".json-editor-btntype-copy").text("Copy to Clipboard")
        mainEditBox.find(".json-editor-btntype-cancel").text("Close")
        mainEditBox.find(".json-editor-btntype-editjson").text("Edit raw JSON")

        bindButtons()

        new MutationObserver((_mutationsList, _observer) => {}).observe(config.form[0], {
          attributes: false,
          childList: true,
          subtree: true,
        })

        $("#metaedit-loading").addClass("d-none")
        $("#metaedit-icon").removeClass("d-none")
        $("#metaedit-controls").removeClass("d-none")

        if (typeof JSONEditor !== "undefined" && JSONEditor.defaults) {
          window.JSONEditor.defaults.callbacks = {
            autocomplete: {
              search_name: function search(jseditor_editor, input) {
                var url = "https://openenergyplatform.org/api/oeo-search?query=" + input

                return new Promise((resolve) => {
                  fetch(url, {
                    mode: "cors",
                  })
                    .then((response) => response.json())
                    .then((data) => {
                      resolve(data["docs"])
                    })
                })
              },
              renderResult_name: (jseditor_editor, result, props) =>
                [
                  "<li " + props + ">",
                  '<div class="eiao-object-snippet">' +
                    result.label +
                    "<small>" +
                    '<span style="color:green">' +
                    " : " +
                    result.definition +
                    "</span></div>",
                  "</li>",
                ].join(""),
              getResultValue_name: function getResultValue(jseditor_editor, result) {
                var selected_value = String(result.label).replaceAll("<B>", "").replaceAll("</B>", "")

                const path = String(jseditor_editor.path).replace("name", "@id")
                const path_uri = config.editor.getEditor(path)
                path_uri.setValue(String(result.resource))

                return selected_value
              },
            },
            button: {
              openModalAction: function openOeoExtPlugin(jseditor, e) {
                if (typeof htmx !== "undefined" && typeof createUrl !== "undefined") {
                  htmx.ajax("GET", createUrl, {
                    target: ".modal-body",
                    swap: "innerHTML",
                    trigger: "click",
                  })
                  $("#formModal").modal("show")
                } else {
                  console.warn("HTMX or createUrl not available for modal action")
                }
              },
            },
          }
        }
      })
    } else {
      $.when($.getJSON("/static/metaedit/schema.json")).done((schema) => {
        config.schema = fixSchema(schema)

        var standalone_options = {
          schema: config.schema,
          theme: "bootstrap5",
          iconlib: "fontawesome5",
          mode: "form",
          compact: true,
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
          remove_empty_properties: false,
        }

        if (typeof JSONEditor === "undefined") {
          console.error("JSONEditor is required but not available")
          return
        }

        config.editor = new JSONEditor(config.form[0], standalone_options)

        var mainEditBox = config.form.find(".je-object__controls").first()
        mainEditBox.find(".json-editor-btntype-save").text("Apply")
        mainEditBox.find(".json-editor-btntype-copy").text("Copy to Clipboard")
        mainEditBox.find(".json-editor-btntype-cancel").text("Close")
        mainEditBox.find(".json-editor-btntype-editjson").text("Edit raw JSON")

        bindButtons()

        new MutationObserver((_mutationsList, _observer) => {}).observe(config.form[0], {
          attributes: false,
          childList: true,
          subtree: true,
        })

        $("#metaedit-loading").addClass("d-none")
        $("#metaedit-icon").removeClass("d-none")
        $("#metaedit-controls").removeClass("d-none")

        if (typeof JSONEditor !== "undefined" && JSONEditor.defaults) {
          window.JSONEditor.defaults.callbacks = {
            autocomplete: {
              search_name: function search(jseditor_editor, input) {
                var url = "https://openenergyplatform.org/api/oeo-search?query=" + input

                return new Promise((resolve) => {
                  fetch(url, {
                    mode: "cors",
                  })
                    .then((response) => response.json())
                    .then((data) => {
                      resolve(data["docs"])
                    })
                })
              },
              renderResult_name: (jseditor_editor, result, props) =>
                [
                  "<li " + props + ">",
                  '<div class="eiao-object-snippet">' +
                    result.label +
                    "<small>" +
                    '<span style="color:green">' +
                    " : " +
                    result.definition +
                    "</span></div>",
                  "</li>",
                ].join(""),
              getResultValue_name: function getResultValue(jseditor_editor, result) {
                var selected_value = String(result.label).replaceAll("<B>", "").replaceAll("</B>", "")

                const path = String(jseditor_editor.path).replace("name", "@id")
                const path_uri = config.editor.getEditor(path)
                path_uri.setValue(String(result.resource))

                return selected_value
              },
            },
            button: {
              openModalAction: function openOeoExtPlugin(jseditor, e) {
                if (typeof htmx !== "undefined" && typeof createUrl !== "undefined") {
                  htmx.ajax("GET", createUrl, {
                    target: ".modal-body",
                    swap: "innerHTML",
                    trigger: "click",
                  })
                  $("#formModal").modal("show")
                } else {
                  console.warn("HTMX or createUrl not available for modal action")
                }
              },
            },
          }
        }
      })
    }
  })()

  return config
}
