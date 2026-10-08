// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// @vitest-environment happy-dom
//
// The datasets tab's binding (#2622): the generic list module with the
// datasets config, on a page shaped like the one the server renders, which
// offers no selection yet (no bulk bar, no row boxes). Live filters, the
// count announced from the live region outside the swapped region, and
// focus put back by id.
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { DATASETS, bindDatasetsTab } from "../datasets_tab.js";

function renderPage() {
  document.body.innerHTML = `
    <div id="datasets-tab" class="dash" data-login-url="/login/">
      <div id="datasets-filters" role="search">
        <input type="search" id="datasets-search" name="search" />
        <fieldset>
          <input type="checkbox" name="topics" value="climate" id="tp-climate" />
          <input type="checkbox" name="topics" value="energy" id="tp-energy" />
        </fieldset>
        <button type="button" id="datasets-more" aria-expanded="false"
                aria-controls="datasets-more-panel">More filters<span
                id="datasets-more-count"></span></button>
        <div id="datasets-more-panel" class="dash-more" hidden>
          <input type="date" name="created_from" id="created-from" />
        </div>
      </div>
      <div id="datasets-live" aria-live="polite"></div>
      ${region()}
    </div>
    <div id="dataset-action"><div id="dataset-action-body"></div></div>
    <div id="datasets-toasts-polite"></div>
    <div id="datasets-toasts-assertive"></div>`;
}

function region({ announcement = "2 datasets", filters = "{}", more = 0 } = {}) {
  return `
    <div id="datasets-results" data-scope="" data-announce="${announcement}"
         data-filters='${filters}' data-more="${more}">
      <h2 id="datasets-heading" tabindex="-1">Your datasets</h2>
      <a id="sort-created" href="?sort=created">Created</a>
      <a id="sort-tables" href="?sort=tables">Tables</a>
      <table><tbody>
        <tr id="row-1"><td class="c-select"></td>
          <td><button type="button" id="mb-1" aria-expanded="false"
                      aria-controls="mb-1-pop" data-dash-popover>3 tables</button>
            <div id="mb-1-pop" hidden><a href="/t/a">A</a></div></td>
          <td class="c-menu"></td></tr>
      </tbody></table>
    </div>`;
}

const $ = (id) => document.getElementById(id);
const click = (element) =>
  element.dispatchEvent(
    new MouseEvent("click", { bubbles: true, cancelable: true })
  );
const fire = (name, detail) =>
  document.body.dispatchEvent(new CustomEvent(name, { bubbles: true, detail }));
const settle = () => new Promise((resolve) => setTimeout(resolve, 0));

function swapRegion(html) {
  const old = $("datasets-results");
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

function configRequest(elt) {
  const parameters = { [elt.name]: elt.value };
  elt.dispatchEvent(
    new CustomEvent("htmx:configRequest", {
      bubbles: true,
      detail: { elt, parameters },
    })
  );
  return parameters;
}

function fakeOverlay() {
  const overlay = { opened: 0, closed: 0 };
  overlay.open = () => {
    overlay.opened += 1;
  };
  overlay.close = () => {
    overlay.closed += 1;
  };
  overlay.onHidden = () => {};
  return overlay;
}

describe("the datasets config", () => {
  it("names the datasets tab's ids and events", () => {
    expect(DATASETS.ids.region).toBe("datasets-results");
    expect(DATASETS.ids.live).toBe("datasets-live");
    expect(DATASETS.ids.dialog).toBe("dataset-action");
    expect(DATASETS.changedEvent).toBe("datasets-changed");
    expect(DATASETS.refusedEvent).toBe("datasets-refused");
    expect(DATASETS.selectionParam).toBe("datasets");
    expect(DATASETS.drawer.id).toBe("dataset-members");
    expect(DATASETS.drawer.origin).toBe("membersOrigin");
  });
});

describe("bindDatasetsTab", () => {
  let unbind;
  let dialog;

  beforeEach(() => {
    renderPage();
    window.history.replaceState(
      null,
      "",
      "/user/profile/1/datasets?sort=created&page=3&status=draft"
    );
    dialog = fakeOverlay();
    unbind = bindDatasetsTab(document, {
      announceDelay: 0,
      dialog,
      drawer: fakeOverlay(),
      schedule: () => {},
    });
  });

  afterEach(() => {
    unbind();
  });

  it("sends a filter with the rest of the state, back on page 1", () => {
    $("tp-energy").checked = true;
    $("tp-climate").checked = true;
    expect(configRequest($("tp-energy"))).toEqual({
      sort: "created",
      status: "draft",
      topics: "climate,energy",
    });
  });

  it("sends an emptied search as no parameter at all", () => {
    $("datasets-search").value = "  ";
    expect(configRequest($("datasets-search"))).toEqual({
      sort: "created",
      status: "draft",
    });
  });

  it("announces the count from the live region outside the swap", async () => {
    swapRegion(region({ announcement: "1 dataset matches, showing 1 to 1" }));
    await settle();
    expect($("datasets-live").textContent).toBe(
      "1 dataset matches, showing 1 to 1"
    );
  });

  it("puts focus back on the control with the same id after a swap", () => {
    $("sort-tables").focus();
    swapRegion(region());
    expect(document.activeElement).toBe($("sort-tables"));
    expect(document.activeElement).not.toBe(null);
  });

  it("puts focus on the heading when the control is gone", () => {
    $("sort-created").focus();
    swapRegion(region().replace(/<a id="sort-created"[^>]*>Created<\/a>/, ""));
    expect(document.activeElement).toBe($("datasets-heading"));
  });

  it("makes the bar follow a chip removed inside the region", () => {
    $("tp-energy").checked = true;
    $("datasets-search").value = "wind";
    swapRegion(
      region({ filters: '{"topics": "climate", "created_from": "2026-01-02"}', more: 1 })
    );
    expect($("tp-energy").checked).toBe(false);
    expect($("tp-climate").checked).toBe(true);
    expect($("datasets-search").value).toBe("");
    expect($("created-from").value).toBe("2026-01-02");
    expect($("datasets-more-count").textContent).toBe(" (1)");
  });

  it("opens and closes More filters", () => {
    click($("datasets-more"));
    expect($("datasets-more-panel").hidden).toBe(false);
    expect($("datasets-more").getAttribute("aria-expanded")).toBe("true");
    click($("datasets-more"));
    expect($("datasets-more-panel").hidden).toBe(true);
  });

  it("opens the Tables popover", () => {
    click($("mb-1"));
    expect($("mb-1-pop").hidden).toBe(false);
    expect($("mb-1").getAttribute("aria-expanded")).toBe("true");
  });

  it("lives without a bulk bar", () => {
    expect(() => {
      click($("row-1"));
      swapRegion(region());
    }).not.toThrow();
  });

  it("follows the datasets tab's events, not the tables tab's", () => {
    fire("tables-changed", { message: "Not for this list." });
    expect($("datasets-toasts-polite").children).toHaveLength(0);
    fire("datasets-changed", { message: "Published “Wind atlas”." });
    expect($("datasets-toasts-polite").textContent).toContain(
      "Published “Wind atlas”."
    );
    fire("datasets-refused", { message: "Nothing was changed." });
    expect($("datasets-toasts-assertive").textContent).toContain(
      "Nothing was changed."
    );
  });
});

describe("a multi-valued filter's dropdown", () => {
  let unbind;

  beforeEach(() => {
    renderPage();
    const fieldset = $("tp-climate").closest("fieldset");
    fieldset.insertAdjacentHTML(
      "beforebegin",
      `<button type="button" id="f-topics-button" data-multi-summary="topics"
               data-label="Topic" data-blank="Topic: any">Topic: any</button>`
    );
    fieldset.insertAdjacentHTML(
      "beforeend",
      `<input type="checkbox" name="topics" value="grid" id="tp-grid" />
`
    );
    unbind = bindDatasetsTab(document, {
      announceDelay: 0,
      dialog: fakeOverlay(),
      drawer: fakeOverlay(),
    });
  });

  afterEach(() => {
    unbind();
  });

  const tick = (id, on = true) => {
    $(id).checked = on;
    $(id).dispatchEvent(new Event("change", { bubbles: true }));
  };

  it("counts what is ticked", () => {
    tick("tp-energy");
    expect($("f-topics-button").textContent).toBe("Topic (1)");
    tick("tp-climate");
    tick("tp-grid");
    expect($("f-topics-button").textContent).toBe("Topic (3)");
    for (const id of ["tp-grid", "tp-climate", "tp-energy"]) {
      tick(id, false);
    }
    expect($("f-topics-button").textContent).toBe("Topic: any");
  });

  it("follows a chip removed inside the region", () => {
    tick("tp-energy");
    swapRegion(region({ filters: '{"topics": "grid"}' }));
    expect($("f-topics-button").textContent).toBe("Topic (1)");
  });
});

// The members drawer in the address (#2625): `?members=<name>` is page
// state, written with replaceState when the drawer opens and removed when it
// closes; on a load or a history restore the drawer opens by itself when the
// server marked the name as one of the user's (`data-open`); after a Create
// it opens on the new Dataset with focus in the add search.
describe("the members drawer in the address", () => {
  const LIST = "/user/profile/1/datasets";
  let unbind;
  let dialog;
  let drawer;
  let loaded;

  function drawerOverlay() {
    const overlay = fakeOverlay();
    overlay.hidden = [];
    overlay.shown = [];
    overlay.onHidden = (callback) => overlay.hidden.push(callback);
    overlay.onShown = (callback) => overlay.shown.push(callback);
    return overlay;
  }

  function mount({ open = null, address = `${LIST}?sort=created` } = {}) {
    renderPage();
    document.body.insertAdjacentHTML(
      "beforeend",
      `<div id="dataset-members"
            data-url-template="/user/profile/1/datasets/__key__/members"
            ${open ? `data-open="${open}" data-open-origin="menu-7"` : ""}>
         <div id="dataset-members-live" aria-live="polite"></div>
         <div id="dataset-members-body"></div>
       </div>`
    );
    $("datasets-results").insertAdjacentHTML(
      "beforeend",
      `<button type="button" id="menu-7">⋯</button>
       <button type="button" id="menu-7-members"
               data-members-origin="menu-7">Manage tables…</button>`
    );
    window.history.replaceState(null, "", address);
    dialog = fakeOverlay();
    dialog.hidden = [];
    dialog.onHidden = (callback) => dialog.hidden.push(callback);
    drawer = drawerOverlay();
    loaded = [];
    unbind = bindDatasetsTab(document, {
      announceDelay: 0,
      dialog,
      drawer,
      schedule: () => {},
      loadDrawer: (url) => loaded.push(url),
    });
  }

  // the drawer's contents arriving, as htmx swaps them
  function fill(key, requester = document.body, extra = "") {
    const body = $("dataset-members-body");
    const detail = { target: body, requestConfig: { elt: requester } };
    body.dispatchEvent(
      new CustomEvent("htmx:beforeSwap", { bubbles: true, detail })
    );
    body.innerHTML = `
      <h2 id="dataset-members-title" tabindex="-1" data-drawer-key="${key}"
          ${extra}>Tables in “${key}”</h2>
      <input type="search" id="dataset-members-add-search" />
      <button type="button" id="dataset-members-remove-1">Remove</button>
      <button type="button" id="dataset-members-remove-2">Remove</button>`;
    body.dispatchEvent(
      new CustomEvent("htmx:afterSwap", { bubbles: true, detail })
    );
    body.dispatchEvent(
      new CustomEvent("htmx:afterSettle", { bubbles: true, detail })
    );
  }

  const close = () => drawer.hidden.forEach((callback) => callback());
  const members = () =>
    new URLSearchParams(window.location.search).get("members");

  afterEach(() => {
    unbind();
  });

  it("is written on open, with no history entry, the rest kept", () => {
    mount();
    const entries = window.history.length;
    fill("wind_atlas", $("menu-7-members"));
    expect(drawer.opened).toBe(1);
    expect(members()).toBe("wind_atlas");
    expect(new URLSearchParams(window.location.search).get("sort")).toBe(
      "created"
    );
    expect(window.history.length).toBe(entries);
  });

  it("is removed on close, and focus goes back to the opener", () => {
    mount();
    fill("wind_atlas", $("menu-7-members"));
    close();
    expect(members()).toBeNull();
    expect(window.location.search).toBe("?sort=created");
    expect(document.activeElement).toBe($("menu-7"));
  });

  it("stays while a change in the drawer swaps it again", () => {
    mount();
    fill("wind_atlas", $("menu-7-members"));
    fill("wind_atlas", $("dataset-members-remove-1"));
    expect(drawer.opened).toBe(1);
    expect(members()).toBe("wind_atlas");
  });

  it("is put back when htmx writes the list's own address", () => {
    mount();
    fill("wind_atlas", $("menu-7-members"));
    window.history.replaceState(null, "", `${LIST}?sort=created`);
    fire("htmx:replacedInHistory", { path: `${LIST}?sort=created` });
    expect(members()).toBe("wind_atlas");
    close();
    fire("htmx:replacedInHistory", { path: `${LIST}?sort=created` });
    expect(members()).toBeNull();
  });

  it("is carried by no filter request", () => {
    mount({ address: `${LIST}?sort=created&members=wind_atlas` });
    $("datasets-search").value = "heat";
    expect(configRequest($("datasets-search"))).toEqual({
      sort: "created",
      search: "heat",
    });
  });

  it("reopens the drawer on load when the server names the Dataset", () => {
    mount({ open: "wind_atlas", address: `${LIST}?members=wind_atlas` });
    expect(loaded).toEqual(["/user/profile/1/datasets/wind_atlas/members"]);
    fill("wind_atlas");
    expect(drawer.opened).toBe(1);
    close();
    // closed, focus goes to the Dataset's ⋯, as if the menu had opened it
    expect(document.activeElement).toBe($("menu-7"));
    expect(members()).toBeNull();
  });

  it("ignores a name the server did not mark (foreign or unknown)", () => {
    mount({ address: `${LIST}?members=someone_elses` });
    expect(loaded).toEqual([]);
    expect(drawer.opened).toBe(0);
  });

  it("ignores a mark the address no longer carries", () => {
    mount({ open: "wind_atlas", address: `${LIST}?sort=created` });
    expect(loaded).toEqual([]);
  });

  it("reopens the drawer on a history restore", () => {
    mount();
    window.history.replaceState(null, "", `${LIST}?members=wind_atlas`);
    $("dataset-members").dataset.open = "wind_atlas";
    fire("htmx:historyRestore", { path: `${LIST}?members=wind_atlas` });
    expect(loaded).toEqual(["/user/profile/1/datasets/wind_atlas/members"]);
  });

  it("opens on a new Dataset after a Create, once the dialog has closed", () => {
    mount();
    fire("datasets-changed", { message: "Created.", created: "new_one" });
    expect(dialog.closed).toBe(1);
    // still showing: nothing loads yet
    expect(loaded).toEqual([]);
    dialog.hidden.forEach((callback) => callback());
    expect(loaded).toEqual(["/user/profile/1/datasets/new_one/members"]);
    fill("new_one");
    expect(drawer.opened).toBe(1);
    expect(members()).toBe("new_one");
    drawer.shown.forEach((callback) => callback());
    expect(document.activeElement).toBe($("dataset-members-add-search"));
  });

  it("focuses what the server names after a removal took the control away", () => {
    mount();
    fill("wind_atlas", $("menu-7-members"));
    $("dataset-members-remove-1").focus();
    fill(
      "wind_atlas",
      $("dataset-members-remove-1"),
      'data-drawer-focus="dataset-members-remove-2"'
    );
    expect(document.activeElement).toBe($("dataset-members-remove-2"));
  });

  it("says what a change did through the drawer's own live region", async () => {
    mount();
    fill("wind_atlas", $("menu-7-members"), 'data-announce="Added “Grid”."');
    await settle();
    expect($("dataset-members-live").textContent).toBe("Added “Grid”.");
  });
});
