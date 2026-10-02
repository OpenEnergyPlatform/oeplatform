// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// @vitest-environment happy-dom
//
// Every place the platform lists tags shows the whole vocabulary at once --
// ~825 of them on the administration page and in the factsheet editor, 273 in
// the factsheet overview's filter. That is a wall of colour nobody can read.
// This is the searching, sorting and collapsing all three share, so they
// cannot drift into three different behaviours.
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  applyTagList,
  bindTagList,
  matchesQuery,
  orderItems,
} from "../tag_list.js";

/**
 * Build a tag list of the shape the templates render.
 *
 * @param {[string, number][]} tags name and usage count pairs.
 * @return {HTMLElement} the container.
 */
function renderList(tags) {
  document.body.innerHTML = `<div data-tag-list></div>`;
  const container = document.querySelector("[data-tag-list]");
  tags.forEach(([name, usage]) => {
    const item = document.createElement("span");
    item.setAttribute("data-tag-name", name);
    item.setAttribute("data-tag-usage", String(usage));
    item.textContent = name;
    container.appendChild(item);
  });
  return container;
}

/**
 * The names currently visible, in DOM order.
 *
 * @param {HTMLElement} container the tag list.
 * @return {string[]} visible tag names.
 */
function visible(container) {
  return Array.from(container.children)
    .filter((el) => !el.hidden)
    .map((el) => el.getAttribute("data-tag-name"));
}

describe("matchesQuery", () => {
  it("matches everything on an empty query", () => {
    expect(matchesQuery("wind onshore", "")).toBe(true);
    expect(matchesQuery("wind onshore", "   ")).toBe(true);
  });

  it("matches a substring anywhere in the name", () => {
    expect(matchesQuery("wind onshore", "onshore")).toBe(true);
    expect(matchesQuery("wind onshore", "nd on")).toBe(true);
  });

  it("ignores case on both sides", () => {
    expect(matchesQuery("Wind Onshore", "WIND")).toBe(true);
  });

  it("does not match an absent substring", () => {
    expect(matchesQuery("wind onshore", "solar")).toBe(false);
  });
});

describe("orderItems", () => {
  const items = [
    { name: "solar", usage: 5 },
    { name: "Wind", usage: 12 },
    { name: "grid", usage: 12 },
  ];

  it("orders by name, case-insensitively", () => {
    expect(orderItems(items, "name").map((i) => i.name)).toEqual([
      "grid",
      "solar",
      "Wind",
    ]);
  });

  it("orders by usage, most used first", () => {
    expect(orderItems(items, "usage").map((i) => i.name)).toEqual([
      "grid",
      "Wind",
      "solar",
    ]);
  });

  it("breaks a usage tie by name, so the order is never arbitrary", () => {
    const tied = orderItems(items, "usage").slice(0, 2).map((i) => i.name);
    expect(tied).toEqual(["grid", "Wind"]);
  });

  it("sorts digits inside a name as numbers, not as text", () => {
    const runs = [
      { name: "run 10", usage: 0 },
      { name: "run 2", usage: 0 },
      { name: "run 1", usage: 0 },
    ];

    expect(orderItems(runs, "name").map((i) => i.name)).toEqual([
      "run 1",
      "run 2",
      "run 10",
    ]);
  });

  it("does not modify the array it was given", () => {
    const original = items.map((i) => i.name);
    orderItems(items, "usage");
    expect(items.map((i) => i.name)).toEqual(original);
  });
});

describe("applyTagList", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
  });

  it("shows everything when there is no limit and no query", () => {
    const c = renderList([["wind", 3], ["solar", 1]]);

    const counts = applyTagList(c, {});

    // Name order is the default, so "solar" leads -- what this asserts is
    // that nothing is hidden.
    expect(visible(c)).toEqual(["solar", "wind"]);
    expect(counts).toEqual({ total: 2, matched: 2, shown: 2 });
  });

  it("shows only the first `limit` items when collapsed", () => {
    const c = renderList([["a", 1], ["b", 2], ["c", 3]]);

    const counts = applyTagList(c, { limit: 2 });

    expect(visible(c)).toEqual(["a", "b"]);
    expect(counts).toEqual({ total: 3, matched: 3, shown: 2 });
  });

  it("narrows to the matches of a query", () => {
    const c = renderList([["wind onshore", 1], ["wind offshore", 2], ["solar", 3]]);

    const counts = applyTagList(c, { query: "offshore" });

    expect(visible(c)).toEqual(["wind offshore"]);
    expect(counts.matched).toBe(1);
  });

  it("ignores the limit while a query is active", () => {
    // Searching is how you reach a tag that the collapsed list hides, so a
    // limit applied on top of it would hide the very thing being looked for.
    const c = renderList([["wind a", 1], ["wind b", 2], ["wind c", 3]]);

    const counts = applyTagList(c, { query: "wind", limit: 1 });

    expect(visible(c)).toEqual(["wind a", "wind b", "wind c"]);
    expect(counts.shown).toBe(3);
  });

  it("reorders the list in place", () => {
    const c = renderList([["solar", 1], ["grid", 9]]);

    applyTagList(c, { sort: "usage" });

    expect(visible(c)).toEqual(["grid", "solar"]);
  });

  it("keeps a checked item visible even past the limit", () => {
    // A tag the reader has already selected must not vanish when the list
    // collapses, or the filter would be on with nothing to show for it.
    const c = renderList([["a", 1], ["b", 2], ["c", 3]]);
    const box = document.createElement("input");
    box.type = "checkbox";
    box.checked = true;
    c.children[2].appendChild(box);

    applyTagList(c, { limit: 1 });

    expect(visible(c)).toEqual(["a", "c"]);
  });
});

describe("bindTagList", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
  });

  /**
   * A list with the controls the templates render around it.
   *
   * @return {{container: HTMLElement, search: HTMLElement, expand: HTMLElement}}
   *   the wired elements.
   */
  function renderWithControls() {
    const container = renderList([["a", 1], ["b", 2], ["c", 3]]);
    const search = document.createElement("input");
    search.setAttribute("data-tag-search", "");
    const expand = document.createElement("button");
    expand.setAttribute("data-tag-expand", "");
    document.body.append(search, expand);
    return { container, search, expand };
  }

  it("collapses to the limit on load", () => {
    const { container } = renderWithControls();

    bindTagList(document, { limit: 2 });

    expect(visible(container)).toEqual(["a", "b"]);
  });

  it("filters as the reader types", () => {
    const { container, search } = renderWithControls();
    bindTagList(document, { limit: 2 });

    search.value = "c";
    search.dispatchEvent(new Event("input"));

    expect(visible(container)).toEqual(["c"]);
  });

  it("shows everything once expanded, and stays expanded", () => {
    const { container, search, expand } = renderWithControls();
    bindTagList(document, { limit: 2 });

    expand.click();
    expect(visible(container)).toEqual(["a", "b", "c"]);

    search.value = "";
    search.dispatchEvent(new Event("input"));
    expect(visible(container)).toEqual(["a", "b", "c"]);
  });

  it("hides the expand control when there is nothing to expand", () => {
    renderList([["only", 1]]);
    const expand = document.createElement("button");
    expand.setAttribute("data-tag-expand", "");
    document.body.append(expand);

    bindTagList(document, { limit: 10 });

    expect(expand.hidden).toBe(true);
  });

  it("does nothing at all without a list to bind", () => {
    document.body.innerHTML = "";

    expect(() => bindTagList(document, { limit: 10 })).not.toThrow();
  });
});
