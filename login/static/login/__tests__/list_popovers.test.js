// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// @vitest-environment happy-dom
//
// A list cell's popover: the server renders the button and its hidden
// panel; the browser opens one at a time, moves focus in so the links are
// reachable, and gives focus back on Escape.
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { bindPopovers } from "../list_popovers.js";
import { bindTablesTab } from "../tables_tab.js";

const CELL = (id, inside) => `
  <button type="button" id="${id}" aria-expanded="false"
          aria-controls="${id}-pop" data-dash-popover>open ${id}</button>
  <div id="${id}-pop" tabindex="-1" hidden>${inside}</div>`;

function render() {
  document.body.innerHTML = `
    <button type="button" id="elsewhere">elsewhere</button>
    <div id="tables-results">
      ${CELL("pub-1", '<a id="pub-1-spdx" href="#spdx">SPDX</a> <a href="#edit">Edit</a>')}
      ${CELL("ds-1", '<a id="ds-1-first" href="#d">dataset</a>')}
      ${CELL("tp-1", '<span class="chip">energy</span>')}
    </div>`;
}

const $ = (id) => document.getElementById(id);
const click = (element) =>
  element.dispatchEvent(new MouseEvent("click", { bubbles: true }));
const press = (key) =>
  document.activeElement.dispatchEvent(
    new KeyboardEvent("keydown", { key, bubbles: true }),
  );

describe("list popovers", () => {
  let popovers;

  beforeEach(() => {
    render();
    popovers = bindPopovers(document);
  });

  afterEach(() => {
    popovers.unbind();
  });

  it("opens on click and says so", () => {
    click($("pub-1"));
    expect($("pub-1-pop").hidden).toBe(false);
    expect($("pub-1").getAttribute("aria-expanded")).toBe("true");
  });

  it("moves focus to the first link inside, so the links are reachable", () => {
    $("pub-1").focus();
    click($("pub-1"));
    expect(document.activeElement).toBe($("pub-1-spdx"));
  });

  it("focuses the panel itself when it holds no link", () => {
    click($("tp-1"));
    expect(document.activeElement).toBe($("tp-1-pop"));
  });

  it("closes on Escape and gives focus back to its button", () => {
    click($("ds-1"));
    expect(document.activeElement).toBe($("ds-1-first"));
    press("Escape");
    expect($("ds-1-pop").hidden).toBe(true);
    expect($("ds-1").getAttribute("aria-expanded")).toBe("false");
    expect(document.activeElement).toBe($("ds-1"));
  });

  it("keeps one open at a time", () => {
    click($("pub-1"));
    click($("ds-1"));
    expect($("pub-1-pop").hidden).toBe(true);
    expect($("pub-1").getAttribute("aria-expanded")).toBe("false");
    expect($("ds-1-pop").hidden).toBe(false);
  });

  it("toggles closed on a second click of its button", () => {
    click($("pub-1"));
    click($("pub-1"));
    expect($("pub-1-pop").hidden).toBe(true);
    expect(document.activeElement).toBe($("pub-1"));
  });

  it("closes on a click outside, leaving focus where the click put it", () => {
    click($("pub-1"));
    click($("elsewhere"));
    expect($("pub-1-pop").hidden).toBe(true);
  });

  it("stays open for a click inside", () => {
    click($("pub-1"));
    click($("pub-1-spdx"));
    expect($("pub-1-pop").hidden).toBe(false);
  });

  it("closes when focus moves elsewhere", () => {
    click($("pub-1"));
    $("elsewhere").focus();
    expect($("pub-1-pop").hidden).toBe(true);
  });

  it("treats a swapped-out popover as closed", () => {
    click($("pub-1"));
    $("tables-results").outerHTML = `<div id="tables-results">${CELL(
      "pub-1",
      '<a href="#spdx">SPDX</a>',
    )}</div>`;
    expect(popovers.current()).toBe(null);
    press("Escape");
    expect($("pub-1-pop").hidden).toBe(true);
  });

  it("leaves Escape alone when nothing is open", () => {
    $("elsewhere").focus();
    press("Escape");
    expect(document.activeElement).toBe($("elsewhere"));
  });
});

describe("the tables tab", () => {
  it("wires the popovers and unwires them again", () => {
    render();
    const unbind = bindTablesTab(document);
    click($("pub-1"));
    expect($("pub-1-pop").hidden).toBe(false);
    press("Escape");
    unbind();
    click($("pub-1"));
    expect($("pub-1-pop").hidden).toBe(true);
  });
});
