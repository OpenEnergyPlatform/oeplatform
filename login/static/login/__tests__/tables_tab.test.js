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
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  LOGGED_OUT,
  SELECTION_CLEARED,
  SERVER_FAILED,
  UNREACHABLE,
  announce,
  bindTablesTab,
  controlValue,
  filterParameters,
  focusAfterAction,
  isUnavailable,
  loginLink,
  rangeOf,
  renderSelection,
  restoreDrawerFocus,
  restoreFocus,
  rowBoxes,
  showToast,
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
          <input type="date" id="f-modified_from" name="modified_from" />
          <input type="date" id="f-modified_to" name="modified_to" />
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

  it("fills both ends of a date range from the URL", () => {
    renderPage(
      REGION("x", { modified_from: "2026-10-02", modified_to: "2026-10-03" }),
    );
    syncFilters(document, region());
    expect(document.getElementById("f-modified_from").value).toBe("2026-10-02");
    expect(document.getElementById("f-modified_to").value).toBe("2026-10-03");
  });

  it("empties both ends once the range's one chip is removed", () => {
    renderPage(REGION("x", { search: "wind" }));
    document.getElementById("f-modified_from").value = "2026-10-02";
    document.getElementById("f-modified_to").value = "2026-10-03";
    syncFilters(document, region());
    expect(document.getElementById("f-modified_from").value).toBe("");
    expect(document.getElementById("f-modified_to").value).toBe("");
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

  it("sends one end of a date range, keeping the other", () => {
    window.history.replaceState(
      {},
      "",
      "/user/profile/1/tables?modified_from=2026-10-01&page=2",
    );
    const end = document.getElementById("f-modified_to");
    end.value = "2026-10-03";
    const parameters = { modified_to: "2026-10-03" };
    configRequest(end, parameters);
    expect(parameters).toEqual({
      modified_from: "2026-10-01",
      modified_to: "2026-10-03",
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

/** One row's ⋯ menu: an action entry, and one above the user's role. */
const ROW_MENU = (pk) => `
  <button id="menu-${pk}" type="button">⋯</button>
  <button id="menu-${pk}-publish" type="button"
          data-action-origin="menu-${pk}">Publish…</button>
  <button id="menu-${pk}-unpublish" type="button" aria-disabled="true">
    Unpublish <span>Only Table admins can unpublish</span></button>`;

/** The page around the region: dialog body and the two toast regions. */
function renderActionPage(region) {
  renderPage(region);
  const tab = document.getElementById("tables-tab");
  tab.dataset.loginUrl = "/user/login/";
  document.body.insertAdjacentHTML(
    "beforeend",
    `<div id="table-action"><div id="table-action-body"></div></div>
     <div id="tables-toasts-polite" aria-live="polite"></div>
     <div id="tables-toasts-assertive" aria-live="assertive"></div>`,
  );
}

/** A dialog that records what was asked of it, like Bootstrap's modal. */
function fakeDialog() {
  const dialog = { opened: 0, closed: 0, hidden: null };
  dialog.open = () => {
    dialog.opened += 1;
  };
  dialog.close = () => {
    dialog.closed += 1;
  };
  dialog.onHidden = (callback) => {
    dialog.hidden = callback;
  };
  return dialog;
}

/** htmx 1.9's swap events for the dialog body, as a menu entry or the
 * dialog's form causes them: dispatched on the target, with `elt` set to
 * the target and the requesting element in `requestConfig.elt`. */
function swapDialog(source, status = 200) {
  const target = document.getElementById("table-action-body");
  const detail = {
    elt: target,
    target,
    requestConfig: { elt: source },
    xhr: { status },
    shouldSwap: status < 300,
    isError: status >= 400,
  };
  const fire = (name) =>
    target.dispatchEvent(new CustomEvent(name, { bubbles: true, detail }));
  fire("htmx:beforeSwap");
  if (detail.shouldSwap) {
    fire("htmx:afterSwap");
  }
  return detail;
}

/** An `HX-Trigger` response header's event, as htmx dispatches it. */
const serverTrigger = (elt, name, detail) =>
  elt.dispatchEvent(new CustomEvent(name, { bubbles: true, detail }));

describe("focusAfterAction", () => {
  beforeEach(() => renderActionPage(REGION("x", {}, ROW_MENU(7))));

  it("focuses the row's ⋯", () => {
    focusAfterAction(document, "menu-7");
    expect(document.activeElement.id).toBe("menu-7");
  });

  it("falls back to the list heading when the row is gone", () => {
    focusAfterAction(document, "menu-99");
    expect(document.activeElement.id).toBe("tables-heading");
  });

  it("moves focus even when something else holds it", () => {
    document.getElementById("tables-search").focus();
    focusAfterAction(document, "menu-7");
    expect(document.activeElement.id).toBe("menu-7");
  });
});

describe("isUnavailable", () => {
  beforeEach(() => renderActionPage(REGION("x", {}, ROW_MENU(7))));

  it("is true inside an entry marked aria-disabled", () => {
    const reason = document.querySelector("#menu-7-unpublish span");
    expect(isUnavailable(reason)).toBe(true);
  });

  it("is false for an available entry", () => {
    const entry = document.getElementById("menu-7-publish");
    expect(isUnavailable(entry)).toBe(false);
  });
});

describe("showToast", () => {
  beforeEach(() => renderActionPage(REGION("x")));

  it("puts a success in the polite region and removes it after the timeout", () => {
    let later = null;
    const toast = showToast(document, "Published “Go” under climate.", {
      schedule: (callback, ms) => {
        later = [callback, ms];
      },
    });
    const polite = document.getElementById("tables-toasts-polite");
    expect(polite.contains(toast)).toBe(true);
    expect(toast.textContent).toContain("Published “Go” under climate.");
    expect(later[1]).toBe(5000);
    later[0]();
    expect(polite.contains(toast)).toBe(false);
  });

  it("puts an error in the assertive region and leaves it until dismissed", () => {
    const schedule = vi.fn();
    const toast = showToast(document, "Nothing was changed: …", {
      error: true,
      schedule,
    });
    const assertive = document.getElementById("tables-toasts-assertive");
    expect(assertive.contains(toast)).toBe(true);
    expect(schedule).not.toHaveBeenCalled();
    toast.querySelector('button[aria-label="Dismiss"]').click();
    expect(toast.isConnected).toBe(false);
  });

  it("puts a warning in the assertive region and leaves it until dismissed", () => {
    const schedule = vi.fn();
    const toast = showToast(document, "Deleted “Go”. The database table…", {
      warning: true,
      schedule,
    });
    const assertive = document.getElementById("tables-toasts-assertive");
    expect(assertive.contains(toast)).toBe(true);
    expect(toast.classList.contains("dash-toast--warning")).toBe(true);
    expect(schedule).not.toHaveBeenCalled();
  });

  it("writes the message as text, never as markup", () => {
    const toast = showToast(document, "<img src=x>", { error: true });
    expect(toast.querySelector("img")).toBeNull();
  });
});

describe("loginLink", () => {
  it("comes back to this view, filters included", () => {
    renderActionPage(REGION("x"));
    const here = "/user/profile/3/tables?status=draft";
    window.history.replaceState(null, "", here);
    expect(loginLink(document)).toEqual({
      href: "/user/login/?next=%2Fuser%2Fprofile%2F3%2Ftables%3Fstatus%3Ddraft",
      text: "Log in again",
    });
  });
});

describe("bindTablesTab, actions", () => {
  let unbind;
  let dialog;

  beforeEach(() => {
    renderActionPage(REGION("2 tables", {}, ROW_MENU(7) + ROW_MENU(8)));
    dialog = fakeDialog();
    unbind = bindTablesTab(document, {
      announceDelay: 0,
      dialog,
      schedule: () => {},
    });
  });

  afterEach(() => unbind());

  it("opens the dialog once a menu entry has filled it", () => {
    swapDialog(document.getElementById("menu-7-publish"));
    expect(dialog.opened).toBe(1);
  });

  it("swaps a refusal or a field error into the open dialog", () => {
    const form = document.createElement("form");
    document.getElementById("table-action-body").append(form);
    for (const status of [409, 400]) {
      const detail = swapDialog(form, status);
      expect(detail.shouldSwap).toBe(true);
      expect(detail.isError).toBe(false);
    }
    expect(dialog.opened).toBe(0);
  });

  it("leaves other failed swaps as errors", () => {
    const detail = swapDialog(document.getElementById("menu-7-publish"), 500);
    expect(detail.shouldSwap).toBe(false);
    expect(detail.isError).toBe(true);
  });

  it("swallows a click on an entry above the user's role", () => {
    const seen = vi.fn();
    document.addEventListener("click", seen);
    const reason = document.querySelector("#menu-7-unpublish span");
    const event = new MouseEvent("click", { bubbles: true, cancelable: true });
    reason.dispatchEvent(event);
    document.removeEventListener("click", seen);
    expect(event.defaultPrevented).toBe(true);
    expect(seen).not.toHaveBeenCalled();
  });

  it("lets a click on an available entry through", () => {
    const seen = vi.fn();
    document.addEventListener("click", seen);
    document.getElementById("menu-7-publish").click();
    document.removeEventListener("click", seen);
    expect(seen).toHaveBeenCalled();
  });

  it("after an action closes the dialog, says so, then focuses the row", () => {
    const entry = document.getElementById("menu-7-publish");
    swapDialog(entry);
    serverTrigger(entry, "tables-changed", {
      message: "Published “Go” under climate.",
      focus: "menu-7",
    });
    expect(dialog.closed).toBe(1);
    expect(
      document.getElementById("tables-toasts-polite").textContent,
    ).toContain("Published “Go” under climate.");
    // the dialog's own button held focus; the region comes back without it
    swapRegion(REGION("1 table", {}, ROW_MENU(7)));
    expect(document.activeElement.id).toBe("menu-7");
  });

  it("focuses the list heading when the row has left the list", () => {
    const entry = document.getElementById("menu-8-publish");
    swapDialog(entry);
    serverTrigger(entry, "tables-changed", {
      message: "Done.",
      focus: "menu-8",
    });
    swapRegion(REGION("1 table", {}, ROW_MENU(7)));
    expect(document.activeElement.id).toBe("tables-heading");
  });

  it("falls back to the opening row when the server names no row", () => {
    const entry = document.getElementById("menu-8-publish");
    swapDialog(entry);
    serverTrigger(entry, "tables-changed", { message: "Done." });
    swapRegion(REGION("2 tables", {}, ROW_MENU(7) + ROW_MENU(8)));
    expect(document.activeElement.id).toBe("menu-8");
  });

  it("returns focus to the ⋯ when the dialog is cancelled", () => {
    swapDialog(document.getElementById("menu-8-publish"));
    dialog.hidden();
    expect(document.activeElement.id).toBe("menu-8");
  });

  it("only moves focus once after an action, then swaps restore as before", () => {
    const entry = document.getElementById("menu-7-publish");
    swapDialog(entry);
    serverTrigger(entry, "tables-changed", {
      message: "Done.",
      focus: "menu-7",
    });
    swapRegion(REGION("x", {}, ROW_MENU(7)));
    document.getElementById("tables-search").focus();
    swapRegion(REGION("x", {}, ROW_MENU(7)));
    expect(document.activeElement.id).toBe("tables-search");
  });

  it("after a delete focuses the list heading, the row being gone", () => {
    const entry = document.getElementById("menu-8-publish");
    swapDialog(entry);
    serverTrigger(entry, "tables-changed", { message: "Deleted “Go”." });
    swapRegion(REGION("1 table", {}, ROW_MENU(7)));
    expect(document.activeElement.id).toBe("tables-heading");
  });

  it("keeps a delete whose database table stayed behind on screen", () => {
    const entry = document.getElementById("menu-8-publish");
    swapDialog(entry);
    serverTrigger(entry, "tables-changed", {
      message: "Deleted “Go”. The database table of “Go” (go) could not…",
      warning: true,
    });
    expect(dialog.closed).toBe(1);
    const assertive = document.getElementById("tables-toasts-assertive");
    expect(assertive.textContent).toContain("could not");
    expect(assertive.querySelector(".dash-toast--warning")).not.toBeNull();
    expect(document.getElementById("tables-toasts-polite").textContent).toBe(
      "",
    );
  });

  it("keeps a refusal on screen, assertively", () => {
    serverTrigger(document.body, "tables-refused", {
      message: "Nothing was changed: Already published (“t”).",
    });
    const assertive = document.getElementById("tables-toasts-assertive");
    expect(assertive.textContent).toContain("Nothing was changed");
    expect(dialog.closed).toBe(0);
  });

  it("tells a logged-out user so, with a way back", () => {
    const here = "/user/profile/3/tables?status=draft";
    window.history.replaceState(null, "", here);
    document.body.dispatchEvent(
      new CustomEvent("htmx:responseError", {
        bubbles: true,
        detail: { xhr: { status: 401 } },
      }),
    );
    const toast = document.getElementById("tables-toasts-assertive");
    expect(toast.textContent).toContain(LOGGED_OUT);
    expect(toast.querySelector("a").getAttribute("href")).toBe(
      "/user/login/?next=%2Fuser%2Fprofile%2F3%2Ftables%3Fstatus%3Ddraft",
    );
  });

  it("says a server error may have left the change undone", () => {
    document.body.dispatchEvent(
      new CustomEvent("htmx:responseError", {
        bubbles: true,
        detail: { xhr: { status: 500 } },
      }),
    );
    expect(
      document.getElementById("tables-toasts-assertive").textContent,
    ).toContain(SERVER_FAILED);
  });

  it("says so when the server cannot be reached", () => {
    document.body.dispatchEvent(
      new CustomEvent("htmx:sendError", { bubbles: true, detail: {} }),
    );
    expect(
      document.getElementById("tables-toasts-assertive").textContent,
    ).toContain(UNREACHABLE);
  });
});

/** A row's two drawer openers: its Access cell and "Manage access". */
const ROW_ACCESS = (pk) => `
  <button id="acc-${pk}" type="button" data-access-origin="acc-${pk}">You</button>
  <button id="menu-${pk}" type="button">⋯</button>
  <button id="menu-${pk}-access" type="button"
          data-access-origin="menu-${pk}">Manage access</button>`;

/** The drawer's contents as the server renders them. */
const DRAWER_BODY = (extra = "") => `
  <h2 id="table-access-title" tabindex="-1">Access to Go</h2>
  ${extra}
  <select id="access-role-user-3" name="level"></select>
  <button id="access-remove-user-3" type="button">Remove</button>`;

/** htmx 1.9's swap of the drawer body: events on the target, the
 * requesting element in `requestConfig.elt`, the contents replaced
 * between beforeSwap and afterSettle. */
function swapDrawer(source, status = 200, html = DRAWER_BODY()) {
  const target = document.getElementById("table-access-body");
  const detail = {
    elt: target,
    target,
    requestConfig: { elt: source },
    xhr: { status },
    shouldSwap: status < 300,
    isError: status >= 400,
  };
  const fire = (name) =>
    target.dispatchEvent(new CustomEvent(name, { bubbles: true, detail }));
  fire("htmx:beforeSwap");
  if (detail.shouldSwap) {
    target.innerHTML = html;
    fire("htmx:afterSwap");
    fire("htmx:afterSettle");
  }
  return detail;
}

describe("restoreDrawerFocus", () => {
  beforeEach(() => {
    document.body.innerHTML = `<div id="table-access-body">${DRAWER_BODY()}</div>`;
  });

  it("does nothing when focus was not in the drawer", () => {
    restoreDrawerFocus(document, null);
    expect(document.activeElement).toBe(document.body);
  });

  it("puts focus back on the same control", () => {
    restoreDrawerFocus(document, "access-role-user-3");
    expect(document.activeElement.id).toBe("access-role-user-3");
  });

  it("falls back to the title when the control is gone", () => {
    restoreDrawerFocus(document, "access-remove-user-9");
    expect(document.activeElement.id).toBe("table-access-title");
  });

  it("prefers the confirmation question when the server asks one", () => {
    document
      .getElementById("table-access-body")
      .insertAdjacentHTML(
        "afterbegin",
        '<div id="table-access-confirm-box" tabindex="-1">Sure?</div>',
      );
    restoreDrawerFocus(document, "access-remove-user-3");
    expect(document.activeElement.id).toBe("table-access-confirm-box");
  });
});

describe("bindTablesTab, access drawer", () => {
  let unbind;
  let dialog;
  let drawer;

  beforeEach(() => {
    renderActionPage(REGION("2 tables", {}, ROW_ACCESS(7) + ROW_ACCESS(8)));
    document.body.insertAdjacentHTML(
      "beforeend",
      '<div id="table-access"><div id="table-access-body"></div></div>',
    );
    dialog = fakeDialog();
    drawer = fakeDialog();
    unbind = bindTablesTab(document, {
      announceDelay: 0,
      dialog,
      drawer,
      schedule: () => {},
    });
  });

  afterEach(() => unbind());

  it("opens the drawer once the Access cell or the menu has filled it", () => {
    swapDrawer(document.getElementById("acc-7"));
    swapDrawer(document.getElementById("menu-8-access"));
    expect(drawer.opened).toBe(2);
    expect(dialog.opened).toBe(0);
  });

  it("does not reopen it for a write made inside it", () => {
    swapDrawer(document.getElementById("acc-7"));
    const form = document.createElement("form");
    document.getElementById("table-access-body").append(form);
    swapDrawer(form);
    expect(drawer.opened).toBe(1);
  });

  it("swaps a refusal, a not-an-Admin and a field error into the drawer", () => {
    const form = document.createElement("form");
    document.getElementById("table-access-body").append(form);
    for (const status of [400, 403, 409]) {
      const detail = swapDrawer(form, status);
      expect(detail.shouldSwap).toBe(true);
      expect(detail.isError).toBe(false);
    }
    const failed = swapDrawer(form, 500);
    expect(failed.shouldSwap).toBe(false);
    expect(failed.isError).toBe(true);
  });

  it("keeps focus on the control used after a change", () => {
    swapDrawer(document.getElementById("acc-7"));
    document.getElementById("access-role-user-3").focus();
    swapDrawer(document.getElementById("access-role-user-3"));
    expect(document.activeElement.id).toBe("access-role-user-3");
  });

  it("moves focus to a confirmation question", () => {
    swapDrawer(document.getElementById("acc-7"));
    document.getElementById("access-remove-user-3").focus();
    swapDrawer(
      document.getElementById("access-remove-user-3"),
      200,
      DRAWER_BODY(
        '<div id="table-access-confirm-box" tabindex="-1">Sure?</div>',
      ),
    );
    expect(document.activeElement.id).toBe("table-access-confirm-box");
  });

  it("after a change says so, but stays open and keeps focus", () => {
    swapDrawer(document.getElementById("acc-7"));
    const select = document.getElementById("access-role-user-3");
    select.focus();
    serverTrigger(select, "tables-changed", {
      message: "AccessAlice is now Admin on “Go”.",
      stay: true,
    });
    expect(drawer.closed).toBe(0);
    expect(dialog.closed).toBe(0);
    expect(
      document.getElementById("tables-toasts-polite").textContent,
    ).toContain("AccessAlice is now Admin");
    // the list re-fetches behind the drawer and leaves focus where it is
    swapRegion(REGION("2 tables", {}, ROW_ACCESS(7) + ROW_ACCESS(8)));
    expect(document.activeElement.id).toBe("access-role-user-3");
  });

  it("returns focus to what opened it when it closes", () => {
    swapDrawer(document.getElementById("menu-8-access"));
    drawer.hidden();
    expect(document.activeElement.id).toBe("menu-8");
  });

  it("returns focus to the list heading when that row has left", () => {
    swapDrawer(document.getElementById("acc-8"));
    swapRegion(REGION("1 table", {}, ROW_ACCESS(7)));
    drawer.hidden();
    expect(document.activeElement.id).toBe("tables-heading");
  });
});

// ---------------------------------------------------------------------------
// The selection and the bulk bar (#2564). The region says which scope it
// shows (`data-scope`) and how many Tables match (the banner's
// `data-total`); everything else is page memory.

/** A region of `names` rows, under `scope`, out of `total` matching. */
const SELECT_REGION = (names, { scope = "", total = names.length } = {}) => `
  <div id="tables-results" data-announce="x" data-filters="{}"
       data-more="0" data-folded="0" data-scope="${scope}">
    <h2 id="tables-heading" tabindex="-1">Your tables</h2>
    <div id="tables-select-all" data-total="${total}"
         data-names-url="/names${scope}" hidden>
      <span data-when="page">All on this page are selected.</span>
      <button type="button" id="tables-select-matching"
              data-when="page">Select all ${total} matching tables</button>
      <span data-when="all">All ${total} matching tables are selected.</span>
      <button type="button" id="tables-select-none"
              data-when="all">Clear selection</button>
    </div>
    <table><thead><tr><th>
      <input type="checkbox" id="select-page" data-select-page />
    </th></tr></thead><tbody>
    ${names
      .map(
        (name, i) => `<tr><td><input type="checkbox" id="select-${i}"
          value="${name}" data-select-row aria-label="Select ${name}" />
          </td></tr>`,
      )
      .join("")}
    </tbody></table>
  </div>`;

/** The page with the bulk bar outside the region. */
function renderSelectPage(region) {
  renderActionPage(region);
  document
    .getElementById("tables-live")
    .insertAdjacentHTML(
      "beforebegin",
      `<div id="tables-bulk">
         <p id="tables-bulk-idle" aria-hidden="true">Tick tables to act on several at once.</p>
         <p id="tables-bulk-note" role="status"></p>
         <div id="tables-bulk-bar" hidden>
           <span id="tables-bulk-count"></span>
           <button type="button" id="tables-bulk-clear">Clear</button>
           <button type="button" id="bulk-publish" data-bulk-action
                   data-action-origin="bulk-publish">Publish…</button>
         </div>
       </div>`,
    );
}

const box = (name) =>
  [...document.querySelectorAll("input[data-select-row]")].find(
    (b) => b.value === name,
  );

/** A click as a browser makes it: a checkbox toggles, then the event. */
function tick(element, { shiftKey = false } = {}) {
  element.dispatchEvent(
    new MouseEvent("click", { bubbles: true, cancelable: true, shiftKey }),
  );
}

const ticked = () => rowBoxes(document.getElementById("tables-results"))
  .filter((b) => b.checked)
  .map((b) => b.value);

const requestParameters = (elt) => {
  const parameters = {};
  elt.dispatchEvent(
    new CustomEvent("htmx:configRequest", {
      bubbles: true,
      detail: { elt, parameters },
    }),
  );
  return parameters;
};

describe("rangeOf", () => {
  beforeEach(() => renderPage(SELECT_REGION(["a", "b", "c", "d"])));

  it("runs from one row to the other in page order, either way", () => {
    const boxes = rowBoxes(document.getElementById("tables-results"));
    expect(rangeOf(boxes, "b", "d")).toEqual(["b", "c", "d"]);
    expect(rangeOf(boxes, "d", "b")).toEqual(["b", "c", "d"]);
  });

  it("is the one row when the other end is not on this page", () => {
    const boxes = rowBoxes(document.getElementById("tables-results"));
    expect(rangeOf(boxes, "zz", "c")).toEqual(["c"]);
  });
});

describe("renderSelection", () => {
  beforeEach(() =>
    renderSelectPage(SELECT_REGION(["a", "b"], { total: 130 })),
  );

  it("reserves the bar's slot with the muted line while nothing is selected", () => {
    renderSelection(document, new Set());
    expect(document.getElementById("tables-bulk-bar").hidden).toBe(true);
    const idle = document.getElementById("tables-bulk-idle");
    expect(idle.hidden).toBe(false);
    expect(idle.getAttribute("aria-hidden")).toBe("true");
  });

  it("turns the slot into the bar with the count on the first tick", () => {
    renderSelection(document, new Set(["a"]));
    expect(document.getElementById("tables-bulk-bar").hidden).toBe(false);
    expect(document.getElementById("tables-bulk-idle").hidden).toBe(true);
    expect(document.getElementById("tables-bulk-count").textContent).toBe(
      "1 selected",
    );
  });

  it("makes the header box indeterminate for part of the page", () => {
    renderSelection(document, new Set(["a"]));
    const header = document.getElementById("select-page");
    expect(header.checked).toBe(false);
    expect(header.indeterminate).toBe(true);
    renderSelection(document, new Set(["a", "b"]));
    expect(header.checked).toBe(true);
    expect(header.indeterminate).toBe(false);
  });

  it("offers every matching table once the page is ticked", () => {
    const banner = document.getElementById("tables-select-all");
    renderSelection(document, new Set(["a"]));
    expect(banner.hidden).toBe(true);
    renderSelection(document, new Set(["a", "b"]));
    expect(banner.hidden).toBe(false);
    expect(
      document.getElementById("tables-select-matching").hidden,
    ).toBe(false);
    expect(document.getElementById("tables-select-none").hidden).toBe(true);
  });

  it("offers nothing more when the page holds every matching table", () => {
    renderSelectPage(SELECT_REGION(["a", "b"], { total: 2 }));
    renderSelection(document, new Set(["a", "b"]));
    expect(document.getElementById("tables-select-all").hidden).toBe(true);
  });
});

describe("bindTablesTab, selection", () => {
  let unbind;
  let dialog;
  let fetchNames;

  beforeEach(() => {
    renderSelectPage(
      SELECT_REGION(["a", "b", "c", "d"], { scope: "?status=draft", total: 6 }),
    );
    dialog = fakeDialog();
    fetchNames = vi.fn(async () => ["a", "b", "c", "d", "e", "f"]);
    unbind = bindTablesTab(document, {
      announceDelay: 0,
      dialog,
      schedule: () => {},
      fetchNames,
    });
  });

  afterEach(() => unbind());

  it("ticks and unticks a row", () => {
    tick(box("b"));
    expect(ticked()).toEqual(["b"]);
    expect(document.getElementById("tables-bulk-count").textContent).toBe(
      "1 selected",
    );
    tick(box("b"));
    expect(ticked()).toEqual([]);
    expect(document.getElementById("tables-bulk-bar").hidden).toBe(true);
  });

  it("ticks a range with Shift+click", () => {
    tick(box("a"));
    tick(box("c"), { shiftKey: true });
    expect(ticked()).toEqual(["a", "b", "c"]);
  });

  it("unticks a range with Shift+click on a ticked row", () => {
    for (const name of ["a", "b", "c", "d"]) {
      tick(box(name));
    }
    tick(box("b"));
    tick(box("d"), { shiftKey: true });
    expect(ticked()).toEqual(["a"]);
  });

  it("ticks the page with the header box, and unticks it again", () => {
    tick(box("a"));
    const header = document.getElementById("select-page");
    tick(header);
    expect(ticked()).toEqual(["a", "b", "c", "d"]);
    tick(header);
    expect(ticked()).toEqual([]);
  });

  it("keeps the selection across paging and sorting", () => {
    tick(box("a"));
    // page 2 of the same scope, then back, sorted differently
    swapRegion(SELECT_REGION(["e", "f"], { scope: "?status=draft", total: 6 }));
    expect(document.getElementById("tables-bulk-count").textContent).toBe(
      "1 selected",
    );
    tick(box("e"));
    swapRegion(
      SELECT_REGION(["d", "c", "b", "a"], { scope: "?status=draft", total: 6 }),
    );
    expect(ticked()).toEqual(["a"]);
    expect(document.getElementById("tables-bulk-count").textContent).toBe(
      "2 selected",
    );
  });

  it("clears the selection with a note when the filters change", () => {
    tick(box("a"));
    swapRegion(SELECT_REGION(["a", "b"], { scope: "?status=published" }));
    expect(ticked()).toEqual([]);
    expect(document.getElementById("tables-bulk-bar").hidden).toBe(true);
    expect(document.getElementById("tables-bulk-note").textContent).toBe(
      SELECTION_CLEARED,
    );
    expect(document.getElementById("tables-bulk-idle").hidden).toBe(true);
    // the next tick replaces the note with the bar
    tick(box("b"));
    expect(document.getElementById("tables-bulk-note").textContent).toBe("");
  });

  it("says nothing when the filters change with nothing selected", () => {
    swapRegion(SELECT_REGION(["a"], { scope: "?search=x" }));
    expect(document.getElementById("tables-bulk-note").textContent).toBe("");
    expect(document.getElementById("tables-bulk-idle").hidden).toBe(false);
  });

  it("selects every matching table with one request, then can clear it", async () => {
    tick(document.getElementById("select-page"));
    tick(document.getElementById("tables-select-matching"));
    await nextTick();
    expect(fetchNames).toHaveBeenCalledWith("/names?status=draft");
    expect(document.getElementById("tables-bulk-count").textContent).toBe(
      "6 selected",
    );
    expect(document.getElementById("tables-select-none").hidden).toBe(false);
    expect(document.activeElement.id).toBe("tables-select-none");
    tick(document.getElementById("tables-select-none"));
    expect(document.getElementById("tables-bulk-bar").hidden).toBe(true);
    expect(document.activeElement.id).toBe("select-page");
  });

  it("lets a table be unticked after selecting every matching one", async () => {
    tick(document.getElementById("select-page"));
    tick(document.getElementById("tables-select-matching"));
    await nextTick();
    tick(box("b"));
    expect(document.getElementById("tables-bulk-count").textContent).toBe(
      "5 selected",
    );
    expect(document.getElementById("tables-select-all").hidden).toBe(true);
  });

  it("drops names that arrive after the filters changed", async () => {
    let answer;
    fetchNames.mockImplementation(
      () => new Promise((resolve) => (answer = resolve)),
    );
    tick(document.getElementById("select-page"));
    tick(document.getElementById("tables-select-matching"));
    swapRegion(SELECT_REGION(["x"], { scope: "?search=x" }));
    answer(["a", "b", "c", "d", "e", "f"]);
    await nextTick();
    expect(document.getElementById("tables-bulk-bar").hidden).toBe(true);
  });

  it("says when the names could not be fetched", async () => {
    fetchNames.mockRejectedValue(Object.assign(new Error("x"), { status: 401 }));
    tick(document.getElementById("select-page"));
    tick(document.getElementById("tables-select-matching"));
    await nextTick();
    expect(
      document.getElementById("tables-toasts-assertive").textContent,
    ).toContain(LOGGED_OUT);
    expect(document.getElementById("tables-bulk-count").textContent).toBe(
      "4 selected",
    );
  });

  it("sends exactly the selected names with a bulk action", () => {
    tick(box("a"));
    tick(box("c"));
    const parameters = requestParameters(
      document.getElementById("bulk-publish"),
    );
    expect(parameters.tables).toBe("a,c");
  });

  it("empties the bar with Clear and moves focus to the header box", () => {
    tick(box("a"));
    document.getElementById("tables-bulk-clear").focus();
    tick(document.getElementById("tables-bulk-clear"));
    expect(ticked()).toEqual([]);
    expect(document.getElementById("tables-bulk-bar").hidden).toBe(true);
    expect(document.activeElement.id).toBe("select-page");
  });

  it("keeps the selection after an action, ticked again on the new region", () => {
    tick(box("a"));
    tick(box("b"));
    const button = document.getElementById("bulk-publish");
    swapDialog(button);
    expect(dialog.opened).toBe(1);
    serverTrigger(button, "tables-changed", {
      message: "Published 2 tables under climate.",
      tables: ["“A”", "“B”"],
    });
    swapRegion(
      SELECT_REGION(["a", "b", "c", "d"], { scope: "?status=draft", total: 6 }),
    );
    expect(ticked()).toEqual(["a", "b"]);
    // focus goes back to the bar's button, which the swap left alone
    expect(document.activeElement.id).toBe("bulk-publish");
  });

  it("lets go of the tables that left the dashboard", () => {
    tick(box("a"));
    tick(box("b"));
    serverTrigger(document.body, "tables-changed", {
      message: "Deleted 1 table.",
      gone: ["b"],
    });
    swapRegion(SELECT_REGION(["a", "c", "d"], { scope: "?status=draft" }));
    expect(ticked()).toEqual(["a"]);
    expect(document.getElementById("tables-bulk-count").textContent).toBe(
      "1 selected",
    );
  });

  it("lets go of a table the access drawer took off the dashboard", () => {
    tick(box("c"));
    serverTrigger(document.body, "tables-changed", {
      message: "You left “C”.",
      stay: true,
      gone: ["c"],
    });
    expect(document.getElementById("tables-bulk-bar").hidden).toBe(true);
  });

  it("lists a bulk success's tables under Show tables", () => {
    serverTrigger(document.body, "tables-changed", {
      message: "Published 2 tables under climate.",
      tables: ["“A”", "“B”"],
    });
    const toast = document.querySelector("#tables-toasts-polite .dash-toast");
    expect(toast.textContent).toContain("Published 2 tables under climate.");
    const more = toast.querySelector(".dash-toast__more");
    const list = toast.querySelector(".dash-toast__list");
    expect(list.hidden).toBe(true);
    more.click();
    expect(list.hidden).toBe(false);
    expect([...list.children].map((li) => li.textContent)).toEqual([
      "“A”",
      "“B”",
    ]);
    expect(more.getAttribute("aria-expanded")).toBe("true");
  });
});

describe("showToast, Show tables", () => {
  beforeEach(() => renderActionPage(REGION("x")));

  it("stays once opened, rather than vanishing while being read", () => {
    const pending = [];
    const toast = showToast(document, "Published 2 tables.", {
      details: ["“A”", "“B”"],
      schedule: (fn) => pending.push(fn),
    });
    toast.querySelector(".dash-toast__more").click();
    pending.forEach((fn) => fn());
    expect(toast.isConnected).toBe(true);
  });

  it("goes after the timeout when nobody opened it", () => {
    const pending = [];
    const toast = showToast(document, "Published 2 tables.", {
      details: ["“A”", "“B”"],
      schedule: (fn) => pending.push(fn),
    });
    pending.forEach((fn) => fn());
    expect(toast.isConnected).toBe(false);
  });
});
