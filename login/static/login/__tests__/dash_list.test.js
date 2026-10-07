// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// @vitest-environment happy-dom
//
// The generic list module, bound with a config that is not the tables tab's
// (#2617): other ids, other event names, another selection parameter, a
// drawer of another name. The tables tab's own suite proves the behaviour
// through its wrapper; this one proves the wiring follows the config rather
// than the tables tab's values, which the wrapper alone could not show.
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { DIALOG_CLOSED, bindList, listConfig } from "../dash_list.js";

const WIDGETS = listConfig({
  plural: "widgets",
  singular: "widget",
  drawer: "members",
});

function renderPage({ scope = "" } = {}) {
  document.body.innerHTML = `
    <div id="widgets-tab" data-login-url="/login/">
      <div id="widgets-filters">
        <input type="search" id="widgets-search" name="search" />
        <button type="button" id="widgets-more" aria-expanded="false"
                aria-controls="widgets-more-panel">More</button>
        <div id="widgets-more-panel" hidden></div>
      </div>
      <div id="widgets-bulk">
        <p id="widgets-bulk-idle">Tick widgets.</p>
        <p id="widgets-bulk-note" role="status"></p>
        <div id="widgets-bulk-bar" hidden>
          <span id="widgets-bulk-count"></span>
          <button type="button" id="widgets-bulk-clear">Clear</button>
          <button type="button" id="bulk-delete" data-bulk-action
                  data-action-origin="bulk-delete">Delete</button>
        </div>
      </div>
      <div id="widgets-live" aria-live="polite"></div>
      ${region(scope)}
    </div>
    <div id="widget-action"><div id="widget-action-body"></div></div>
    <div id="widget-members"><div id="widget-members-body"></div></div>
    <div id="widgets-toasts-polite"></div>
    <div id="widgets-toasts-assertive"></div>
    <div id="tables-toasts-polite"></div>
    <div id="tables-toasts-assertive"></div>`;
}

function region(scope, announcement = "2 widgets") {
  return `
    <div id="widgets-results" data-scope="${scope}"
         data-announce="${announcement}" data-filters="{}">
      <h2 id="widgets-heading" tabindex="-1">Your widgets</h2>
      <input type="checkbox" id="select-page" data-select-page />
      <input type="checkbox" id="row-a" data-select-row value="alpha" />
      <input type="checkbox" id="row-b" data-select-row value="beta" />
      <button type="button" id="menu-alpha">⋯</button>
      <button type="button" id="members-alpha"
              data-members-origin="members-alpha">Members</button>
    </div>`;
}

const $ = (id) => document.getElementById(id);
const click = (element, init = {}) =>
  element.dispatchEvent(
    new MouseEvent("click", { bubbles: true, cancelable: true, ...init })
  );
const fire = (name, detail) =>
  document.body.dispatchEvent(new CustomEvent(name, { bubbles: true, detail }));

function swapRegion(html) {
  const old = $("widgets-results");
  const detail = { target: old };
  old.dispatchEvent(
    new CustomEvent("htmx:beforeSwap", { bubbles: true, detail })
  );
  const holder = document.createElement("div");
  holder.innerHTML = html;
  const fresh = holder.firstElementChild;
  old.replaceWith(fresh);
  fresh.dispatchEvent(
    new CustomEvent("htmx:afterSettle", { bubbles: true, detail })
  );
}

function fakeOverlay() {
  const overlay = { opened: 0, closed: 0, hidden: [] };
  overlay.open = () => {
    overlay.opened += 1;
  };
  overlay.close = () => {
    overlay.closed += 1;
  };
  overlay.onHidden = (callback) => overlay.hidden.push(callback);
  return overlay;
}

describe("listConfig", () => {
  it("builds every id from the nouns", () => {
    expect(WIDGETS.ids.region).toBe("widgets-results");
    expect(WIDGETS.ids.dialogBody).toBe("widget-action-body");
    expect(WIDGETS.ids.selectPage).toBe("select-page");
    expect(WIDGETS.changedEvent).toBe("widgets-changed");
    expect(WIDGETS.refusedEvent).toBe("widgets-refused");
    expect(WIDGETS.selectionParam).toBe("widgets");
    expect(WIDGETS.drawer).toEqual({
      id: "widget-members",
      body: "widget-members-body",
      title: "widget-members-title",
      confirm: "widget-members-confirm-box",
      origin: "membersOrigin",
    });
  });

  it("names no drawer for a list without one", () => {
    expect(listConfig({ plural: "a", singular: "b" }).drawer).toBeNull();
  });
});

describe("bindList with another list's config", () => {
  let unbind;
  let dialog;
  let drawer;

  beforeEach(() => {
    renderPage({ scope: "status=draft" });
    dialog = fakeOverlay();
    drawer = fakeOverlay();
    unbind = bindList(document, WIDGETS, {
      announceDelay: 0,
      dialog,
      drawer,
      schedule: () => {},
    });
  });

  afterEach(() => {
    unbind();
  });

  it("selects into the list's bulk bar", () => {
    click($("row-a"));
    expect($("row-a").checked).toBe(true);
    expect($("widgets-bulk-bar").hidden).toBe(false);
    expect($("widgets-bulk-count").textContent).toBe("1 selected");
  });

  it("sends the selection as the list's own parameter", () => {
    click($("row-a"));
    click($("row-b"));
    const parameters = {};
    $("bulk-delete").dispatchEvent(
      new CustomEvent("htmx:configRequest", {
        bubbles: true,
        detail: { elt: $("bulk-delete"), parameters },
      })
    );
    expect(parameters).toEqual({ widgets: "alpha,beta" });
  });

  it("announces the swapped region in the list's live element", async () => {
    swapRegion(region("status=draft", "1 widget"));
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect($("widgets-live").textContent).toBe("1 widget");
  });

  it("clears the selection when the list's region changes scope", () => {
    click($("row-a"));
    swapRegion(region("status=published"));
    expect($("widgets-bulk-bar").hidden).toBe(true);
    expect($("widgets-bulk-note").textContent).toMatch(/selection was cleared/);
  });

  it("follows the list's changed event, not the tables tab's", () => {
    fire("tables-changed", { message: "Not for this list." });
    expect(dialog.closed).toBe(0);
    expect($("widgets-toasts-polite").children).toHaveLength(0);

    fire("widgets-changed", {
      message: "Deleted 2 widgets.",
      widgets: ["alpha", "beta"],
      gone: ["alpha"],
    });
    expect(dialog.closed).toBe(1);
    const toast = $("widgets-toasts-polite").firstElementChild;
    expect(toast.textContent).toContain("Deleted 2 widgets.");
    // a batch's items are listed under the list's own noun
    expect(toast.querySelector("button").textContent).toBe("Show widgets");
    expect(
      [...toast.querySelectorAll("li")].map((li) => li.textContent)
    ).toEqual(["alpha", "beta"]);
    expect($("tables-toasts-polite").children).toHaveLength(0);
  });

  it("follows the list's refused event, not the tables tab's", () => {
    fire("tables-refused", { message: "Not for this list." });
    expect($("widgets-toasts-assertive").children).toHaveLength(0);
    fire("widgets-refused", { message: "Nothing was changed." });
    expect($("widgets-toasts-assertive").textContent).toContain(
      "Nothing was changed."
    );
  });

  it("opens the list's drawer from its own origin attribute", () => {
    const body = $("widget-members-body");
    body.dispatchEvent(
      new CustomEvent("htmx:afterSwap", {
        bubbles: true,
        detail: {
          target: body,
          elt: body,
          requestConfig: { elt: $("members-alpha") },
        },
      })
    );
    expect(drawer.opened).toBe(1);
    // closed, focus goes back to what opened it
    drawer.hidden.forEach((callback) => callback());
    expect(document.activeElement).toBe($("members-alpha"));
  });

  it("links a 401 to the login page the list's tab names", () => {
    fire("htmx:responseError", { xhr: { status: 401 } });
    const link = $("widgets-toasts-assertive").querySelector("a");
    expect(link.getAttribute("href")).toMatch(/^\/login\/\?next=/);
  });
});

describe("bindList for a list without a drawer", () => {
  it("binds and ignores swaps into another list's drawer", () => {
    renderPage();
    const dialog = fakeOverlay();
    const unbind = bindList(
      document,
      listConfig({ plural: "widgets", singular: "widget" }),
      { announceDelay: 0, dialog }
    );
    const body = $("widget-members-body");
    expect(() =>
      body.dispatchEvent(
        new CustomEvent("htmx:afterSwap", {
          bubbles: true,
          detail: {
            target: body,
            requestConfig: { elt: $("members-alpha") },
          },
        })
      )
    ).not.toThrow();
    unbind();
  });
});

describe("a dialog link that opens something else (close before open)", () => {
  let unbind;
  let dialog;
  let sent;

  beforeEach(() => {
    renderPage();
    $("widget-action-body").innerHTML = `
      <p>This widget cannot be published yet.</p>
      <a href="#" id="gate-edit" data-close-then
         hx-trigger="${DIALOG_CLOSED}" data-action-origin="menu-alpha">Edit…</a>`;
    dialog = fakeOverlay();
    unbind = bindList(document, WIDGETS, {
      announceDelay: 0,
      dialog,
      drawer: fakeOverlay(),
      schedule: () => {},
    });
    sent = [];
    $("gate-edit").addEventListener(DIALOG_CLOSED, (event) => sent.push(event));
  });

  afterEach(() => {
    unbind();
  });

  const hidden = () => dialog.hidden.forEach((callback) => callback());

  it("closes the dialog and opens the target only once it has closed", () => {
    const event = new MouseEvent("click", { bubbles: true, cancelable: true });
    $("gate-edit").dispatchEvent(event);
    expect(event.defaultPrevented).toBe(true);
    expect(dialog.closed).toBe(1);
    // still showing: the target must not open yet
    expect(sent).toHaveLength(0);

    hidden();
    expect(sent).toHaveLength(1);
    expect(sent[0].target).toBe($("gate-edit"));
  });

  it("opens the target once, not again when the dialog closes later", () => {
    click($("gate-edit"));
    hidden();
    hidden();
    expect(sent).toHaveLength(1);
  });

  // the dialog as a row's ⋯ opened it
  const openedFromTheRow = () => {
    $("menu-alpha").dataset.actionOrigin = "menu-alpha";
    $("widget-action-body").dispatchEvent(
      new CustomEvent("htmx:afterSwap", {
        bubbles: true,
        detail: {
          target: $("widget-action-body"),
          requestConfig: { elt: $("menu-alpha") },
        },
      })
    );
  };

  it("leaves focus to what the target opens, not the row's ⋯", () => {
    openedFromTheRow();
    click($("gate-edit"));
    hidden();
    expect(document.activeElement).not.toBe($("menu-alpha"));
  });

  it("still sends focus back to the row's ⋯ when cancelled", () => {
    openedFromTheRow();
    hidden();
    expect(document.activeElement).toBe($("menu-alpha"));
    expect(sent).toHaveLength(0);
  });

  it("opens nothing when the dialog is only cancelled", () => {
    hidden();
    expect(sent).toHaveLength(0);
  });

  it("ignores the marker outside the dialog", () => {
    const outside = document.createElement("a");
    outside.setAttribute("data-close-then", "");
    $("widgets-results").append(outside);
    outside.addEventListener(DIALOG_CLOSED, (event) => sent.push(event));
    const event = new MouseEvent("click", { bubbles: true, cancelable: true });
    outside.dispatchEvent(event);
    expect(event.defaultPrevented).toBe(false);
    expect(dialog.closed).toBe(0);
    hidden();
    expect(sent).toHaveLength(0);
  });
});
