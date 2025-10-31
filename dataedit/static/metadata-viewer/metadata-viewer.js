// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
//
// SPDX-License-Identifier: AGPL-3.0-or-later

// My idea v0´s code :)
function initMetadataViewer() {
  console.log(window.meta_api);
  const metadataViewer = document.getElementById("metadata-viewer");
  if (!metadataViewer) return;

  const metadataId = metadataViewer.dataset.metadataId;

  // First fetch the schema to get field descriptions
  fetch("/static/metaedit/schema.json")
    .then((response) => {
      if (!response.ok) {
        console.warn(
          "Could not fetch schema, proceeding without field descriptions"
        );
        return null;
      }
      return response.json();
    })
    .then((schema) => {
      // Store schema globally for use in rendering
      window.metadataSchema = schema;

      // Now fetch the actual metadata
      return fetch(window.meta_api);
    })
    .then((response) => {
      if (!response.ok) {
        throw new Error(
          `Failed to fetch metadata: ${response.status} ${response.statusText}`
        );
      }
      return response.json();
    })
    .then((metadata) => {
      renderMetadataViewer(metadata, metadataViewer);

      // Initialize tooltips after rendering
      initializeTooltips();
    })
    .catch((error) => {
      console.error("Error fetching metadata:", error);
      metadataViewer.innerHTML = `
        <div class="alert alert-danger" role="alert">
          <h4 class="alert-heading">Error loading metadata</h4>
          <p>${error.message}</p>
        </div>
      `;
    });
}

// Initialize Bootstrap tooltips
function initializeTooltips() {
  const tooltipTriggerList = document.querySelectorAll(
    '[data-bs-toggle="tooltip"]'
  );
  const tooltipList = [...tooltipTriggerList].map(
    (tooltipTriggerEl) =>
      new bootstrap.Tooltip(tooltipTriggerEl, {
        html: true,
        placement: "right",
      })
  );
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initMetadataViewer);
} else {
  initMetadataViewer();
}

// Helper function to get field description from schema
function getFieldDescription(fieldPath) {
  if (!window.metadataSchema) return null;

  try {
    // Navigate through the schema to find the field description
    const pathParts = fieldPath.split(".");
    let current = window.metadataSchema;

    for (const part of pathParts) {
      if (current.properties && current.properties[part]) {
        current = current.properties[part];
      } else if (
        current.items &&
        current.items.properties &&
        current.items.properties[part]
      ) {
        current = current.items.properties[part];
      } else {
        return null;
      }
    }

    return current.description || null;
  } catch (error) {
    console.warn(`Error getting description for ${fieldPath}:`, error);
    return null;
  }
}

// Helper function to create info icon with tooltip
function createInfoIcon(fieldPath, title) {
  const description = getFieldDescription(fieldPath);

  if (!description) return "";

  return `
    <span class="info-icon ms-1" data-bs-toggle="tooltip" data-bs-title="${description}">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-info-circle" viewBox="0 0 16 16">
        <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
        <path d="m8.93 6.588-2.29.287-.082.38.45.083c.294.07.352.176.288.469l-.738 3.468c-.194.897.105 1.319.808 1.319.545 0 1.178-.252 1.465-.598l.088-.416c-.2.176-.492.246-.686.246-.275 0-.375-.193-.304-.533L8.93 6.588zM9 4.5a1 1 0 1 1-2 0 1 1 0 0 1 2 0z"/>
      </svg>
    </span>
  `;
}

// Update the overview tab to remove metadata version and add licenses to resource summary
function renderOverviewTab(metadata) {
  let html = '<div class="row">';

  // Basic information card
  html += `
    <div class="col-md-6 mb-4">
      <div class="card metadata-card">
        <div class="card-header metadata-card-header">
          <h5 class="card-title mb-0">Dataset information</h5>
        </div>
        <div class="card-body metadata-card-body">
          <dl>
            <dt>Name ${createInfoIcon("name", "Dataset Name")}</dt>
            <dd>${metadata.name || "-"}</dd>

            <dt>Title ${createInfoIcon("title", "Dataset Title")}</dt>
            <dd>${metadata.title || "-"}</dd>

            <dt>Description ${createInfoIcon(
              "description",
              "Dataset Description"
            )}</dt>
            <dd>${metadata.description || "-"}</dd>

            <dt>Identifier ${createInfoIcon("@id", "Dataset Identifier")}</dt>
            <dd>
              ${
                metadata["@id"]
                  ? `<a href="${metadata["@id"]}" target="_blank" rel="noopener noreferrer">
                  ${metadata["@id"]}
                  <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" fill="currentColor" class="bi bi-box-arrow-up-right ms-1" viewBox="0 0 16 16">
                    <path fill-rule="evenodd" d="M8.636 3.5a.5.5 0 0 0-.5-.5H1.5A1.5 1.5 0 0 0 0 4.5v10A1.5 1.5 0 0 0 1.5 16h10a1.5 1.5 0 0 0 1.5-1.5V7.864a.5.5 0 0 0-1 0V14.5a.5.5 0 0 1-.5.5h-10a.5.5 0 0 1-.5-.5v-10a.5.5 0 0 1 .5-.5h6.636a.5.5 0 0 0 .5-.5z"/>
                    <path fill-rule="evenodd" d="M16 .5a.5.5 0 0 0-.5-.5h-5a.5.5 0 0 0 0 1h3.793L6.146 9.146a.5.5 0 1 0 .708.708L15 1.707V5.5a.5.5 0 0 0 1 0v-5z"/>
                  </svg>
                </a>`
                  : "-"
              }
            </dd>
          </dl>
        </div>
      </div>
    </div>
  `;

  // Resources summary card with licenses
  if (metadata.resources && metadata.resources.length > 0) {
    html += `
      <div class="col-md-6 mb-4">
        <div class="card metadata-card">
          <div class="card-header metadata-card-header">
            <h5 class="card-title mb-0">Resources Summary</h5>
          </div>
          <div class="card-body metadata-card-body">
            <p>This dataset contains <strong>${metadata.resources.length}</strong> resource(s).</p>
            <div class="list-group">
    `;

    metadata.resources.forEach((resource, index) => {
      html += `
        <div class="list-group-item">
          <h6 class="mb-1">${
            resource.title || resource.name || `Resource ${index + 1}`
          }</h6>
          <p class="mb-1 text-muted small">${
            resource.description
              ? resource.description.length > 150
                ? resource.description.substring(0, 150) + "..."
                : resource.description
              : "No description available"
          }</p>
      `;

      // Add licenses for each resource
      if (resource.licenses && resource.licenses.length > 0) {
        html += `<div class="mb-2"><strong class="small">Licenses:</strong> `;
        resource.licenses.forEach((license, licenseIndex) => {
          html += `
            <a href="${
              license.path
            }" target="_blank" rel="noopener noreferrer" class="badge bg-light text-dark me-1">
              ${license.name || license.title || `License ${licenseIndex + 1}`}
            </a>
          `;
        });
        html += `</div>`;
      }

      html += `
          <button class="btn btn-sm btn-link p-0 resource-details-link" data-resource-index="${index}">
            View details
          </button>
        </div>
      `;
    });

    html += `
            </div>
          </div>
        </div>
      </div>
    `;
  }

  html += "</div>"; // End of row

  return html;
}

function renderResourcesTab(metadata) {
  if (!metadata.resources || metadata.resources.length === 0) {
    return '<div class="metadata-empty">No resources available</div>';
  }

  let html = "";

  metadata.resources.forEach((resource, resourceIndex) => {
    html += `
      <div class="card metadata-card" id="resource-${resourceIndex}">
        <div class="card-header metadata-card-header">
          <h5 class="card-title mb-0">${
            resource.title || resource.name || `Resource ${resourceIndex + 1}`
          }</h5>
          <p class="mb-0 text-muted small">${resource.description || ""}</p>
        </div>
        <div class="card-body metadata-card-body">
          <div class="row mb-4">
            <div class="col-md-6">
              <h6 class="metadata-section-title">Basic Information</h6>
              <dl>
                <dt>Name ${createInfoIcon(
                  "resources.name",
                  "Resource Name"
                )}</dt>
                <dd>${resource.name || "-"}</dd>

                <dt>Path ${createInfoIcon(
                  "resources.path",
                  "Resource Path"
                )}</dt>
                <dd>
                  ${
                    resource.path
                      ? `<a href="${resource.path}" target="_blank" rel="noopener noreferrer">
                      ${resource.path}
                      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" fill="currentColor" class="bi bi-box-arrow-up-right ms-1" viewBox="0 0 16 16">
                        <path fill-rule="evenodd" d="M8.636 3.5a.5.5 0 0 0-.5-.5H1.5A1.5 1.5 0 0 0 0 4.5v10A1.5 1.5 0 0 0 1.5 16h10a1.5 1.5 0 0 0 1.5-1.5V7.864a.5.5 0 0 0-1 0V14.5a.5.5 0 0 1-.5.5h-10a.5.5 0 0 1-.5-.5v-10a.5.5 0 0 1 .5-.5h6.636a.5.5 0 0 0 .5-.5z"/>
                        <path fill-rule="evenodd" d="M16 .5a.5.5 0 0 0-.5-.5h-5a.5.5 0 0 0 0 1h3.793L6.146 9.146a.5.5 0 1 0 .708.708L15 1.707V5.5a.5.5 0 0 0 1 0v-5z"/>
                      </svg>
                    </a>`
                      : "-"
                  }
                </dd>

                <dt>Type ${createInfoIcon(
                  "resources.type",
                  "Resource Type"
                )}</dt>
                <dd>${resource.type || "-"}</dd>

                <dt>Format ${createInfoIcon(
                  "resources.format",
                  "Resource Format"
                )}</dt>
                <dd>${resource.format || "-"}</dd>

                <dt>Publication Date ${createInfoIcon(
                  "resources.publicationDate",
                  "Publication Date"
                )}</dt>
                <dd>${resource.publicationDate || "-"}</dd>

                <dt>Databus Identifier ${createInfoIcon(
                  "resources.@id",
                  "Databus Identifier"
                )}</dt>
                <dd>
                  ${
                    resource["@id"]
                      ? `<a href="${resource["@id"]}" target="_blank" rel="noopener noreferrer">
                      ${resource["@id"]}
                      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" fill="currentColor" class="bi bi-box-arrow-up-right ms-1" viewBox="0 0 16 16">
                        <path fill-rule="evenodd" d="M8.636 3.5a.5.5 0 0 0-.5-.5H1.5A1.5 1.5 0 0 0 0 4.5v10A1.5 1.5 0 0 0 1.5 16h10a1.5 1.5 0 0 0 1.5-1.5V7.864a.5.5 0 0 0-1 0V14.5a.5.5 0 0 1-.5.5h-10a.5.5 0 0 1-.5-.5v-10a.5.5 0 0 1 .5-.5h6.636a.5.5 0 0 0 .5-.5z"/>
                        <path fill-rule="evenodd" d="M16 .5a.5.5 0 0 0-.5-.5h-5a.5.5 0 0 0 0 1h3.793L6.146 9.146a.5.5 0 1 0 .708.708L15 1.707V5.5a.5.5 0 0 0 1 0v-5z"/>
                      </svg>
                    </a>`
                      : "-"
                  }
                </dd>
              </dl>
            </div>

            <div class="col-md-6">
              <h6 class="metadata-section-title">Topics & Languages</h6>
    `;

    // Topics
    if (resource.topics && resource.topics.length > 0) {
      html += `
        <div class="mb-3">
          <h6 class="small text-muted mb-2">Topics ${createInfoIcon(
            "resources.topics",
            "Topics"
          )}</h6>
          <div>
      `;

      resource.topics.forEach((topic) => {
        html += `<span class="metadata-badge metadata-badge-blue">${topic}</span> `;
      });

      html += `
          </div>
        </div>
      `;
    }

    // Languages
    if (resource.languages && resource.languages.length > 0) {
      html += `
        <div class="mb-3">
          <h6 class="small text-muted mb-2">Languages ${createInfoIcon(
            "resources.languages",
            "Languages"
          )}</h6>
          <div>
      `;

      resource.languages.forEach((lang) => {
        html += `<span class="metadata-badge metadata-badge-green">${lang}</span> `;
      });

      html += `
          </div>
        </div>
      `;
    }

    // Keywords
    if (resource.keywords && resource.keywords.length > 0) {
      html += `
        <div class="mb-3">
          <h6 class="small text-muted mb-2">Keywords ${createInfoIcon(
            "resources.keywords",
            "Keywords"
          )}</h6>
          <div>
      `;

      resource.keywords.forEach((keyword) => {
        html += `<span class="metadata-badge metadata-badge-gray">${keyword}</span> `;
      });

      html += `
          </div>
        </div>
      `;
    }

    html += `
            </div>
          </div>
    `;

    // Collapsible sections

    // Subject
    if (resource.subject && resource.subject.length > 0) {
      html += createCollapsibleSection(
        `Subject ${createInfoIcon("resources.subject", "Subject")}`,
        `resource-${resourceIndex}-subject`,
        renderSubjectContent(resource.subject)
      );
    }

    // Context
    if (resource.context) {
      html += createCollapsibleSection(
        `Context ${createInfoIcon("resources.context", "Context")}`,
        `resource-${resourceIndex}-context`,
        renderContextContent(resource.context)
      );
    }

    // Spatial
    if (resource.spatial) {
      html += createCollapsibleSection(
        `Spatial Information ${createInfoIcon(
          "resources.spatial",
          "Spatial Information"
        )}`,
        `resource-${resourceIndex}-spatial`,
        renderSpatialContent(resource.spatial)
      );
    }

    // Temporal
    if (resource.temporal) {
      html += createCollapsibleSection(
        `Temporal Information ${createInfoIcon(
          "resources.temporal",
          "Temporal Information"
        )}`,
        `resource-${resourceIndex}-temporal`,
        renderTemporalContent(resource.temporal)
      );
    }

    // Sources
    if (resource.sources && resource.sources.length > 0) {
      html += createCollapsibleSection(
        `Sources ${createInfoIcon("resources.sources", "Sources")}`,
        `resource-${resourceIndex}-sources`,
        renderSourcesContent(resource.sources)
      );
    }

    // Licenses
    if (resource.licenses && resource.licenses.length > 0) {
      html += createCollapsibleSection(
        `Licenses ${createInfoIcon("resources.licenses", "Licenses")}`,
        `resource-${resourceIndex}-licenses`,
        renderLicensesContent(resource.licenses)
      );
    }

    // Contributors
    if (resource.contributors && resource.contributors.length > 0) {
      html += createCollapsibleSection(
        `Contributors ${createInfoIcon(
          "resources.contributors",
          "Contributors"
        )}`,
        `resource-${resourceIndex}-contributors`,
        renderContributorsContent(resource.contributors)
      );
    }

    // Review
    if (resource.review) {
      html += createCollapsibleSection(
        `Review ${createInfoIcon("resources.review", "Review")}`,
        `resource-${resourceIndex}-review`,
        renderReviewContent(resource.review)
      );
    }

    html += `
        </div>
      </div>
    `;
  });

  return html;
}

// Update the schema tab (now data model) to rename Field Details and add search
function renderSchemaTab(metadata) {
  if (!metadata.resources || metadata.resources.length === 0) {
    return '<div class="metadata-empty">No data model information available</div>';
  }

  let html = "";
  let hasSchema = false;

  metadata.resources.forEach((resource, resourceIndex) => {
    if (!resource.schema) return;

    hasSchema = true;
    html += `
      <div class="card metadata-card">
        <div class="card-header metadata-card-header">
          <h5 class="card-title mb-0">${
            resource.title || resource.name || `Resource ${resourceIndex + 1}`
          } Data Model</h5>
        </div>
        <div class="card-body metadata-card-body">
    `;

    // Fields table with search
    if (resource.schema.fields && resource.schema.fields.length > 0) {
      html += `
        <h6 class="metadata-section-title">Fields ${createInfoIcon(
          "resources.schema.fields",
          "Fields"
        )}</h6>

        <div class="mb-3">
          <input type="text" id="field-search-${resourceIndex}" class="form-control" placeholder="Search fields...">
        </div>

        <div class="metadata-table-container">
          <table class="table table-striped metadata-table" id="fields-table-${resourceIndex}">
            <thead>
              <tr>
                <th>Name ${createInfoIcon(
                  "resources.schema.fields.name",
                  "Field Name"
                )}</th>
                <th>Type ${createInfoIcon(
                  "resources.schema.fields.type",
                  "Field Type"
                )}</th>
                <th>Description ${createInfoIcon(
                  "resources.schema.fields.description",
                  "Description"
                )}</th>
                <th>Nullable ${createInfoIcon(
                  "resources.schema.fields.nullable",
                  "Nullable"
                )}</th>
                <th>Unit ${createInfoIcon(
                  "resources.schema.fields.unit",
                  "Unit"
                )}</th>
              </tr>
            </thead>
            <tbody>
      `;

      resource.schema.fields.forEach((field) => {
        html += `
          <tr>
            <td>${field.name || "-"} </td>
            <td>${field.type || "-"} </td>
            <td>${field.description || "-"}</td>
            <td>${
              field.nullable !== undefined
                ? field.nullable
                  ? "Yes"
                  : "No"
                : "-"
            } </td>
            <td>${field.unit || "-"} </td>
          </tr>
        `;
      });

      html += `
            </tbody>
          </table>
        </div>
      `;

      // Primary and Foreign Keys
      html += '<div class="row mt-4">';

      // Primary Key
      if (resource.schema.primaryKey && resource.schema.primaryKey.length > 0) {
        html += `
          <div class="col-md-6 mb-4">
            <div class="card">
              <div class="card-header">
                <h6 class="card-title mb-0">Primary Key ${createInfoIcon(
                  "resources.schema.primaryKey",
                  "Primary Key"
                )}</h6>
              </div>
              <div class="card-body">
                <div>
        `;

        resource.schema.primaryKey.forEach((key) => {
          html += `<span class="metadata-badge metadata-badge-blue">${key}</span> `;
        });

        html += `
                </div>
              </div>
            </div>
          </div>
        `;
      }

      // Foreign Keys
      if (
        resource.schema.foreignKeys &&
        resource.schema.foreignKeys.length > 0
      ) {
        html += `
          <div class="col-md-6 mb-4">
            <div class="card">
              <div class="card-header">
                <h6 class="card-title mb-0">Foreign Keys ${createInfoIcon(
                  "resources.schema.foreignKeys",
                  "Foreign Keys"
                )}</h6>
              </div>
              <div class="card-body">
                <div class="list-group list-group-flush">
        `;

        resource.schema.foreignKeys.forEach((fk) => {
          html += `
            <div class="list-group-item px-0">
              <div><strong>Fields:</strong> ${fk.fields.join(", ")}</div>
              <div><strong>References:</strong> ${
                fk.reference.resource
              } (${fk.reference.fields.join(", ")})</div>
            </div>
          `;
        });

        html += `
                </div>
              </div>
            </div>
          </div>
        `;
      }

      html += "</div>"; // End of row

      // Dialect
      if (resource.dialect) {
        html += `
          <div class="card mt-4">
            <div class="card-header">
              <h6 class="card-title mb-0">Dialect ${createInfoIcon(
                "resources.dialect",
                "Dialect"
              )}</h6>
            </div>
            <div class="card-body">
              <dl class="row">
        `;

        Object.entries(resource.dialect).forEach(([key, value]) => {
          html += `
            <dt class="col-sm-3">${
              key.charAt(0).toUpperCase() + key.slice(1)
            } ${createInfoIcon(`resources.dialect.${key}`, key)}</dt>
            <dd class="col-sm-9">${value}</dd>
          `;
        });

        html += `
              </dl>
            </div>
          </div>
        `;
      }

      // Renamed from Field Details to Ontological Data Annotation
      html += `
        <h6 class="metadata-section-title mt-4">Ontological Data Annotation</h6>
        <div class="accordion" id="fieldAccordion-${resourceIndex}">
      `;

      resource.schema.fields.forEach((field, fieldIndex) => {
        html += `
          <div class="accordion-item field-item" data-field-name="${
            field.name?.toLowerCase() || ""
          }">
            <h2 class="accordion-header" id="fieldHeading-${resourceIndex}-${fieldIndex}">
              <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#fieldCollapse-${resourceIndex}-${fieldIndex}" aria-expanded="false" aria-controls="fieldCollapse-${resourceIndex}-${fieldIndex}">
                ${field.name}
              </button>
            </h2>
            <div id="fieldCollapse-${resourceIndex}-${fieldIndex}" class="accordion-collapse collapse" aria-labelledby="fieldHeading-${resourceIndex}-${fieldIndex}" data-bs-parent="#fieldAccordion-${resourceIndex}">
              <div class="accordion-body">
                <p>${field.description || "No description"}</p>

                <div class="row mb-3">
                  <div class="col-md-4">
                    <strong>Type ${createInfoIcon(
                      "resources.schema.fields.type",
                      "Field Type"
                    )}:</strong> ${field.type || "-"}
                  </div>
                  <div class="col-md-4">
                    <strong>Nullable ${createInfoIcon(
                      "resources.schema.fields.nullable",
                      "Nullable"
                    )}:</strong> ${
                      field.nullable !== undefined
                        ? field.nullable
                          ? "Yes"
                          : "No"
                        : "-"
                    }
                  </div>
                  <div class="col-md-4">
                    <strong>Unit ${createInfoIcon(
                      "resources.schema.fields.unit",
                      "Unit"
                    )}:</strong> ${field.unit || "-"}
                  </div>
                </div>
        `;

        // Is About
        if (field.isAbout && field.isAbout.length > 0) {
          html += `
            <div class="mb-3">
              <h6 class="small text-muted mb-2">Is About ${createInfoIcon(
                "resources.schema.fields.isAbout",
                "Is About"
              )}</h6>
              <div class="list-group">
          `;

          field.isAbout.forEach((about) => {
            html += `
              <div class="list-group-item">
                <div>${about.name || "-"}</div>
                ${
                  about["@id"]
                    ? `<a href="${about["@id"]}" target="_blank" rel="noopener noreferrer" class="small">
                    ${about["@id"]}
                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" fill="currentColor" class="bi bi-box-arrow-up-right ms-1" viewBox="0 0 16 16">
                      <path fill-rule="evenodd" d="M8.636 3.5a.5.5 0 0 0-.5-.5H1.5A1.5 1.5 0 0 0 0 4.5v10A1.5 1.5 0 0 0 1.5 16h10a1.5 1.5 0 0 0 1.5-1.5V7.864a.5.5 0 0 0-1 0V14.5a.5.5 0 0 1-.5.5h-10a.5.5 0 0 1-.5-.5v-10a.5.5 0 0 1 .5-.5h6.636a.5.5 0 0 0 .5-.5z"/>
                      <path fill-rule="evenodd" d="M16 .5a.5.5 0 0 0-.5-.5h-5a.5.5 0 0 0 0 1h3.793L6.146 9.146a.5.5 0 1 0 .708.708L15 1.707V5.5a.5.5 0 0 0 1 0v-5z"/>
                    </svg>
                  </a>`
                    : ""
                }
              </div>
            `;
          });

          html += `
              </div>
            </div>
          `;
        }

        // Value Reference
        if (
          field.valueReference &&
          field.valueReference.length > 0 &&
          field.valueReference.some(
            (ref) => ref.value || ref.name || ref["@id"]
          )
        ) {
          html += `
            <div class="mb-3">
              <h6 class="small text-muted mb-2">Value References ${createInfoIcon(
                "resources.schema.fields.valueReference",
                "Value References"
              )}</h6>
              <div class="list-group">
          `;

          field.valueReference
            .filter((ref) => ref.value || ref.name || ref["@id"])
            .forEach((ref) => {
              html += `
                <div class="list-group-item">
                  ${
                    ref.value
                      ? `<div><strong>Value:</strong> ${ref.value}</div>`
                      : ""
                  }
                  ${
                    ref.name
                      ? `<div><strong>Name:</strong> ${ref.name}</div>`
                      : ""
                  }
                  ${
                    ref["@id"]
                      ? `<a href="${ref["@id"]}" target="_blank" rel="noopener noreferrer" class="small">
                      ${ref["@id"]}
                      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" fill="currentColor" class="bi bi-box-arrow-up-right ms-1" viewBox="0 0 16 16">
                        <path fill-rule="evenodd" d="M8.636 3.5a.5.5 0 0 0-.5-.5H1.5A1.5 1.5 0 0 0 0 4.5v10A1.5 1.5 0 0 0 1.5 16h10a1.5 1.5 0 0 0 1.5-1.5V7.864a.5.5 0 0 0-1 0V14.5a.5.5 0 0 1-.5.5h-10a.5.5 0 0 1-.5-.5v-10a.5.5 0 0 1 .5-.5h6.636a.5.5 0 0 0 .5-.5z"/>
                        <path fill-rule="evenodd" d="M16 .5a.5.5 0 0 0-.5-.5h-5a.5.5 0 0 0 0 1h3.793L6.146 9.146a.5.5 0 1 0 .708.708L15 1.707V5.5a.5.5 0 0 0 1 0v-5z"/>
                      </svg>
                    </a>`
                      : ""
                  }
                </div>
              `;
            });

          html += `
              </div>
            </div>
          `;
        }

        html += `
              </div>
            </div>
          </div>
        `;
      });

      html += `
        </div>
      `;
    }

    html += `
        </div>
      </div>
    `;
  });

  if (!hasSchema) {
    return '<div class="metadata-empty">No data model information available</div>';
  }

  return html;
}

// Update the metadata tab (formerly meta metadata) to include the metadata version
function renderMetadataTab(metadata) {
  if (!metadata.metaMetadata) {
    return '<div class="metadata-empty">No metadata version information available</div>';
  }

  let html = `
    <div class="card metadata-card">
      <div class="card-header metadata-card-header">
        <h5 class="card-title mb-0">Metadata Version Information</h5>
      </div>
      <div class="card-body metadata-card-body">
        <div class="d-flex align-items-center mb-4">
          <div class="bg-info bg-opacity-10 p-3 rounded-circle me-3">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-info text-info" viewBox="0 0 16 16">
              <path d="m8.93 6.588-2.29.287-.082.38.45.083c.294.07.352.176.288.469l-.738 3.468c-.194.897.105 1.319.808 1.319.545 0 1.178-.252 1.465-.598l.088-.416c-.2.176-.492.246-.686.246-.275 0-.375-.193-.304-.533L8.93 6.588zM9 4.5a1 1 0 1 1-2 0 1 1 0 0 1 2 0z"/>
            </svg>
          </div>
          <div>
            <p class="mb-1">This dataset uses OEMetadata version <strong>${
              metadata.metaMetadata.metadataVersion || "Unknown"
            }</strong></p>
          </div>
        </div>

        <dl class="row">
  `;

  if (metadata.metaMetadata.metadataLicense) {
    html += `
          <dt class="col-sm-3">Metadata License ${createInfoIcon(
            "metaMetadata.metadataLicense",
            "Metadata License"
          )}</dt>
          <dd class="col-sm-9">
            <div class="card">
              <div class="card-body">
                <h6 class="card-subtitle mb-2">${
                  metadata.metaMetadata.metadataLicense.title || "-"
                }</h6>
                <a href="${
                  metadata.metaMetadata.metadataLicense.path
                }" target="_blank" rel="noopener noreferrer" class="card-link">
                  ${metadata.metaMetadata.metadataLicense.name || "-"}
                  <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" fill="currentColor" class="bi bi-box-arrow-up-right ms-1" viewBox="0 0 16 16">
                    <path fill-rule="evenodd" d="M8.636 3.5a.5.5 0 0 0-.5-.5H1.5A1.5 1.5 0 0 0 0 4.5v10A1.5 1.5 0 0 0 1.5 16h10a1.5 1.5 0 0 0 1.5-1.5V7.864a.5.5 0 0 0-1 0V14.5a.5.5 0 0 1-.5.5h-10a.5.5 0 0 1-.5-.5v-10a.5.5 0 0 1 .5-.5h6.636a.5.5 0 0 0 .5-.5z"/>
                    <path fill-rule="evenodd" d="M16 .5a.5.5 0 0 0-.5-.5h-5a.5.5 0 0 0 0 1h3.793L6.146 9.146a.5.5 0 1 0 .708.708L15 1.707V5.5a.5.5 0 0 0 1 0v-5z"/>
                  </svg>
                </a>
              </div>
            </div>
          </dd>
    `;
  }

  // Add any other meta metadata properties
  Object.entries(metadata.metaMetadata).forEach(([key, value]) => {
    if (key !== "metadataVersion" && key !== "metadataLicense") {
      html += `
        <dt class="col-sm-3">${
          key.charAt(0).toUpperCase() + key.slice(1)
        } ${createInfoIcon(`metaMetadata.${key}`, key)}</dt>
        <dd class="col-sm-9">
          ${typeof value === "object" ? JSON.stringify(value, null, 2) : value}
        </dd>
      `;
    }
  });

  html += `
        </dl>
      </div>
    </div>
  `;

  return html;
}

// Add event listener setup for field search
document.addEventListener("DOMContentLoaded", () => {
  // Original event listener code...

  // After rendering the metadata viewer, set up the field search functionality
  document.querySelectorAll('[id^="field-search-"]').forEach((searchInput) => {
    searchInput.addEventListener("input", function () {
      const resourceIndex = this.id.split("-")[2];
      const searchTerm = this.value.toLowerCase();

      // Filter table rows
      const tableRows = document.querySelectorAll(
        `#fields-table-${resourceIndex} tbody tr`
      );
      tableRows.forEach((row) => {
        const text = row.textContent.toLowerCase();
        if (text.includes(searchTerm)) {
          row.style.display = "";
        } else {
          row.style.display = "none";
        }
      });

      // Filter accordion items
      const fieldItems = document.querySelectorAll(
        `#fieldAccordion-${resourceIndex} .field-item`
      );
      fieldItems.forEach((item) => {
        const fieldName = item.dataset.fieldName;
        if (fieldName && fieldName.includes(searchTerm)) {
          item.style.display = "";
        } else {
          item.style.display = "none";
        }
      });
    });
  });
});

// Helper functions for rendering collapsible sections
function createCollapsibleSection(title, id, contentHTML) {
  return `
    <div class="metadata-collapsible mb-3">
      <div class="metadata-collapsible-header" id="${id}-header">
        <span>${title}</span>
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-chevron-right chevron-icon" viewBox="0 0 16 16">
          <path fill-rule="evenodd" d="M4.646 1.646a.5.5 0 0 1 .708 0l6 6a.5.5 0 0 1 0 .708l-6 6a.5.5 0 0 1-.708-.708L10.293 8 4.646 2.354a.5.5 0 0 1 0-.708z"/>
        </svg>
      </div>
      <div class="metadata-collapsible-content" id="${id}-content" style="display: none;">
        ${contentHTML}
      </div>
    </div>
  `;
}

function renderSubjectContent(subjects) {
  let html = '<div class="list-group">';

  subjects.forEach((subject) => {
    html += `
      <div class="list-group-item">
        <div class="fw-bold">${subject.name || "-"} ${createInfoIcon(
          "resources.subject.name",
          "Subject Name"
        )}</div>
        ${
          subject["@id"]
            ? `<a href="${subject["@id"]}" target="_blank" rel="noopener noreferrer" class="small">
            ${subject["@id"]}
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" fill="currentColor" class="bi bi-box-arrow-up-right ms-1" viewBox="0 0 16 16">
              <path fill-rule="evenodd" d="M8.636 3.5a.5.5 0 0 0-.5-.5H1.5A1.5 1.5 0 0 0 0 4.5v10A1.5 1.5 0 0 0 1.5 16h10a1.5 1.5 0 0 0 1.5-1.5V7.864a.5.5 0 0 0-1 0V14.5a.5.5 0 0 1-.5.5h-10a.5.5 0 0 1-.5-.5v-10a.5.5 0 0 1 .5-.5h6.636a.5.5 0 0 0 .5-.5z"/>
              <path fill-rule="evenodd" d="M16 .5a.5.5 0 0 0-.5-.5h-5a.5.5 0 0 0 0 1h3.793L6.146 9.146a.5.5 0 1 0 .708.708L15 1.707V5.5a.5.5 0 0 0 1 0v-5z"/>
            </svg>
          </a>`
            : ""
        }
      </div>
    `;
  });

  html += "</div>";
  return html;
}

function renderContextContent(context) {
  let html = '<dl class="row">';

  Object.entries(context).forEach(([key, value]) => {
    html += `
      <dt class="col-sm-3">${
        key.charAt(0).toUpperCase() + key.slice(1)
      } ${createInfoIcon(`resources.context.${key}`, key)}</dt>
      <dd class="col-sm-9">
        ${
          typeof value === "string" && value.startsWith("http")
            ? `<a href="${value}" target="_blank" rel="noopener noreferrer">
            ${value}
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" fill="currentColor" class="bi bi-box-arrow-up-right ms-1" viewBox="0 0 16 16">
              <path fill-rule="evenodd" d="M8.636 3.5a.5.5 0 0 0-.5-.5H1.5A1.5 1.5 0 0 0 0 4.5v10A1.5 1.5 0 0 0 1.5 16h10a1.5 1.5 0 0 0 1.5-1.5V7.864a.5.5 0 0 0-1 0V14.5a.5.5 0 0 1-.5.5h-10a.5.5 0 0 1-.5-.5v-10a.5.5 0 0 1 .5-.5h6.636a.5.5 0 0 0 .5-.5z"/>
              <path fill-rule="evenodd" d="M16 .5a.5.5 0 0 0-.5-.5h-5a.5.5 0 0 0 0 1h3.793L6.146 9.146a.5.5 0 1 0 .708.708L15 1.707V5.5a.5.5 0 0 0 1 0v-5z"/>
            </svg>
          </a>`
            : value
        }
      </dd>
    `;
  });

  html += "</dl>";
  return html;
}

function renderSpatialContent(spatial) {
  let html = "";

  if (spatial.location) {
    html += `
      <div class="mb-4">
        <h6 class="fw-bold mb-2">Location ${createInfoIcon(
          "resources.spatial.location",
          "Location"
        )}</h6>
        <dl class="row">
    `;

    Object.entries(spatial.location).forEach(([key, value]) => {
      html += `
        <dt class="col-sm-3">${
          key.charAt(0).toUpperCase() + key.slice(1)
        } ${createInfoIcon(`resources.spatial.location.${key}`, key)}</dt>
        <dd class="col-sm-9">
          ${
            typeof value === "string" && value.startsWith("http")
              ? `<a href="${value}" target="_blank" rel="noopener noreferrer">
              ${value}
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" fill="currentColor" class="bi bi-box-arrow-up-right ms-1" viewBox="0 0 16 16">
                <path fill-rule="evenodd" d="M8.636 3.5a.5.5 0 0 0-.5-.5H1.5A1.5 1.5 0 0 0 0 4.5v10A1.5 1.5 0 0 0 1.5 16h10a1.5 1.5 0 0 0 1.5-1.5V7.864a.5.5 0 0 0-1 0V14.5a.5.5 0 0 1-.5.5h-10a.5.5 0 0 1-.5-.5v-10a.5.5 0 0 1 .5-.5h6.636a.5.5 0 0 0 .5-.5z"/>
                <path fill-rule="evenodd" d="M16 .5a.5.5 0 0 0-.5-.5h-5a.5.5 0 0 0 0 1h3.793L6.146 9.146a.5.5 0 1 0 .708.708L15 1.707V5.5a.5.5 0 0 0 1 0v-5z"/>
              </svg>
            </a>`
              : value
          }
        </dd>
      `;
    });

    html += `
        </dl>
      </div>
    `;
  }

  if (spatial.extent) {
    html += `
      <div>
        <h6 class="fw-bold mb-2">Extent ${createInfoIcon(
          "resources.spatial.extent",
          "Extent"
        )}</h6>
        <dl class="row">
    `;

    Object.entries(spatial.extent)
      .filter(([key]) => key !== "boundingBox")
      .forEach(([key, value]) => {
        html += `
          <dt class="col-sm-3">${
            key.charAt(0).toUpperCase() + key.slice(1)
          } ${createInfoIcon(`resources.spatial.extent.${key}`, key)}</dt>
          <dd class="col-sm-9">
            ${
              typeof value === "string" && value.startsWith("http")
                ? `<a href="${value}" target="_blank" rel="noopener noreferrer">
                ${value}
                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" fill="currentColor" class="bi bi-box-arrow-up-right ms-1" viewBox="0 0 16 16">
                  <path fill-rule="evenodd" d="M8.636 3.5a.5.5 0 0 0-.5-.5H1.5A1.5 1.5 0 0 0 0 4.5v10A1.5 1.5 0 0 0 1.5 16h10a1.5 1.5 0 0 0 1.5-1.5V7.864a.5.5 0 0 0-1 0V14.5a.5.5 0 0 1-.5.5h-10a.5.5 0 0 1-.5-.5v-10a.5.5 0 0 1 .5-.5h6.636a.5.5 0 0 0 .5-.5z"/>
                  <path fill-rule="evenodd" d="M16 .5a.5.5 0 0 0-.5-.5h-5a.5.5 0 0 0 0 1h3.793L6.146 9.146a.5.5 0 1 0 .708.708L15 1.707V5.5a.5.5 0 0 0 1 0v-5z"/>
                </svg>
              </a>`
                : value
            }
          </dd>
        `;
      });

    html += `
        </dl>
    `;

    if (spatial.extent.boundingBox) {
      html += `
        <div class="mt-3">
          <h6 class="small text-muted mb-2">Bounding Box ${createInfoIcon(
            "resources.spatial.extent.boundingBox",
            "Bounding Box"
          )}</h6>
          <div class="p-2 bg-light rounded">
            <code>[${spatial.extent.boundingBox.join(", ")}]</code>
          </div>
        </div>
      `;
    }

    html += `</div>`;
  }

  return html;
}

function renderTemporalContent(temporal) {
  let html = "";

  if (temporal.referenceDate) {
    html += `
      <div class="mb-4">
        <h6 class="small text-muted mb-2">Reference Date ${createInfoIcon(
          "resources.temporal.referenceDate",
          "Reference Date"
        )}</h6>
        <p>${temporal.referenceDate}</p>
      </div>
    `;
  }

  if (temporal.timeseries && temporal.timeseries.length > 0) {
    html += `
      <div>
        <h6 class="small text-muted mb-2">Time Series ${createInfoIcon(
          "resources.temporal.timeseries",
          "Time Series"
        )}</h6>
        <div class="list-group">
    `;

    temporal.timeseries.forEach((series) => {
      html += `
        <div class="list-group-item">
          <dl class="row mb-0">
      `;

      Object.entries(series).forEach(([key, value]) => {
        html += `
          <dt class="col-sm-3">${
            key.charAt(0).toUpperCase() + key.slice(1)
          } ${createInfoIcon(`resources.temporal.timeseries.${key}`, key)}</dt>
          <dd class="col-sm-9">${value}</dd>
        `;
      });

      html += `
          </dl>
        </div>
      `;
    });

    html += `
        </div>
      </div>
    `;
  }

  return html;
}

function renderSourcesContent(sources) {
  let html = '<div class="list-group">';

  sources.forEach((source) => {
    html += `
      <div class="list-group-item">
        <h6 class="mb-2">${source.title || "-"} ${createInfoIcon(
          "resources.sources.title",
          "Source Title"
        )}</h6>
        <p class="small text-muted mb-3">${source.description || "-"}</p>

        <div class="row mb-3">
          <div class="col-md-6">
            <strong>Publication Year ${createInfoIcon(
              "resources.sources.publicationYear",
              "Publication Year"
            )}:</strong> ${source.publicationYear || "-"}
          </div>
          <div class="col-md-6">
            <strong>Path ${createInfoIcon(
              "resources.sources.path",
              "Path"
            )}:</strong>
            ${
              source.path
                ? `<a href="${source.path}" target="_blank" rel="noopener noreferrer">
                ${source.path}
                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" fill="currentColor" class="bi bi-box-arrow-up-right ms-1" viewBox="0 0 16 16">
                  <path fill-rule="evenodd" d="M8.636 3.5a.5.5 0 0 0-.5-.5H1.5A1.5 1.5 0 0 0 0 4.5v10A1.5 1.5 0 0 0 1.5 16h10a1.5 1.5 0 0 0 1.5-1.5V7.864a.5.5 0 0 0-1 0V14.5a.5.5 0 0 1-.5.5h-10a.5.5 0 0 1-.5-.5v-10a.5.5 0 0 1 .5-.5h6.636a.5.5 0 0 0 .5-.5z"/>
                  <path fill-rule="evenodd" d="M16 .5a.5.5 0 0 0-.5-.5h-5a.5.5 0 0 0 0 1h3.793L6.146 9.146a.5.5 0 1 0 .708.708L15 1.707V5.5a.5.5 0 0 0 1 0v-5z"/>
                </svg>
              </a>`
                : "-"
            }
          </div>
        </div>
    `;

    if (source.authors && source.authors.length > 0) {
      html += `
        <div class="mb-3">
          <h6 class="small text-muted mb-2">Authors ${createInfoIcon(
            "resources.sources.authors",
            "Authors"
          )}</h6>
          <div>
      `;

      source.authors.forEach((author) => {
        html += `<span class="metadata-badge metadata-badge-gray">${author}</span> `;
      });

      html += `
          </div>
        </div>
      `;
    }

    if (source.sourceLicenses && source.sourceLicenses.length > 0) {
      html += `
        <div>
          <h6 class="small text-muted mb-2">Licenses ${createInfoIcon(
            "resources.sources.sourceLicenses",
            "Source Licenses"
          )}</h6>
          <div class="list-group">
      `;

      source.sourceLicenses.forEach((license) => {
        html += `
          <div class="list-group-item">
            <div class="fw-bold">${license.title || "-"} ${createInfoIcon(
              "resources.sources.sourceLicenses.title",
              "License Title"
            )}</div>
            <a href="${
              license.path
            }" target="_blank" rel="noopener noreferrer" class="small">
              ${license.name || "-"}
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" fill="currentColor" class="bi bi-box-arrow-up-right ms-1" viewBox="0 0 16 16">
                <path fill-rule="evenodd" d="M8.636 3.5a.5.5 0 0 0-.5-.5H1.5A1.5 1.5 0 0 0 0 4.5v10A1.5 1.5 0 0 0 1.5 16h10a1.5 1.5 0 0 0 1.5-1.5V7.864a.5.5 0 0 0-1 0V14.5a.5.5 0 0 1-.5.5h-10a.5.5 0 0 1-.5-.5v-10a.5.5 0 0 1 .5-.5h6.636a.5.5 0 0 0 .5-.5z"/>
                <path fill-rule="evenodd" d="M16 .5a.5.5 0 0 0-.5-.5h-5a.5.5 0 0 0 0 1h3.793L6.146 9.146a.5.5 0 1 0 .708.708L15 1.707V5.5a.5.5 0 0 0 1 0v-5z"/>
              </svg>
            </a>
            ${
              license.instruction
                ? `<p class="small mt-2">${license.instruction}</p>`
                : ""
            }
            ${
              license.attribution
                ? `<p class="small text-muted">Attribution: ${license.attribution}</p>`
                : ""
            }
          </div>
        `;
      });

      html += `
          </div>
        </div>
      `;
    }

    html += "</div>";
  });

  html += "</div>";
  return html;
}

function renderLicensesContent(licenses) {
  let html = '<div class="list-group">';

  licenses.forEach((license) => {
    html += `
      <div class="list-group-item">
        <h6 class="mb-2">${license.title || "-"} ${createInfoIcon(
          "resources.licenses.title",
          "License Title"
        )}</h6>
        <a href="${
          license.path
        }" target="_blank" rel="noopener noreferrer" class="small">
          ${license.name || "-"}
          <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" fill="currentColor" class="bi bi-box-arrow-up-right ms-1" viewBox="0 0 16 16">
            <path fill-rule="evenodd" d="M8.636 3.5a.5.5 0 0 0-.5-.5H1.5A1.5 1.5 0 0 0 0 4.5v10A1.5 1.5 0 0 0 1.5 16h10a1.5 1.5 0 0 0 1.5-1.5V7.864a.5.5 0 0 0-1 0V14.5a.5.5 0 0 1-.5.5h-10a.5.5 0 0 1-.5-.5v-10a.5.5 0 0 1 .5-.5h6.636a.5.5 0 0 0 .5-.5z"/>
            <path fill-rule="evenodd" d="M16 .5a.5.5 0 0 0-.5-.5h-5a.5.5 0 0 0 0 1h3.793L6.146 9.146a.5.5 0 1 0 .708.708L15 1.707V5.5a.5.5 0 0 0 1 0v-5z"/>
          </svg>
        </a>
        ${
          license.instruction
            ? `<p class="small mt-2">${license.instruction}</p>`
            : ""
        }
        ${
          license.attribution
            ? `<p class="small text-muted">Attribution: ${license.attribution}</p>`
            : ""
        }
        ${
          license.copyrightStatement
            ? `<p class="small text-muted">
            Copyright:
            <a href="${license.copyrightStatement}" target="_blank" rel="noopener noreferrer">
              ${license.copyrightStatement}
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" fill="currentColor" class="bi bi-box-arrow-up-right ms-1" viewBox="0 0 16 16">
                <path fill-rule="evenodd" d="M8.636 3.5a.5.5 0 0 0-.5-.5H1.5A1.5 1.5 0 0 0 0 4.5v10A1.5 1.5 0 0 0 1.5 16h10a1.5 1.5 0 0 0 1.5-1.5V7.864a.5.5 0 0 0-1 0V14.5a.5.5 0 0 1-.5.5h-10a.5.5 0 0 1-.5-.5v-10a.5.5 0 0 1 .5-.5h6.636a.5.5 0 0 0 .5-.5z"/>
                <path fill-rule="evenodd" d="M16 .5a.5.5 0 0 0-.5-.5h-5a.5.5 0 0 0 0 1h3.793L6.146 9.146a.5.5 0 1 0 .708.708L15 1.707V5.5a.5.5 0 0 0 1 0v-5z"/>
              </svg>
            </a>
          </p>`
            : ""
        }
      </div>
    `;
  });

  html += "</div>";
  return html;
}

function renderContributorsContent(contributors) {
  let html = '<div class="list-group">';

  contributors.forEach((contributor) => {
    html += `
      <div class="list-group-item">
        <div class="d-flex justify-content-between align-items-center mb-2">
          <h6 class="mb-0">${contributor.title || "-"} ${createInfoIcon(
            "resources.contributors.title",
            "Contributor Title"
          )}</h6>
          <span class="metadata-badge metadata-badge-blue">${
            contributor.organization || "-"
          }</span>
        </div>

        <div class="row mb-3">
          ${
            contributor.path
              ? `
            <div class="col-md-6">
              <strong>Path ${createInfoIcon(
                "resources.contributors.path",
                "Path"
              )}:</strong>
              <a href="${
                contributor.path
              }" target="_blank" rel="noopener noreferrer" class="small">
                ${contributor.path}
                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" fill="currentColor" class="bi bi-box-arrow-up-right ms-1" viewBox="0 0 16 16">
                  <path fill-rule="evenodd" d="M8.636 3.5a.5.5 0 0 0-.5-.5H1.5A1.5 1.5 0 0 0 0 4.5v10A1.5 1.5 0 0 0 1.5 16h10a1.5 1.5 0 0 0 1.5-1.5V7.864a.5.5 0 0 0-1 0V14.5a.5.5 0 0 1-.5.5h-10a.5.5 0 0 1-.5-.5v-10a.5.5 0 0 1 .5-.5h6.636a.5.5 0 0 0 .5-.5z"/>
                  <path fill-rule="evenodd" d="M16 .5a.5.5 0 0 0-.5-.5h-5a.5.5 0 0 0 0 1h3.793L6.146 9.146a.5.5 0 1 0 .708.708L15 1.707V5.5a.5.5 0 0 0 1 0v-5z"/>
                </svg>
              </a>
            </div>
          `
              : ""
          }

          ${
            contributor.date
              ? `
            <div class="col-md-6">
              <strong>Date ${createInfoIcon(
                "resources.contributors.date",
                "Date"
              )}:</strong> ${contributor.date}
            </div>
          `
              : ""
          }

          ${
            contributor.object
              ? `
            <div class="col-md-6">
              <strong>Object ${createInfoIcon(
                "resources.contributors.object",
                "Object"
              )}:</strong> ${contributor.object}
            </div>
          `
              : ""
          }
        </div>
    `;

    if (contributor.roles && contributor.roles.length > 0) {
      html += `
        <div class="mb-3">
          <h6 class="small text-muted mb-2">Roles ${createInfoIcon(
            "resources.contributors.roles",
            "Roles"
          )}</h6>
          <div>
      `;

      contributor.roles.forEach((role) => {
        html += `<span class="metadata-badge metadata-badge-gray">${role}</span> `;
      });

      html += `
          </div>
        </div>
      `;
    }

    if (contributor.comment) {
      html += `<p class="small text-muted">${contributor.comment}</p>`;
    }

    html += "</div>";
  });

  html += "</div>";
  return html;
}

function renderReviewContent(review) {
  let html = '<dl class="row">';

  Object.entries(review).forEach(([key, value]) => {
    html += `
      <dt class="col-sm-3">${
        key.charAt(0).toUpperCase() + key.slice(1)
      } ${createInfoIcon(`resources.review.${key}`, key)}</dt>
      <dd class="col-sm-9">
        ${
          typeof value === "string" && value.startsWith("http")
            ? `<a href="${value}" target="_blank" rel="noopener noreferrer">
            ${value}
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" fill="currentColor" class="bi bi-box-arrow-up-right ms-1" viewBox="0 0 16 16">
              <path fill-rule="evenodd" d="M8.636 3.5a.5.5 0 0 0-.5-.5H1.5A1.5 1.5 0 0 0 0 4.5v10A1.5 1.5 0 0 0 1.5 16h10a1.5 1.5 0 0 0 1.5-1.5V7.864a.5.5 0 0 0-1 0V14.5a.5.5 0 0 1-.5.5h-10a.5.5 0 0 1-.5-.5v-10a.5.5 0 0 1 .5-.5h6.636a.5.5 0 0 0 .5-.5z"/>
              <path fill-rule="evenodd" d="M16 .5a.5.5 0 0 0-.5-.5h-5a.5.5 0 0 0 0 1h3.793L6.146 9.146a.5.5 0 1 0 .708.708L15 1.707V5.5a.5.5 0 0 0 1 0v-5z"/>
            </svg>
          </a>`
            : value
        }
      </dd>
    `;
  });

  html += "</dl>";
  return html;
}

// Main function to render the metadata viewer
function renderMetadataViewer(metadata, container) {
  // Create the main container
  const html = `
    <div class="metadata-container">
      <!-- Header with title and download button -->
      <div class="d-flex justify-content-between align-items-center metadata-header">
        <h1>Dataset: ${
          metadata.title || metadata.name || "Metadata Specification"
        }</h1>
        <!--
        <button id="download-json" class="btn btn-primary">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-download me-2" viewBox="0 0 16 16">
            <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/>
            <path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"/>
          </svg>
          Download JSON
        </button>
        -->
      </div>

      <!-- Tabs -->
      <ul class="nav nav-tabs mb-4" id="metadataTabs" role="tablist">
        <li class="nav-item" role="presentation">
          <button class="nav-link active" id="overview-tab" data-bs-toggle="tab" data-bs-target="#overview" type="button" role="tab" aria-controls="overview" aria-selected="true">Overview</button>
        </li>
        <li class="nav-item" role="presentation">
          <button class="nav-link" id="resources-tab" data-bs-toggle="tab" data-bs-target="#resources" type="button" role="tab" aria-controls="resources" aria-selected="false">Resources</button>
        </li>
        <li class="nav-item" role="presentation">
          <button class="nav-link" id="schema-tab" data-bs-toggle="tab" data-bs-target="#schema" type="button" role="tab" aria-controls="schema" aria-selected="false">Data Model</button>
        </li>
        <li class="nav-item" role="presentation">
          <button class="nav-link" id="metameta-tab" data-bs-toggle="tab" data-bs-target="#metameta" type="button" role="tab" aria-controls="metameta" aria-selected="false">Metadata Version</button>
        </li>
      </ul>

      <!-- Tab content -->
      <div class="tab-content" id="metadataTabsContent">
        <!-- Overview tab -->
        <div class="tab-pane fade show active" id="overview" role="tabpanel" aria-labelledby="overview-tab">
          ${renderOverviewTab(metadata)}
        </div>

        <!-- Resources tab -->
        <div class="tab-pane fade" id="resources" role="tabpanel" aria-labelledby="resources-tab">
          ${renderResourcesTab(metadata)}
        </div>

        <!-- Data Model tab (formerly Schema) -->
        <div class="tab-pane fade" id="schema" role="tabpanel" aria-labelledby="schema-tab">
          ${renderSchemaTab(metadata)}
        </div>

        <!-- Metadata Version tab (formerly Meta Metadata) -->
        <div class="tab-pane fade" id="metameta" role="tabpanel" aria-labelledby="metameta-tab">
          ${renderMetadataTab(metadata)}
        </div>
      </div>
    </div>
  `;

  // Set the HTML content
  container.innerHTML = html;

  // Add event listener for download button
  // document.getElementById("download-json").addEventListener("click", () => {
  //   downloadJson(metadata)
  // })

  // Add event listeners for collapsible sections
  setupCollapsibleSections();

  // Add event listeners for resource detail links
  setupResourceDetailLinks();
}

function downloadJson(metadata) {
  const dataStr = JSON.stringify(metadata, null, 2);
  const dataUri = `data:application/json;charset=utf-8,${encodeURIComponent(
    dataStr
  )}`;

  const downloadAnchorNode = document.createElement("a");
  downloadAnchorNode.setAttribute("href", dataUri);
  downloadAnchorNode.setAttribute(
    "download",
    `${metadata.name || "metadata"}.json`
  );
  document.body.appendChild(downloadAnchorNode);
  downloadAnchorNode.click();
  downloadAnchorNode.remove();
}

function setupCollapsibleSections() {
  document
    .querySelectorAll(".metadata-collapsible-header")
    .forEach((header) => {
      header.addEventListener("click", function () {
        // Toggle the content visibility
        const content = this.nextElementSibling;
        const isVisible = content.style.display !== "none";

        // Toggle the chevron icon
        const chevron = this.querySelector(".chevron-icon");

        if (isVisible) {
          content.style.display = "none";
          chevron.classList.remove("expanded");
        } else {
          content.style.display = "block";
          chevron.classList.add("expanded");
        }
      });
    });
}

function setupResourceDetailLinks() {
  document.querySelectorAll(".resource-details-link").forEach((link) => {
    link.addEventListener("click", function () {
      const resourceIndex = this.dataset.resourceIndex;

      // Switch to resources tab
      const resourcesTab = document.querySelector("#resources-tab");
      // Use Bootstrap's Tab API to show the tab
      const bootstrapTab = new bootstrap.Tab(resourcesTab);
      bootstrapTab.show();

      // Scroll to the resource after a short delay to allow the tab to render
      setTimeout(() => {
        const resourceElement = document.querySelector(
          `#resource-${resourceIndex}`
        );
        if (resourceElement) {
          resourceElement.scrollIntoView({ behavior: "smooth" });
        }
      }, 300);
    });
  });
}

// Add event listener setup for field search
document.addEventListener("DOMContentLoaded", () => {
  // Get the metadata viewer container
  const metadataViewer = document.getElementById("metadata-viewer");
  if (!metadataViewer) return;

  // Get the metadata ID from the data attribute
  const metadataId = metadataViewer.dataset.metadataId;

  // Fetch the metadata
  window
    .reverseUrl("api:api_table_meta", {
      schema: "data",
      table: window.meta_widget_config.table,
    })
    .then((url) => {
      return fetch(url);
    })
    .then((response) => {
      if (!response.ok) {
        throw new Error(
          `Failed to fetch metadata: ${response.status} ${response.statusText}`
        );
      }
      return response.json();
    })
    .then((metadata) => {
      // Render the metadata viewer
      renderMetadataViewer(metadata, metadataViewer);
    })
    .catch((error) => {
      console.error("Error fetching metadata:", error);
      metadataViewer.innerHTML = `
        <div class="alert alert-danger" role="alert">
          <h4 class="alert-heading">Error loading metadata</h4>
          <p>${error.message}</p>
        </div>
      `;
    });

  // After rendering the metadata viewer, set up the field search functionality
  document.querySelectorAll('[id^="field-search-"]').forEach((searchInput) => {
    searchInput.addEventListener("input", function () {
      const resourceIndex = this.id.split("-")[2];
      const searchTerm = this.value.toLowerCase();

      // Filter table rows
      const tableRows = document.querySelectorAll(
        `#fields-table-${resourceIndex} tbody tr`
      );
      tableRows.forEach((row) => {
        const text = row.textContent.toLowerCase();
        if (text.includes(searchTerm)) {
          row.style.display = "";
        } else {
          row.style.display = "none";
        }
      });

      // Filter accordion items
      const fieldItems = document.querySelectorAll(
        `#fieldAccordion-${resourceIndex} .field-item`
      );
      fieldItems.forEach((item) => {
        const fieldName = item.dataset.fieldName;
        if (fieldName && fieldName.includes(searchTerm)) {
          item.style.display = "";
        } else {
          item.style.display = "none";
        }
      });
    });
  });
});
