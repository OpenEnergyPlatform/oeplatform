// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import "./tablelist.css";

// Helper function to prevent XSS attacks (Required to pass Snyk)
function escapeHTML(str) {
  if (!str) return "";
  return String(str).replace(/[&<>'"]/g, function (tag) {
    const charsToReplace = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      "'": "&#39;",
      '"': "&quot;",
    };
    return charsToReplace[tag] || tag;
  });
}

// Extract metadata fetching logic into a reusable function
function fetchMetadataForCards() {
  const resourceCards = document.querySelectorAll(
    ".resource-card:not(.meta-loaded)"
  );

  resourceCards.forEach((card) => {
    // Mark as loaded to prevent double fetching on AJAX reloads
    card.classList.add("meta-loaded");

    const metaUrl = card.getAttribute("data-meta-url");
    const injectionZone = card.querySelector(".metadata-injection-zone");

    if (!metaUrl) return;

    fetch(metaUrl)
      .then((response) => {
        if (!response.ok) throw new Error("Network response was not ok");
        return response.json();
      })
      .then((data) => {
        const metaObj = data.metadata || data;

        let description = "No description provided.";
        let licenseHtml = "";
        let spatialHtml = "";
        let temporalHtml = "";
        let reviewHtml = "";
        let orgHtml = "";
        let projectHtml = "";

        if (metaObj && metaObj.resources && metaObj.resources.length > 0) {
          const res = metaObj.resources[0];

          // Description
          if (res.description) {
            description =
              res.description.length > 200
                ? res.description.substring(0, 200) + "..."
                : res.description;
            description = escapeHTML(description); // Escape description to prevent XSS
          }

          // Project Extraction
          let projectName = "";
          if (res.projectContext && res.projectContext.title) {
            projectName = res.projectContext.title;
          } else if (res.context && res.context.title) {
            projectName = res.context.title;
          }

          if (projectName) {
            projectHtml = `<span class="me-3 mb-2 text-muted" data-bs-toggle="tooltip" title="Project Name"><i class="fas fa-project-diagram me-1"></i>Project: <span class="fw-medium text-dark">${escapeHTML(projectName)}</span></span>`;
          }

          // Creator Organization Extraction
          let creatorOrg = "";
          if (res.contributors && Array.isArray(res.contributors)) {
            const creator = res.contributors.find(
              (c) => c.roles && c.roles.includes("Creator")
            );
            if (creator && creator.organization) {
              creatorOrg = creator.organization;
            }
          }

          if (creatorOrg) {
            orgHtml = `<span class="me-3 mb-2 text-muted" data-bs-toggle="tooltip" title="Creator Organization"><i class="fas fa-building me-1"></i>Org: <span class="fw-medium text-dark">${escapeHTML(creatorOrg)}</span></span>`;
          }

          // License
          if (res.licenses && res.licenses.length > 0) {
            const licenseTitle = escapeHTML(
              res.licenses[0].title || "Data License"
            );
            const licenseName = escapeHTML(res.licenses[0].name);
            licenseHtml = `<span class="badge bg-light text-dark border me-2 mb-2" data-bs-toggle="tooltip" title="${licenseTitle}"><i class="fas fa-balance-scale me-1"></i>License: ${licenseName}</span>`;
          }

          // Spatial
          if (res.spatial && res.spatial.extent && res.spatial.extent.name) {
            spatialHtml = `<span class="me-3 mb-2 text-muted" data-bs-toggle="tooltip" title="Spatial Extent / Location"><i class="fas fa-map-marker-alt me-1"></i>Location: <span class="fw-medium text-dark">${escapeHTML(res.spatial.extent.name)}</span></span>`;
          }

          // Temporal
          if (res.temporal && res.temporal.referenceDate) {
            temporalHtml = `<span class="me-3 mb-2 text-muted" data-bs-toggle="tooltip" title="Temporal Reference"><i class="far fa-calendar-alt me-1"></i>Ref Date: <span class="fw-medium text-dark">${escapeHTML(res.temporal.referenceDate)}</span></span>`;
          }

          // Peer Review Badge
          if (res.review && res.review.badge) {
            reviewHtml = `<span class="badge bg-success bg-opacity-10 text-success border border-success me-2 mb-2" data-bs-toggle="tooltip" title="Peer Review Status"><i class="fas fa-award me-1"></i>${escapeHTML(res.review.badge)} Reviewed</span>`;
          }
        }

        // InnerHTML is now safe because all variables have been escaped
        injectionZone.innerHTML = `
          <p class="card-text text-secondary mb-3 small" style="line-height: 1.5;">
            ${description}
          </p>
          <div class="d-flex flex-wrap align-items-center small">
            ${reviewHtml}
            ${licenseHtml}
            ${projectHtml}
            ${orgHtml}
            ${spatialHtml}
            ${temporalHtml}
          </div>
        `;

        // Initialize tooltips on the newly injected elements
        var tooltipTriggerList = [].slice.call(
          injectionZone.querySelectorAll('[data-bs-toggle="tooltip"]')
        );
        tooltipTriggerList.map(function (tooltipTriggerEl) {
          return new bootstrap.Tooltip(tooltipTriggerEl);
        });
      })
      .catch((error) => {
        injectionZone.innerHTML = `
           <p class="card-text text-muted fst-italic small">Metadata currently unavailable.</p>
        `;
      });
  });
}

document.addEventListener("DOMContentLoaded", function () {
  // 1. Initialize Bootstrap tooltips
  var tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // 2. Initial Metadata Fetch
  fetchMetadataForCards();

  // 3. AJAX Filtering Logic
  const formFilter = document.getElementById("form-filter");

  if (formFilter) {
    $(formFilter).on("submit", function (e) {
      e.preventDefault();

      const form = $(this);
      const url = form.attr("action") || window.location.pathname;
      const params = form.serialize();
      const fullUrl = url + "?" + params;

      window.history.pushState({ path: fullUrl }, "", fullUrl);

      const container = document.getElementById("table-list-container");

      container.innerHTML = `
        <div class="d-flex justify-content-center align-items-center py-5">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
        </div>
      `;

      fetch(fullUrl, { headers: { "X-Requested-With": "XMLHttpRequest" } })
        .then((response) => response.text())
        .then((html) => {
          const parser = new DOMParser();
          const doc = parser.parseFromString(html, "text/html");
          const newContainer = doc.getElementById("table-list-container");

          if (newContainer) {
            container.innerHTML = newContainer.innerHTML;
            bindAjaxPagination();
            fetchMetadataForCards();
          }
        })
        .catch((error) => {
          console.error("Error fetching filtered data:", error);
          container.innerHTML =
            '<div class="alert alert-danger shadow-sm">Error loading data. Please try again.</div>';
        });
    });
  }

  // 4. Handle AJAX Pagination
  function bindAjaxPagination() {
    const paginationLinks = document.querySelectorAll(".ajax-pagination");
    paginationLinks.forEach((link) => {
      link.addEventListener("click", function (e) {
        e.preventDefault();
        const href = this.getAttribute("href");

        if (formFilter) {
          window.history.pushState({ path: href }, "", href);
          const container = document.getElementById("table-list-container");
          container.innerHTML = `<div class="d-flex justify-content-center align-items-center py-5"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>`;

          fetch(href, { headers: { "X-Requested-With": "XMLHttpRequest" } })
            .then((res) => res.text())
            .then((html) => {
              const doc = new DOMParser().parseFromString(html, "text/html");
              container.innerHTML = doc.getElementById(
                "table-list-container"
              ).innerHTML;
              bindAjaxPagination();
              fetchMetadataForCards();
            });
        }
      });
    });
  }

  bindAjaxPagination();

  // 5. Handle browser back/forward buttons
  window.addEventListener("popstate", function (e) {
    window.location.reload();
  });
});
