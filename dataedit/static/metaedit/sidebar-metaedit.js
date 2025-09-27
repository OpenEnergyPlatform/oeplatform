// Enhanced MetaEdit with Sidebar Layout
window.SidebarMetaEdit = (config) => {
  function getCookie(name) {
    var cookieValue = null
    if (document.cookie && document.cookie !== "") {
      var cookies = document.cookie.split(";")
      for (var i = 0; i < cookies.length; i++) {
        var cookie = window.$.trim(cookies[i])
        if (cookie.substring(0, name.length + 1) === name + "=") {
          cookieValue = window.decodeURIComponent(cookie.substring(name.length + 1))
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
    return window.$.ajax({
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
    function fixRecursive(elem) {
      window.Object.keys(elem).map((key) => {
        var prop = elem[key]
        prop.title = prop.title || key[0].toLocaleUpperCase() + key.slice(1)
        if (prop.type == "array") {
          prop.items.title = prop.items.title || key[0].toLocaleUpperCase() + key.slice(1)
          fixRecursive({ "": prop.items })
        } else if (prop.type == "object") {
          fixRecursive(prop.properties)
        } else if (typeof prop.type == "object") {
          var index = prop.type.indexOf("null")
          if (index >= 0) {
            prop.type.splice(index, 1)
          }
          if (prop.type.length == 1) {
            prop.type = prop.type[0]
          }
        }
      })
    }
    fixRecursive(json.properties)

    // Configure for sidebar layout
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

    // Hide sections that will be managed by sidebar
    json.properties.resources.items.properties.embargoPeriod.options = { hidden: true }
    json.properties.resources.items.properties.type.options = { hidden: true }
    json.properties.resources.items.properties.encoding.options = { hidden: true }
    json.properties.resources.items.properties.dialect.options = { hidden: true }
    json.properties.metaMetadata.options = { hidden: true }

    json["options"] = {
      disable_edit_json: false,
      disable_collapse: true,
      object_layout: "normal",
    }

    if (config.standalone == false) {
      json["title"] = "Metadata for the Dataset: " + config.table
    } else {
      json["title"] = "Create new Metadata for your Dataset"
    }

    json.properties.resources.items.basicCategoryTitle = "General"

    return json
  }

  function fixData(json) {
    json = json || {}

    json["@context"] =
      json["@context"] ||
      "https://raw.githubusercontent.com/OpenEnergyPlatform/oemetadata/production/oemetadata/latest/context.json"

    json.metaMetadata = json.metaMetadata || {}
    if (!json.metaMetadata.metadataVersion) {
      json.metaMetadata.metadataVersion = "OEMetadata-2.0.4"
    }

    json.resources = json.resources || [{}]
    const resource = json.resources[0]
    resource.name = resource.name || config.table
    resource.path = resource.path || config.url_table_id

    resource.schema = resource.schema || {}
    resource.schema.fields = resource.schema.fields || []

    const existingFields = resource.schema.fields
    const fieldMap = new window.Map()

    existingFields.forEach((field) => {
      if (field.name) fieldMap.set(field.name, field)
    })

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

    resource.schema.fields = updatedFields

    function fillMissingFromSchema(schemaProps, target) {
      window.Object.entries(schemaProps).forEach(([key, prop]) => {
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

    if (Array.isArray(json.resources)) {
      json.resources.forEach((resource) => {
        const bboxPath = resource?.spatial?.extent?.boundingBox
        if (!Array.isArray(bboxPath) || bboxPath.length !== 4 || bboxPath.some((val) => typeof val !== "number")) {
          if (!resource.spatial) resource.spatial = {}
          if (!resource.spatial.extent) resource.spatial.extent = {}
          resource.spatial.extent.boundingBox = [0, 0, 0, 0]
        }
      })
    }

    return json
  }

  function createSidebarNavigation() {
    const sections = [
      {
        title: "Dataset Overview",
        items: [
          { id: "dataset-info", label: "Basic Information", fields: ["name", "title", "description", "@id"] },
          { id: "dataset-context", label: "Context & Keywords", fields: ["context", "keywords"] },
        ],
      },
      {
        title: "Data Resources",
        items: [
          { id: "resource-list", label: "Resource Management", special: "resource-manager" },
          {
            id: "resource-general",
            label: "General Info",
            fields: ["resources.*.name", "resources.*.title", "resources.*.description"],
          },
          { id: "resource-schema", label: "Schema & Fields", fields: ["resources.*.schema"] },
          { id: "resource-spatial", label: "Spatial Data", fields: ["resources.*.spatial"] },
          { id: "resource-temporal", label: "Temporal Data", fields: ["resources.*.temporal"] },
        ],
      },
      {
        title: "Documentation",
        items: [
          { id: "sources", label: "Sources", fields: ["resources.*.sources"] },
          { id: "licenses", label: "Licenses", fields: ["resources.*.licenses"] },
          { id: "contributors", label: "Contributors", fields: ["resources.*.contributors"] },
        ],
      },
    ]

    return sections
  }

  function buildSidebar() {
    const sections = createSidebarNavigation()
    let sidebarHTML = `
      <div class="sidebar">
        <div class="sidebar-header">
          <h3><i class="fa fa-tags mr-2"></i>Metadata Editor</h3>
        </div>
        <div class="sidebar-nav">
    `

    sections.forEach((section) => {
      sidebarHTML += `
        <div class="nav-section">
          <div class="nav-section-title">${section.title}</div>
      `

      section.items.forEach((item, index) => {
        const activeClass = index === 0 && section === sections[0] ? "active" : ""
        sidebarHTML += `
          <a href="#" class="nav-item ${activeClass}" data-section="${item.id}" data-special="${item.special || ""}">
            ${item.label}
            ${item.badge ? `<span class="badge badge-${item.badge.toLowerCase()}">${item.badge}</span>` : ""}
          </a>
        `
      })

      sidebarHTML += `</div>`
    })

    sidebarHTML += `
        </div>
      </div>
    `

    return sidebarHTML
  }

  function initSidebarNavigation() {
    window.$(document).on("click", ".nav-item", function (e) {
      e.preventDefault()

      // Update active state
      window.$(".nav-item").removeClass("active")
      window.$(this).addClass("active")

      const sectionId = window.$(this).data("section")
      const special = window.$(this).data("special")

      // Hide all form sections
      window.$(".form-section").addClass("hidden")

      if (special === "resource-manager") {
        showResourceManager()
      } else {
        showFormSection(sectionId)
      }
    })
  }

  function showResourceManager() {
    window.$("#metaedit-form").hide()

    const resourceManagerHTML = `
      <div class="form-section" id="resource-manager">
        <h4>Data Resource Management</h4>
        <p class="text-muted">Manage your dataset resources. Each resource represents a data file or table.</p>
        
        <div class="resource-list" id="resource-list">
          <!-- Resources will be populated here -->
        </div>
        
        <button class="btn btn-primary add-resource-btn" onclick="addNewResource()">
          <i class="fa fa-plus mr-2"></i>Add New Resource
        </button>
      </div>
    `

    window.$(".main-content .content-body").html(resourceManagerHTML)
    updateResourceList()
  }

  function updateResourceList() {
    if (!config.editor) {
      // Editor not ready yet, show loading state
      window
        .$("#resource-list")
        .html('<div class="text-center"><i class="fa fa-spinner fa-spin"></i> Loading resources...</div>')
      return
    }

    const resources = config.editor.getValue().resources || []
    let resourceHTML = ""

    resources.forEach((resource, index) => {
      const name = resource.name || `Resource ${index + 1}`
      const description = resource.description || "No description provided"

      resourceHTML += `
        <div class="resource-item ${index === 0 ? "active" : ""}" data-index="${index}">
          <h5>${name}</h5>
          <p>${description}</p>
        </div>
      `
    })

    window.$("#resource-list").html(resourceHTML)

    // Handle resource selection
    window.$(".resource-item").click(function () {
      window.$(".resource-item").removeClass("active")
      window.$(this).addClass("active")
      const index = window.$(this).data("index")
      // Switch to resource editing view
      window.showResourceForm(index)
    })
  }

  function showFormSection(sectionId) {
    window.$("#metaedit-form").show()

    // Show all form elements first, then hide what we don't need
    window.$("#metaedit-form .je-object__container").show()
    window.$("#metaedit-form .je-object__container > div").show()

    // Show specific sections based on sectionId
    switch (sectionId) {
      case "dataset-info":
        showDatasetInfoFields()
        break
      case "dataset-context":
        showFormFields(["context", "keywords"])
        break
      case "resource-general":
        showResourceFields(["name", "title", "description"])
        break
      case "resource-schema":
        showResourceFields(["schema"])
        break
      case "resource-spatial":
        showResourceFields(["spatial"])
        break
      case "resource-temporal":
        showResourceFields(["temporal"])
        break
      case "sources":
        showResourceFields(["sources"])
        break
      case "licenses":
        showResourceFields(["licenses"])
        break
      case "contributors":
        showResourceFields(["contributors"])
        break
      default:
        // Show all fields if no specific section
        window.$("#metaedit-form .je-object__container > div").show()
    }
  }

  function showDatasetInfoFields() {
    // Hide all sections first
    window.$("#metaedit-form .je-object__container > div").hide()

    // Show main dataset fields (name, title, description, @id)
    const mainFields = ["name", "title", "description", "@id"]
    mainFields.forEach((fieldName) => {
      // Try multiple selectors to find the field
      let fieldElement = window
        .$(`#metaedit-form [data-schemapath="root.${fieldName}"]`)
        .closest(".je-object__container > div")

      if (!fieldElement.length) {
        // Try alternative selector
        fieldElement = window.$(`#metaedit-form [name*="${fieldName}"]`).closest(".je-object__container > div")
      }

      if (!fieldElement.length) {
        // Try finding by label text
        fieldElement = window.$(`#metaedit-form label:contains("${fieldName}")`).closest(".je-object__container > div")
      }

      if (fieldElement.length) {
        fieldElement.show()
        console.log(`[v0] Showing field: ${fieldName}`)
      } else {
        console.log(`[v0] Could not find field: ${fieldName}`)
      }
    })

    // Also show the main container
    window.$("#metaedit-form > .je-object__container").show()
  }

  function showFormFields(fieldNames) {
    window.$("#metaedit-form .je-object__container > div").hide()

    fieldNames.forEach((fieldName) => {
      // Try multiple selectors to find the field
      let fieldElement = window
        .$(`#metaedit-form [data-schemapath="root.${fieldName}"]`)
        .closest(".je-object__container > div")

      if (!fieldElement.length) {
        fieldElement = window.$(`#metaedit-form [name*="${fieldName}"]`).closest(".je-object__container > div")
      }

      if (fieldElement.length) {
        fieldElement.show()
        console.log(`[v0] Showing field: ${fieldName}`)
      } else {
        console.log(`[v0] Could not find field: ${fieldName}`)
      }
    })
  }

  function showResourceFields(fieldNames) {
    const resourcesContainer = window
      .$('#metaedit-form [data-schemapath="root.resources"]')
      .closest(".je-object__container > div")
    if (resourcesContainer.length) {
      resourcesContainer.show()

      // Hide all resource fields first
      resourcesContainer.find(".je-object__container > div").hide()

      // Show specific resource fields
      fieldNames.forEach((fieldName) => {
        const fieldElement = resourcesContainer
          .find(`[data-schemapath*=".${fieldName}"]`)
          .closest(".je-object__container > div")
        if (fieldElement.length) {
          fieldElement.show()
        }
      })
    }
  }

  function getErrorMsg(x) {
    try {
      x = "Upload failed: " + window.JSON.parse(x.responseJSON).reason
    } catch (e) {
      x = x.statusText
    }
    return x
  }

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
    window.$("#metaedit-download").bind("click", function downloadMetadata() {
      var json = config.editor.getValue()
      convertEmptyStringsToNull(json)
      console.log(json)
      json = window.JSON.stringify(json, null, 1)
      var blob = new window.Blob([json], { type: "application/json" })
      var dataUrl = window.URL.createObjectURL(blob)
      var a = document.createElement("a")
      document.body.appendChild(a)
      a.style = "display: none"
      a.href = dataUrl
      a.download = config.table + ".metadata.json"
      a.click()
      window.URL.revokeObjectURL(dataUrl)
      a.parentNode.removeChild(a)
    })

    window.$("#metaedit-submit").bind("click", function sumbmitMetadata() {
      window.$("#metaedit-submitting").removeClass("d-none")
      var json = config.editor.getValue()
      convertEmptyStringsToNull(json)
      json = fixData(json)
      json = window.JSON.stringify(json)
      sendJson("POST", config.url_api_meta, json)
        .then(() => {
          window.location = config.url_view_table
        })
        .catch((err) => {
          window.$("#metaedit-submitting").addClass("d-none")
          alert(getErrorMsg(err))
        })
    })

    window.$("#metaedit-cancel").bind("click", function cancel() {
      window.location = config.cancle_url
    })
  }
  ;(function init() {
    window.$("#metaedit-loading").removeClass("d-none")

    // Create the sidebar layout structure
    const sidebarHTML = buildSidebar()
    const mainContentHTML = `
      <div class="main-content">
        <div class="content-header">
          <h2>Dataset Metadata</h2>
          <nav aria-label="breadcrumb">
            <ol class="breadcrumb">
              <li class="breadcrumb-item"><a href="#">Home</a></li>
              <li class="breadcrumb-item active" aria-current="page">Metadata Editor</li>
            </ol>
          </nav>
        </div>
        <div class="content-body">
          <!-- JSON Editor form will be shown/hidden here based on navigation -->
        </div>
      </div>
    `

    const containerHTML = `
      <div class="metadata-editor-container">
        ${sidebarHTML}
        ${mainContentHTML}
      </div>
    `

    window.$("#main-container").html(containerHTML)

    const existingForm = window.$("#metaedit-form")
    window.$(".main-content .content-body").append(existingForm)
    config.form = existingForm

    // Initialize sidebar navigation
    initSidebarNavigation()

    if (config.standalone == false) {
      window.$.when(window.$.getJSON(config.url_api_meta), window.$.getJSON(config.url_api_schema)).done(
        (data, schema) => {
          config.schema = fixSchema(schema[0])
          config.initialData = fixData(data[0])

          const options = {
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

          config.editor = new window.JSONEditor(config.form[0], options)

          var mainEditBox = config.form.find(".je-object__controls").first()
          mainEditBox.find(".json-editor-btntype-save").text("Apply")
          mainEditBox.find(".json-editor-btntype-copy").text("Copy to Clipboard")
          mainEditBox.find(".json-editor-btntype-cancel").text("Close")
          mainEditBox.find(".json-editor-btntype-editjson").text("Edit raw JSON")

          bindButtons()

          new window.MutationObserver((_mutationsList, _observer) => {
            // Handle dynamic content updates
          }).observe(config.form[0], { attributes: false, childList: true, subtree: true })

          window.$("#metaedit-loading").addClass("d-none")
          window.$("#metaedit-icon").removeClass("d-none")
          window.$("#metaedit-controls").removeClass("d-none")

          setTimeout(() => {
            showFormSection("dataset-info")
            console.log("[v0] Default dataset info section shown")
          }, 100)
        },
      )
    } else {
      // ... existing code for standalone mode ...
    }
  })()

  return config
}

// Global functions for resource management
window.addNewResource = () => {
  // Add new resource logic
  console.log("Adding new resource...")
  const v = config.editor.getValue();
  v.resources = v.resources || [];
  v.resources.push({ name: `resource_${v.resources.length+1}`, schema: { fields: [] }});
  config.editor.setValue(v);  // triggers re-render
  config.ui.activeResourceIndex = v.resources.length - 1;
  updateResourceList();
  showFormSection("resource-general");
}

window.showResourceForm = (index) => {
  // Show specific resource form
  console.log("Showing resource form for index:", index)
}

config.editor.on("change", () => {
  if ($(".nav-item.active").data("special") === "resource-manager") {
    updateResourceList();
  }
});
