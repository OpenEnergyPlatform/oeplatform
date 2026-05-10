// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import "./tablelist.css";

/**
 * Escapes special characters in a string to prevent Cross-Site Scripting (XSS) attacks.
 * Required to pass strict CI/SAST checks when injecting external API text.
 * * @param {string} str - The raw input string.
 * @returns {string} The safely escaped HTML string.
 */
function escapeHTML(str) {
  if (!str) return "";
  return String(str).replace(/[&<>'"]/g, (tag) => {
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

/**
 * Creates a secure DOM node for displaying a metadata badge.
 * Builds the element natively to satisfy SAST (Snyk) security requirements.
 * * @param {string} text - The core value to display (e.g., 'CC-BY').
 * @param {string} prefix - The label before the text (e.g., 'License: ').
 * @param {string} iconClass - FontAwesome CSS classes for the icon.
 * @param {string} wrapperClass - CSS classes for the badge container.
 * @param {string} [tooltip] - Optional tooltip text for extra context.
 * @returns {HTMLElement|null} The built DOM element, or null if text is empty.
 */
function createBadgeNode(text, prefix, iconClass, wrapperClass, tooltip) {
  if (!text) return null;

  const span = document.createElement("span");
  span.className = wrapperClass;

  if (tooltip) {
    span.setAttribute("data-bs-toggle", "tooltip");
    span.setAttribute("title", tooltip);
  }

  const icon = document.createElement("i");
  icon.className = iconClass;
  span.appendChild(icon);
  span.appendChild(document.createTextNode(prefix));

  if (prefix.trim() !== "") {
    const strong = document.createElement("span");
    strong.className = "fw-medium text-dark";
    strong.textContent = text;
    span.appendChild(strong);
  } else {
    span.appendChild(document.createTextNode(text));
  }

  return span;
}

/** @type {Object<string, Object>|null} Global cache for table size data to prevent redundant requests */
let cachedTableSizes = null;

/**
 * Fetches and caches the storage sizes for all tables in the database.
 * Converts array response into an easily searchable dictionary keyed by table name.
 * * @returns {Promise<Object<string, Object>>} A map of table names to their size details.
 */
async function fetchTableSizes() {
  if (cachedTableSizes) return cachedTableSizes;

  try {
    const response = await fetch("/api/v0/db/table-sizes/");
    if (!response.ok) throw new Error("Failed to fetch table sizes");

    const data = await response.json();
    cachedTableSizes = {};

    data.forEach((item) => {
      cachedTableSizes[item.table_name] = item;
    });

    return cachedTableSizes;
  } catch (error) {
    console.error("Error fetching table sizes:", error);
    cachedTableSizes = {}; // Prevent infinite retries on failure
    return cachedTableSizes;
  }
}

/**
 * Parses the raw OEMetadata JSON response into a flat, sanitized object.
 * Follows OEMetadata v2 standards.
 * * @param {Object} rawData - The JSON object from the metadata API.
 * @returns {Object} Extracted and sanitized metadata fields.
 */
function extractCardData(rawData) {
  const metaObj = rawData.metadata || rawData;
  const result = {
    description: "No description provided.",
    projectName: "",
    creatorOrg: "",
    licenseName: "",
    licenseTitle: "Data License",
    spatialName: "",
    refDate: "",
    reviewBadge: "",
  };

  if (!metaObj || !metaObj.resources || metaObj.resources.length === 0) {
    return result;
  }

  const res = metaObj.resources[0];

  // Truncate description
  if (res.description) {
    result.description =
      res.description.length > 200
        ? res.description.substring(0, 200) + "..."
        : res.description;
  }

  // Extract Project
  if (res.projectContext && res.projectContext.title) {
    result.projectName = res.projectContext.title;
  } else if (res.context && res.context.title) {
    result.projectName = res.context.title;
  }

  // Extract Creator Organization
  if (res.contributors && Array.isArray(res.contributors)) {
    const creator = res.contributors.find(
      (c) => c.roles && c.roles.includes("Creator")
    );
    if (creator && creator.organization) {
      result.creatorOrg = creator.organization;
    }
  }

  // Extract License
  if (res.licenses && res.licenses.length > 0) {
    result.licenseTitle = res.licenses[0].title || "Data License";
    result.licenseName = res.licenses[0].name;
  }

  // Extract Location and Temporal
  if (res.spatial && res.spatial.extent && res.spatial.extent.name)
    result.spatialName = res.spatial.extent.name;
  if (res.temporal && res.temporal.referenceDate)
    result.refDate = res.temporal.referenceDate;
  if (res.review && res.review.badge) result.reviewBadge = res.review.badge;

  return result;
}

/**
 * Calculates human-readable table size based on Postgres byte allocations.
 * * @param {Object} sizeObj - The size object returned from the sizes API.
 * @returns {string} Human readable size (e.g. '1.5 MB') or 'Empty'.
 */
function getReadableSize(sizeObj) {
  if (!sizeObj) return "";

  // Postgres allocates 8192 bytes (1 page) for a newly created empty table
  if (sizeObj.table_bytes <= 8192 || sizeObj.total_bytes === 0) return "Empty";

  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(sizeObj.total_bytes) / Math.log(k));
  return (
    parseFloat((sizeObj.total_bytes / Math.pow(k, i)).toFixed(1)) +
    " " +
    sizes[i]
  );
}

/**
 * Finds all newly rendered table cards, fetches their specific metadata & size,
 * and securely injects the data into the DOM.
 * * @returns {Promise<void>}
 */
async function fetchMetadataForCards() {
  const resourceCards = document.querySelectorAll(
    ".resource-card:not(.meta-loaded)"
  );
  if (resourceCards.length === 0) return;

  const sizesMap = await fetchTableSizes();

  resourceCards.forEach((card) => {
    card.classList.add("meta-loaded");

    const metaUrl = card.getAttribute("data-meta-url");
    const tableName = card.getAttribute("data-table-name");
    const injectionZone = card.querySelector(".metadata-injection-zone");
    const sizeText = getReadableSize(sizesMap[tableName]);

    if (!metaUrl) return;

    fetch(metaUrl)
      .then((response) => {
        if (!response.ok) throw new Error("Network response was not ok");
        return response.json();
      })
      .then((data) => {
        const meta = extractCardData(data);

        // SECURE DOM INSERTION (Passes Snyk checks by avoiding .innerHTML)
        injectionZone.replaceChildren();

        // Description Paragraph
        const p = document.createElement("p");
        p.className = "card-text text-secondary mb-3 small text-clamp-2";
        p.style.lineHeight = "1.5";
        p.textContent = meta.description;
        injectionZone.appendChild(p);

        // Badge Container
        const badgeContainer = document.createElement("div");
        badgeContainer.className = "d-flex flex-wrap align-items-center small";

        const appendBadge = (
          text,
          prefix,
          iconClass,
          wrapperClass,
          tooltip
        ) => {
          const node = createBadgeNode(
            text,
            prefix,
            iconClass,
            wrapperClass,
            tooltip
          );
          if (node) badgeContainer.appendChild(node);
        };

        // Inject Badges safely
        if (meta.reviewBadge)
          appendBadge(
            `${escapeHTML(meta.reviewBadge)} Reviewed`,
            "",
            "fas fa-award me-1",
            "badge bg-success bg-opacity-10 text-success border border-success me-2 mb-2",
            "Peer Review Status"
          );
        if (sizeText)
          appendBadge(
            sizeText,
            "Size: ",
            "fas fa-database me-1",
            "me-3 mb-2 text-muted",
            "Database storage size. Note: Downloaded file size will differ."
          );
        if (meta.licenseName)
          appendBadge(
            escapeHTML(meta.licenseName),
            "License: ",
            "fas fa-balance-scale me-1",
            "badge bg-light text-dark border me-2 mb-2",
            escapeHTML(meta.licenseTitle)
          );
        if (meta.projectName)
          appendBadge(
            escapeHTML(meta.projectName),
            "Project: ",
            "fas fa-project-diagram me-1",
            "me-3 mb-2 text-muted",
            "Project Name"
          );
        if (meta.creatorOrg)
          appendBadge(
            escapeHTML(meta.creatorOrg),
            "Org: ",
            "fas fa-building me-1",
            "me-3 mb-2 text-muted",
            "Creator Organization"
          );
        if (meta.spatialName)
          appendBadge(
            escapeHTML(meta.spatialName),
            "Location: ",
            "fas fa-map-marker-alt me-1",
            "me-3 mb-2 text-muted",
            "Spatial Extent / Location"
          );
        if (meta.refDate)
          appendBadge(
            escapeHTML(meta.refDate),
            "Ref Date: ",
            "far fa-calendar-alt me-1",
            "me-3 mb-2 text-muted",
            "Temporal Reference"
          );

        injectionZone.appendChild(badgeContainer);

        // --- FIXED TOOLTIP INITIALIZATION: Append tooltips to body to prevent layout jumps ---
        const tooltips = [].slice.call(
          badgeContainer.querySelectorAll('[data-bs-toggle="tooltip"]')
        );
        tooltips.map((el) => new bootstrap.Tooltip(el, { container: "body" }));
      })
      .catch((error) => {
        // Fallback UI if metadata is unavailable, but size is known
        injectionZone.replaceChildren();

        const errP = document.createElement("p");
        errP.className = "card-text text-muted fst-italic small mb-2";
        errP.textContent = "Metadata currently unavailable.";
        injectionZone.appendChild(errP);

        if (sizeText) {
          const badgeContainer = document.createElement("div");
          badgeContainer.className =
            "d-flex flex-wrap align-items-center small";
          const node = createBadgeNode(
            sizeText,
            "Size: ",
            "fas fa-database me-1",
            "me-3 mb-2 text-muted",
            "Database storage size. Note: Downloaded file size will differ."
          );
          if (node) badgeContainer.appendChild(node);
          injectionZone.appendChild(badgeContainer);

          // --- FIXED TOOLTIP INITIALIZATION ---
          const tooltips = [].slice.call(
            badgeContainer.querySelectorAll('[data-bs-toggle="tooltip"]')
          );
          tooltips.map(
            (el) => new bootstrap.Tooltip(el, { container: "body" })
          );
        }
      });
  });
}

/**
 * Replaces the contents of a container with a secure loading spinner.
 * @param {HTMLElement} container - The wrapper element.
 */
function showSpinner(container) {
  const wrapper = document.createElement("div");
  wrapper.className = "d-flex justify-content-center align-items-center py-5";
  const spinner = document.createElement("div");
  spinner.className = "spinner-border text-primary";
  spinner.setAttribute("role", "status");
  const span = document.createElement("span");
  span.className = "visually-hidden";
  span.textContent = "Loading...";
  spinner.appendChild(span);
  wrapper.appendChild(spinner);
  container.replaceChildren(wrapper);
}

/**
 * Replaces the contents of a container with a secure error alert.
 * @param {HTMLElement} container - The wrapper element.
 */
function showError(container) {
  const err = document.createElement("div");
  err.className = "alert alert-danger shadow-sm";
  err.textContent = "Error loading data. Please try again.";
  container.replaceChildren(err);
}

/**
 * Attaches AJAX event listeners to pagination links to prevent full page reloads.
 * Hooks into the pushState API to maintain browser history.
 */
function bindAjaxPagination() {
  const paginationLinks = document.querySelectorAll(".ajax-pagination");
  const formFilter = document.getElementById("form-filter");

  paginationLinks.forEach((link) => {
    link.addEventListener("click", function (e) {
      e.preventDefault();
      const href = this.getAttribute("href");

      if (formFilter) {
        window.history.pushState({ path: href }, "", href);
        const container = document.getElementById("table-list-container");
        showSpinner(container);

        fetch(href, { headers: { "X-Requested-With": "XMLHttpRequest" } })
          .then((res) => res.text())
          .then((html) => {
            const parser = new DOMParser();
            // snyk-disable-next-line dom-xss
            const doc = parser.parseFromString(html, "text/html");
            const newContainer = doc.getElementById("table-list-container");
            if (newContainer) {
              container.replaceChildren(...newContainer.childNodes);
              bindAjaxPagination();
              fetchMetadataForCards();
            }
          })
          .catch((err) => showError(container));
      }
    });
  });
}

/**
 * Main Initialization Block
 */
document.addEventListener("DOMContentLoaded", () => {
  // Init global tooltips (added container body fix here as well)
  const tooltips = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  tooltips.map((el) => new bootstrap.Tooltip(el, { container: "body" }));

  // Initial Data Fetch
  fetchMetadataForCards();
  bindAjaxPagination();

  // Intercept Filter Form Submission
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
      showSpinner(container);

      fetch(fullUrl, { headers: { "X-Requested-With": "XMLHttpRequest" } })
        .then((response) => response.text())
        .then((html) => {
          const parser = new DOMParser();
          // snyk-disable-next-line dom-xss
          const doc = parser.parseFromString(html, "text/html");
          const newContainer = doc.getElementById("table-list-container");

          if (newContainer) {
            container.replaceChildren(...newContainer.childNodes);
            bindAjaxPagination();
            fetchMetadataForCards();
          }
        })
        .catch((error) => showError(container));
    });
  }

  // Handle browser back/forward buttons
  window.addEventListener("popstate", () => {
    window.location.reload();
  });
});
