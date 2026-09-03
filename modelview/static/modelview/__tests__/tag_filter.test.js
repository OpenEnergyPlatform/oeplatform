// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// @vitest-environment happy-dom
//
// The factsheet list page's tag filter shipped two bugs that a Django test
// could not see, because both lived in the browser: the CSV link built from
// checkbox DOM ids instead of primary keys, and a checkbox restored from the
// URL that rendered without its tick. Each has a test here.
import { beforeEach, describe, expect, it } from "vitest";

import {
  checkedTagValues,
  filterQuery,
  filteredUrl,
  rowMatchesTags,
  showCheckedTags,
  toggleTag,
} from "../tag_filter.js";

/**
 * Render the sidebar's tag checkboxes the way `modellist.html` does.
 *
 * The label wraps the input, which matters: the visible tick is drawn from a
 * class on that parent, not on the input itself.
 *
 * @param {{pk: string, checked?: boolean}[]} tags the tags to render.
 * @return {void}
 */
function renderSidebar(tags) {
  document.body.innerHTML = tags
    .map(
      (tag) =>
        `<label class="tag-checkbox-container">
           <input type="checkbox" class="tag-checkbox" id="select_${tag.pk}"
                  value="${tag.pk}" ${tag.checked ? "checked" : ""}>
         </label>`
    )
    .join("");
}

describe("toggleTag", () => {
  it("adds a newly checked tag", () => {
    expect(toggleTag(["a"], "b", true)).toEqual(["a", "b"]);
  });

  it("removes an unchecked tag", () => {
    expect(toggleTag(["a", "b"], "a", false)).toEqual(["b"]);
  });

  it("does not add the same tag twice", () => {
    expect(toggleTag(["a"], "a", true)).toEqual(["a"]);
  });

  it("leaves the caller's array alone", () => {
    const active = ["a"];

    toggleTag(active, "b", true);

    expect(active).toEqual(["a"]);
  });
});

describe("filterQuery", () => {
  it("carries raw primary keys, comma separated", () => {
    expect(filterQuery(["wind", "solar"])).toBe("?tags=wind,solar");
  });

  it("is empty when nothing is selected", () => {
    // Not `?tags=`: an unfiltered view should be the plain page URL, and the
    // CSV link should be the plain download URL.
    expect(filterQuery([])).toBe("");
  });

  it("never emits the checkbox id prefix", () => {
    // The whole defect in one assertion: the page used to send
    // `?tags=select_wind`, which the CSV endpoint matched against nothing and
    // answered with a header row and no error.
    expect(filterQuery(["wind"])).not.toContain("select_");
  });
});

describe("filteredUrl", () => {
  const location = { pathname: "/factsheets/models/", search: "", hash: "" };

  it("adds the selection to a bare URL", () => {
    expect(filteredUrl(location, ["wind"])).toBe(
      "/factsheets/models/?tags=wind"
    );
  });

  it("replaces an existing selection rather than appending one", () => {
    const filtered = { ...location, search: "?tags=solar" };

    expect(filteredUrl(filtered, ["wind"])).toBe(
      "/factsheets/models/?tags=wind"
    );
  });

  it("drops the parameter entirely when the filter is cleared", () => {
    const filtered = { ...location, search: "?tags=wind" };

    expect(filteredUrl(filtered, [])).toBe("/factsheets/models/");
  });

  it("keeps other query parameters", () => {
    const other = { ...location, search: "?page=3&sort=name" };

    const url = filteredUrl(other, ["wind"]);

    expect(url).toContain("page=3");
    expect(url).toContain("sort=name");
    expect(url).toContain("tags=wind");
  });

  it("keeps other query parameters when the filter is cleared", () => {
    const other = { ...location, search: "?page=3&tags=wind" };

    expect(filteredUrl(other, [])).toBe("/factsheets/models/?page=3");
  });

  it("keeps the fragment", () => {
    const anchored = { ...location, hash: "#overview" };

    expect(filteredUrl(anchored, ["wind"])).toBe(
      "/factsheets/models/?tags=wind#overview"
    );
  });
});

describe("rowMatchesTags", () => {
  const row = [{ pk: "wind" }, { pk: "solar" }];

  it("keeps every row when nothing is selected", () => {
    expect(rowMatchesTags(row, [])).toBe(true);
  });

  it("keeps a row carrying the selected tag", () => {
    expect(rowMatchesTags(row, ["wind"])).toBe(true);
  });

  it("drops a row missing the selected tag", () => {
    expect(rowMatchesTags(row, ["hydro"])).toBe(false);
  });

  it("requires every selected tag, not any of them", () => {
    // The AND semantics the sidebar has always had, and which the payload
    // slices must not trade away.
    expect(rowMatchesTags(row, ["wind", "solar"])).toBe(true);
    expect(rowMatchesTags(row, ["wind", "hydro"])).toBe(false);
  });

  it("drops a row whose tags are missing entirely", () => {
    expect(rowMatchesTags(undefined, ["wind"])).toBe(false);
  });

  it("matches on raw primary keys", () => {
    expect(rowMatchesTags(row, ["select_wind"])).toBe(false);
  });
});

describe("checkedTagValues", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
  });

  it("reads the selection the server rendered from the URL", () => {
    renderSidebar([
      { pk: "wind", checked: true },
      { pk: "solar" },
      { pk: "hydro", checked: true },
    ]);

    expect(checkedTagValues(document)).toEqual(["wind", "hydro"]);
  });

  it("is empty on an unfiltered page", () => {
    renderSidebar([{ pk: "wind" }, { pk: "solar" }]);

    expect(checkedTagValues(document)).toEqual([]);
  });

  it("returns primary keys, not the checkbox ids", () => {
    renderSidebar([{ pk: "wind", checked: true }]);

    expect(checkedTagValues(document)).toEqual(["wind"]);
  });
});

describe("showCheckedTags", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
  });

  it("gives a checked tag its visible tick", () => {
    // The bug this exists for: the input is `display: none`, so a filter
    // restored from the URL filtered the table while the sidebar looked
    // untouched.
    renderSidebar([{ pk: "wind", checked: true }, { pk: "solar" }]);

    showCheckedTags(document);

    const labels = document.querySelectorAll(".tag-checkbox-container");
    expect(labels[0].classList.contains("tag-checkbox-checked")).toBe(true);
    expect(labels[1].classList.contains("tag-checkbox-checked")).toBe(false);
  });

  it("removes the tick from a tag that is no longer checked", () => {
    renderSidebar([{ pk: "wind", checked: true }]);
    showCheckedTags(document);
    document.querySelector(".tag-checkbox").checked = false;

    showCheckedTags(document);

    expect(
      document
        .querySelector(".tag-checkbox-container")
        .classList.contains("tag-checkbox-checked")
    ).toBe(false);
  });
});
