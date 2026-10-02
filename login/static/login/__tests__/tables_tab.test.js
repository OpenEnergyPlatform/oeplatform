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
  restoreFocus,
  searchParameters,
  syncSearch,
} from "../tables_tab.js";

const REGION = (announcement, search = "", body = "") => `
  <div id="tables-results" data-announce="${announcement}" data-search="${search}">
    <h2 id="tables-heading" tabindex="-1">Your tables</h2>
    ${body}
  </div>`;

function renderPage(region) {
  document.body.innerHTML = `
    <div id="tables-tab">
      <input type="search" id="tables-search" name="search" />
      <div id="tables-live" aria-live="polite"></div>
      ${region}
    </div>`;
}

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

describe("searchParameters", () => {
  it("keeps the status and the sort, and drops the page", () => {
    const params = searchParameters("?status=draft&sort=-status&page=4", "wind");
    expect(params.get("status")).toBe("draft");
    expect(params.get("sort")).toBe("-status");
    expect(params.get("search")).toBe("wind");
    expect(params.has("page")).toBe(false);
  });

  it("leaves an empty search out instead of writing search=", () => {
    const params = searchParameters("?search=wind&status=draft", "   ");
    expect(params.has("search")).toBe(false);
    expect(params.toString()).toBe("status=draft");
  });

  it("trims what was typed", () => {
    expect(searchParameters("", "  solar ").get("search")).toBe("solar");
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

describe("syncSearch", () => {
  beforeEach(() => renderPage(REGION("x", "")));

  it("follows the region when the user is not typing", () => {
    const input = document.getElementById("tables-search");
    input.value = "wind";
    syncSearch(document, document.getElementById("tables-results"));
    expect(input.value).toBe("");
  });

  it("never overwrites what the user is typing", () => {
    const input = document.getElementById("tables-search");
    input.focus();
    input.value = "wind tur";
    syncSearch(document, document.getElementById("tables-results"));
    expect(input.value).toBe("wind tur");
  });
});

describe("bindTablesTab", () => {
  let unbind;

  beforeEach(() => {
    renderPage(REGION("130 tables, showing 1 to 25", "", '<a id="pg-2" href="#">2</a>'));
    unbind = bindTablesTab(document, { announceDelay: 0 });
  });

  afterEach(() => unbind());

  it("writes the new count into the persistent live element", async () => {
    const live = document.getElementById("tables-live");
    swapRegion(REGION("12 tables match, showing 1 to 12", "wind"));
    await nextTick();
    expect(document.getElementById("tables-live")).toBe(live);
    expect(live.textContent).toBe("12 tables match, showing 1 to 12");
  });

  it("puts focus back on the control with the same id after a swap", () => {
    document.getElementById("pg-2").focus();
    swapRegion(REGION("x", "", '<a id="pg-2" href="#">2</a>'));
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
    swapRegion(REGION("x", ""));
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
