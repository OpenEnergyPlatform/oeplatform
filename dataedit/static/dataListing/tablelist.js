import "./tablelist.css";

function fetchMetadataForCards() {
  const resourceCards = document.querySelectorAll(
    ".resource-card:not(.meta-loaded)"
  );

  resourceCards.forEach((card) => {
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

        let descriptionText = "No description provided.";
        let projectName = "";
        let creatorOrg = "";
        let licenseName = "";
        let licenseTitle = "Data License";
        let spatialName = "";
        let refDate = "";
        let reviewBadge = "";

        if (metaObj && metaObj.resources && metaObj.resources.length > 0) {
          const res = metaObj.resources[0];

          if (res.description) {
            descriptionText =
              res.description.length > 200
                ? res.description.substring(0, 200) + "..."
                : res.description;
          }

          if (res.projectContext && res.projectContext.title) {
            projectName = res.projectContext.title;
          } else if (res.context && res.context.title) {
            projectName = res.context.title;
          }

          if (res.contributors && Array.isArray(res.contributors)) {
            const creator = res.contributors.find(
              (c) => c.roles && c.roles.includes("Creator")
            );
            if (creator && creator.organization) {
              creatorOrg = creator.organization;
            }
          }

          if (res.licenses && res.licenses.length > 0) {
            licenseTitle = res.licenses[0].title || "Data License";
            licenseName = res.licenses[0].name;
          }

          if (res.spatial && res.spatial.extent && res.spatial.extent.name) {
            spatialName = res.spatial.extent.name;
          }

          if (res.temporal && res.temporal.referenceDate) {
            refDate = res.temporal.referenceDate;
          }

          if (res.review && res.review.badge) {
            reviewBadge = res.review.badge;
          }
        }

        // SECURE DOM INSERTION (Passes Snyk checks by avoiding .innerHTML)
        injectionZone.replaceChildren(); // clear skeleton

        // Build Description
        const p = document.createElement("p");
        p.className = "card-text text-secondary mb-3 small";
        p.style.lineHeight = "1.5";
        p.textContent = descriptionText;
        injectionZone.appendChild(p);

        // Build Badge Container
        const badgeContainer = document.createElement("div");
        badgeContainer.className = "d-flex flex-wrap align-items-center small";

        // Helper to append badges using pure Document nodes
        const appendBadge = (
          text,
          prefix,
          iconClass,
          wrapperClass,
          tooltip
        ) => {
          if (!text) return;
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

          badgeContainer.appendChild(span);
        };

        // Append active badges
        if (reviewBadge) {
          appendBadge(
            `${reviewBadge} Reviewed`,
            "",
            "fas fa-award me-1",
            "badge bg-success bg-opacity-10 text-success border border-success me-2 mb-2",
            "Peer Review Status"
          );
        }
        if (licenseName) {
          appendBadge(
            licenseName,
            "License: ",
            "fas fa-balance-scale me-1",
            "badge bg-light text-dark border me-2 mb-2",
            licenseTitle
          );
        }
        if (projectName) {
          appendBadge(
            projectName,
            "Project: ",
            "fas fa-project-diagram me-1",
            "me-3 mb-2 text-muted",
            "Project Name"
          );
        }
        if (creatorOrg) {
          appendBadge(
            creatorOrg,
            "Org: ",
            "fas fa-building me-1",
            "me-3 mb-2 text-muted",
            "Creator Organization"
          );
        }
        if (spatialName) {
          appendBadge(
            spatialName,
            "Location: ",
            "fas fa-map-marker-alt me-1",
            "me-3 mb-2 text-muted",
            "Spatial Extent / Location"
          );
        }
        if (refDate) {
          appendBadge(
            refDate,
            "Ref Date: ",
            "far fa-calendar-alt me-1",
            "me-3 mb-2 text-muted",
            "Temporal Reference"
          );
        }

        injectionZone.appendChild(badgeContainer);

        // Initialize tooltips dynamically
        var tooltipTriggerList = [].slice.call(
          badgeContainer.querySelectorAll('[data-bs-toggle="tooltip"]')
        );
        tooltipTriggerList.map(function (tooltipTriggerEl) {
          return new bootstrap.Tooltip(tooltipTriggerEl);
        });
      })
      .catch((error) => {
        injectionZone.replaceChildren();
        const errP = document.createElement("p");
        errP.className = "card-text text-muted fst-italic small";
        errP.textContent = "Metadata currently unavailable.";
        injectionZone.appendChild(errP);
      });
  });
}

// Secure UI Helpers
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
  container.replaceChildren(wrapper); // Replaces content securely
}

function showError(container) {
  const err = document.createElement("div");
  err.className = "alert alert-danger shadow-sm";
  err.textContent = "Error loading data. Please try again.";
  container.replaceChildren(err);
}

document.addEventListener("DOMContentLoaded", function () {
  var tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  fetchMetadataForCards();

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
          const doc = parser.parseFromString(html, "text/html");
          const newContainer = doc.getElementById("table-list-container");

          if (newContainer) {
            // Replaces nodes securely instead of using innerHTML
            container.replaceChildren(...newContainer.childNodes);
            bindAjaxPagination();
            fetchMetadataForCards();
          }
        })
        .catch((error) => showError(container));
    });
  }

  function bindAjaxPagination() {
    const paginationLinks = document.querySelectorAll(".ajax-pagination");
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
              const doc = new DOMParser().parseFromString(html, "text/html");
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

  bindAjaxPagination();

  window.addEventListener("popstate", function (e) {
    window.location.reload();
  });
});
