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
  SERVER_FAILED,
  UNREACHABLE,
  announce,
  bindTablesTab,
  controlValue,
  filterParameters,
  focusAfterAction,
  isUnavailable,
  loginLink,
  restoreFocus,
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
