// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// @vitest-environment happy-dom
//
// The tables tab swaps one results region. The live count, the focus and the
// search box all live outside it or across it, so they are browser state a
// Django test cannot see. htmx is not loaded here: its events are dispatched
// by hand with the detail htmx 1.9 gives them, which is the whole contract
// the module relies on.
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import {
  announce,
  bindTablesTab,
  controlValue,
  filterParameters,
  restoreFocus,
  syncFilters,
} from "../tables_tab.js";

/** The region, its `data-filters` written the way Django escapes it. */
const REGION = (announcement, filters = {}, body = "", more = 0, folded = 0) => `
  <div id="tables-results" data-announce="${announcement}"
       data-filters="${JSON.stringify(filters).replaceAll('"', "&quot;")}"
       data-more="${more}" data-folded="${folded}">
    <h2 id="tables-heading" tabindex="-1">Your tables</h2>
    ${body}
  </div>`;

function renderPage(region) {
  document.body.innerHTML = `
    <div id="tables-tab">
      <div id="tables-filters">
        <input type="search" id="tables-search" name="search" />
        <button type="button" id="tables-fold" aria-expanded="false"
                aria-controls="tables-fold-panel">Filters<span
                id="tables-fold-count"></span></button>
        <div id="tables-fold-panel">
        <select id="f-review" name="review">
          <option value="">Review: any</option>
          <option value="reviewed">Reviewed</option>
          <option value="in_review">In review</option>
        </select>
        <button type="button" id="tables-more" aria-expanded="false"
                aria-controls="tables-more-panel">More filters<span
                id="tables-more-count"></span></button>
        <div id="tables-more-panel" hidden>
          <input type="checkbox" id="f-tags-1" name="tags" value="grid" />
          <input type="checkbox" id="f-tags-2" name="tags" value="wind" />
          <input type="checkbox" id="f-tags-3" name="tags" value="solar" />
        </div>
        </div>
      </div>
      <div id="tables-live" aria-live="polite"></div>
      ${region}
    </div>`;
}

const configRequest = (elt, parameters) =>
  elt.dispatchEvent(
    new CustomEvent("htmx:configRequest", {
      bubbles: true,
      detail: { elt, parameters },
    }),
  );

/** Swap the region the way htmx's outerHTML swap does, firing its events. */
function swapRegion(html) {
  const old = document.getElementById("tables-results");
  const detail = { target: old };
  old.dispatchEvent(new CustomEvent("htmx:beforeSwap", { bubbles: true, detail }));
  const holder = document.createElement("div");
  holder.innerHTML = html;
  const fresh = holder.firstElementChild;
  old.replaceWith(fresh);
  fresh.dispatchEvent(new CustomEvent("htmx:afterSettle", { bubbles: true, detail }));
  return fresh;
}

const nextTick = () => new Promise((resolve) => setTimeout(resolve, 0));

describe("filterParameters", () => {
  it("keeps the status, the sort and other filters, and drops the page", () => {
    const params = filterParameters(
      "?status=draft&sort=-status&tags=grid&page=4",
      "search",
      "wind",
    );
    expect(params.get("status")).toBe("draft");
    expect(params.get("sort")).toBe("-status");
    expect(params.get("tags")).toBe("grid");
    expect(params.get("search")).toBe("wind");
    expect(params.has("page")).toBe(false);
  });

  it("leaves an empty value out instead of writing it empty", () => {
    const params = filterParameters("?review=reviewed&page=2", "review", "");
    expect(params.has("review")).toBe(false);
    expect(params.toString()).toBe("");
  });

  it("trims what was typed", () => {
    expect(filterParameters("", "search", "  wind ").get("search")).toBe("wind");
  });

  it("replaces a value that no longer applies", () => {
    const params = filterParameters("?dataset=gone", "dataset", "any");
    expect(params.getAll("dataset")).toEqual(["any"]);
  });
});

describe("controlValue", () => {
  beforeEach(() => renderPage(REGION("x")));

  it("joins the ticked values of a group in the bar's order", () => {
    const bar = document.getElementById("tables-filters");
    document.getElementById("f-tags-3").checked = true;
    document.getElementById("f-tags-1").checked = true;
    expect(controlValue(bar, document.getElementById("f-tags-3"))).toBe(
      "grid,solar",
    );
  });

  it("is empty when the last box is unticked", () => {
    const bar = document.getElementById("tables-filters");
    expect(controlValue(bar, document.getElementById("f-tags-2"))).toBe("");
  });

  it("is a select's value", () => {
    const bar = document.getElementById("tables-filters");
    const select = document.getElementById("f-review");
    select.value = "in_review";
    expect(controlValue(bar, select)).toBe("in_review");
  });
});

describe("announce", () => {
  it("re-announces an identical text by clearing first", async () => {
    const live = document.createElement("div");
    live.textContent = "4 tables, showing 1 to 4";
    const done = announce(live, "4 tables, showing 1 to 4", 0);
    expect(live.textContent).toBe("");
    await done;
    expect(live.textContent).toBe("4 tables, showing 1 to 4");
  });
});

describe("restoreFocus", () => {
  beforeEach(() => {
    renderPage(REGION("x", "", '<a id="pg-2" href="#">2</a>'));
  });

  it("focuses the control with the same id", () => {
    restoreFocus(document, "pg-2");
    expect(document.activeElement.id).toBe("pg-2");
  });

  it("falls back to the list heading when the control is gone", () => {
    restoreFocus(document, "pg-9");
    expect(document.activeElement.id).toBe("tables-heading");
  });

  it("leaves focus that already sits somewhere live", () => {
    document.getElementById("tables-search").focus();
    restoreFocus(document, "pg-2");
    expect(document.activeElement.id).toBe("tables-search");
  });

  it("does nothing when nothing in the region had focus", () => {
    restoreFocus(document, null);
    expect(document.activeElement).toBe(document.body);
  });
});

describe("syncFilters", () => {
  beforeEach(() => renderPage(REGION("x")));
  const region = () => document.getElementById("tables-results");

  it("follows the region when the user is not typing", () => {
    const input = document.getElementById("tables-search");
    input.value = "wind";
    syncFilters(document, region());
    expect(input.value).toBe("");
  });

  it("never overwrites what the user is typing", () => {
    const input = document.getElementById("tables-search");
    input.focus();
    input.value = "wind tur";
    syncFilters(document, region());
    expect(input.value).toBe("wind tur");
  });

  it("selects and ticks what the URL holds", () => {
    renderPage(REGION("x", { review: "in_review", tags: "grid,solar" }, "", 1));
    syncFilters(document, region());
    expect(document.getElementById("f-review").value).toBe("in_review");
    const ticked = ["f-tags-1", "f-tags-2", "f-tags-3"].map(
      (id) => document.getElementById(id).checked,
    );
    expect(ticked).toEqual([true, false, true]);
    expect(document.getElementById("tables-more-count").textContent).toBe(
      " (1)",
    );
  });

  it("shows a select's blank option for a value that no longer applies", () => {
    renderPage(REGION("x", { review: "excellent" }));
    document.getElementById("f-review").value = "reviewed";
    syncFilters(document, region());
    expect(document.getElementById("f-review").value).toBe("");
  });

  it("clears the bar after a Reset", () => {
    renderPage(REGION("x", {}));
    document.getElementById("f-review").value = "reviewed";
    document.getElementById("f-tags-2").checked = true;
    document.getElementById("tables-more-count").textContent = " (1)";
    syncFilters(document, region());
    expect(document.getElementById("f-review").value).toBe("");
    expect(document.getElementById("f-tags-2").checked).toBe(false);
    expect(document.getElementById("tables-more-count").textContent).toBe("");
  });
});

describe("bindTablesTab", () => {
  let unbind;

  beforeEach(() => {
    renderPage(REGION("130 tables, showing 1 to 25", {}, '<a id="pg-2" href="#">2</a>'));
    unbind = bindTablesTab(document, { announceDelay: 0 });
  });

  afterEach(() => unbind());

  it("writes the new count into the persistent live element", async () => {
    const live = document.getElementById("tables-live");
    swapRegion(REGION("12 tables match, showing 1 to 12", { search: "wind" }));
    await nextTick();
    expect(document.getElementById("tables-live")).toBe(live);
    expect(live.textContent).toBe("12 tables match, showing 1 to 12");
  });

  it("puts focus back on the control with the same id after a swap", () => {
    document.getElementById("pg-2").focus();
    swapRegion(REGION("x", {}, '<a id="pg-2" href="#">2</a>'));
    expect(document.activeElement.id).toBe("pg-2");
  });

  it("moves focus to the heading when the focused control is gone", () => {
    document.getElementById("pg-2").focus();
    swapRegion(REGION("x"));
    expect(document.activeElement.id).toBe("tables-heading");
  });

  it("clears the search box after a Reset", () => {
    const input = document.getElementById("tables-search");
    input.value = "wind";
    swapRegion(REGION("x", {}));
    expect(input.value).toBe("");
  });

  it("ignores swaps of other targets", async () => {
    const live = document.getElementById("tables-live");
    live.textContent = "before";
    const other = document.createElement("div");
    other.id = "elsewhere";
    document.body.appendChild(other);
    other.dispatchEvent(
      new CustomEvent("htmx:afterSettle", { bubbles: true, detail: { target: other } }),
    );
    await nextTick();
    expect(live.textContent).toBe("before");
  });

  it("rewrites the search request's parameters from the URL state", () => {
    window.history.replaceState({}, "", "/user/profile/1/tables?status=draft&page=3");
    const input = document.getElementById("tables-search");
    input.value = "wind";
    const parameters = { search: "wind" };
    input.dispatchEvent(
      new CustomEvent("htmx:configRequest", {
        bubbles: true,
        detail: { elt: input, parameters },
      }),
    );
    expect(parameters).toEqual({ status: "draft", search: "wind" });
  });

  it("rewrites a select's request, keeping the rest and dropping the page", () => {
    window.history.replaceState(
      {},
      "",
      "/user/profile/1/tables?search=wind&tags=grid&sort=-status&page=3",
    );
    const select = document.getElementById("f-review");
    select.value = "reviewed";
    const parameters = { review: "reviewed" };
    configRequest(select, parameters);
    expect(parameters).toEqual({
      search: "wind",
      tags: "grid",
      sort: "-status",
      review: "reviewed",
    });
  });

  it("sends a checkbox group's ticked values comma-joined", () => {
    window.history.replaceState({}, "", "/user/profile/1/tables?tags=grid");
    document.getElementById("f-tags-1").checked = true;
    const box = document.getElementById("f-tags-2");
    box.checked = true;
    const parameters = { tags: "wind" };
    configRequest(box, parameters);
    expect(parameters).toEqual({ tags: "grid,wind" });
  });

  it("drops the filter when its last box is unticked", () => {
    window.history.replaceState({}, "", "/user/profile/1/tables?tags=grid&status=draft");
    const box = document.getElementById("f-tags-1");
    const parameters = {};
    configRequest(box, parameters);
    expect(parameters).toEqual({ status: "draft" });
  });

  it("opens and closes More filters", () => {
    const button = document.getElementById("tables-more");
    const panel = document.getElementById("tables-more-panel");
    button.click();
    expect(button.getAttribute("aria-expanded")).toBe("true");
    expect(panel.hidden).toBe(false);
    button.click();
    expect(button.getAttribute("aria-expanded")).toBe("false");
    expect(panel.hidden).toBe(true);
  });

  it("keeps an open More filters panel and the bar's state across a swap", () => {
    document.getElementById("tables-more").click();
    swapRegion(REGION("x", { tags: "wind" }, "", 1));
    expect(document.getElementById("tables-more-panel").hidden).toBe(false);
    expect(document.getElementById("f-tags-2").checked).toBe(true);
    expect(document.getElementById("tables-more-count").textContent).toBe(" (1)");
  });

  it("rewrites the Sort by request, keeping the filters and dropping the page", () => {
    window.history.replaceState(
      {},
      "",
      "/user/profile/1/tables?search=wind&status=draft&sort=table&page=3",
    );
    swapRegion(
      REGION(
        "x",
        { search: "wind" },
        `<select id="sort-select" name="sort" data-list-sort>
           <option value="table">Table: A to Z</option>
           <option value="-review">Review: reviewed first</option>
         </select>`,
      ),
    );
    const select = document.getElementById("sort-select");
    select.value = "-review";
    const parameters = { sort: "-review" };
    configRequest(select, parameters);
    expect(parameters).toEqual({ search: "wind", status: "draft", sort: "-review" });
  });

  it("puts focus back on Sort by after the swap it caused", () => {
    const select = `<select id="sort-select" name="sort" data-list-sort></select>`;
    swapRegion(REGION("x", {}, select));
    document.getElementById("sort-select").focus();
    swapRegion(REGION("y", {}, select));
    expect(document.activeElement.id).toBe("sort-select");
  });

  it("opens and closes Filters, and leaves showing the panel to the CSS", () => {
    const button = document.getElementById("tables-fold");
    const panel = document.getElementById("tables-fold-panel");
    button.click();
    expect(button.getAttribute("aria-expanded")).toBe("true");
    button.click();
    expect(button.getAttribute("aria-expanded")).toBe("false");
    // above 900 px of list the panel is part of the row, toggle or not
    expect(panel.hidden).toBe(false);
  });

  it("keeps Filters (n) in step with the region", () => {
    const count = document.getElementById("tables-fold-count");
    swapRegion(REGION("x", { review: "reviewed", tags: "wind" }, "", 1, 2));
    expect(count.textContent).toBe(" (2)");
    swapRegion(REGION("x", {}, "", 0, 0));
    expect(count.textContent).toBe("");
  });

  it("keeps an open Filters panel open across a swap", () => {
    document.getElementById("tables-fold").click();
    swapRegion(REGION("x", { review: "reviewed" }, "", 0, 1));
    expect(document.getElementById("tables-fold").getAttribute("aria-expanded")).toBe(
      "true",
    );
  });

  it("leaves other requests' parameters alone", () => {
    const link = document.getElementById("pg-2");
    const parameters = { page: "2" };
    link.dispatchEvent(
      new CustomEvent("htmx:configRequest", {
        bubbles: true,
        detail: { elt: link, parameters },
      }),
    );
    expect(parameters).toEqual({ page: "2" });
  });
});
