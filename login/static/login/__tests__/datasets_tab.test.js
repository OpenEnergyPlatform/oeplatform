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
       <label for="tp-climate">Climate</label>
       <label for="tp-energy">Energy</label>
       <label for="tp-grid">Grid</label>`
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

  it("names up to two ticked options, then how many", () => {
    tick("tp-energy");
    expect($("f-topics-button").textContent).toBe("Topic: Energy");
    tick("tp-climate");
    expect($("f-topics-button").textContent).toBe("Topic: Climate, Energy");
    tick("tp-grid");
    expect($("f-topics-button").textContent).toBe("Topic: 3 ticked");
    for (const id of ["tp-grid", "tp-climate", "tp-energy"]) {
      tick(id, false);
    }
    expect($("f-topics-button").textContent).toBe("Topic: any");
  });

  it("follows a chip removed inside the region", () => {
    tick("tp-energy");
    swapRegion(region({ filters: '{"topics": "grid"}' }));
    expect($("f-topics-button").textContent).toBe("Topic: Grid");
  });
});
