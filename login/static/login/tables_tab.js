// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// The profile dashboard's tables tab, in the browser (spec #2551).
//
// The server renders every state, a direct load and an htmx request alike;
// htmx swaps only the results region. What is left for the browser is what
// the region cannot carry across its own replacement:
//
// - the live count: one persistent, visually hidden `aria-live` element
//   OUTSIDE the region, rewritten after each swap from the region's
//   `data-announce`. A live region that is itself replaced is not announced
//   reliably.
// - focus: every control in the region has a stable id; focus goes back to
//   the element with the same id after a swap, or to the list heading when
//   that control is gone (the page it pointed at, say).
// - the search box, which sits outside the region so typing survives a
//   swap: its request keeps every other part of the URL state and returns to
//   page 1, and it follows the region's `data-search` when something else
//   changed it (a Reset).
//
// Newer requests replace older ones through `hx-sync` on the tab, so a
// stale response never overwrites a newer state. The cells' popovers are
// `list_popovers.js`, wired here so the page has one thing to bind.

import { bindPopovers } from "./list_popovers.js";

export const REGION_ID = "tables-results";
export const HEADING_ID = "tables-heading";
export const LIVE_ID = "tables-live";
export const SEARCH_ID = "tables-search";

/**
 * The query a new search sends: every other parameter of the current state
 * kept, the page dropped (a filter change returns to page 1), an empty
 * search left out (defaults are never written).
 *
 * @param {string} currentSearch the current `location.search`.
 * @param {string} text what the search box holds.
 * @return {URLSearchParams} the parameters of the new request.
 */
export function searchParameters(currentSearch, text) {
  const params = new URLSearchParams(currentSearch);
  const value = text.trim();
  if (value) {
    params.set("search", value);
  } else {
    params.delete("search");
  }
  params.delete("page");
  return params;
}

/**
 * Write `text` into the live element so that it is announced, also when it
 * equals what was announced last: clear first, then set.
 *
 * @param {Element} live the persistent `aria-live` element.
 * @param {string} text what to announce.
 * @param {number} delay ms between clearing and setting.
 * @return {Promise<void>} resolves once the text is set.
 */
export function announce(live, text, delay = 60) {
  live.textContent = "";
  return new Promise((resolve) => {
    setTimeout(() => {
      live.textContent = text;
      resolve();
    }, delay);
  });
}

/**
 * The id of the focused control, if it sits inside `region`.
 *
 * @param {Document} doc the document.
 * @param {Element} region the region about to be swapped.
 * @return {string|null} the id to restore after the swap.
 */
export function focusedIdWithin(doc, region) {
  const active = doc.activeElement;
  if (active && active.id && region && region.contains(active)) {
    return active.id;
  }
  return null;
}

/**
 * Put focus back after a swap: on the control with the same id, or on the
 * list heading when that control is gone. Focus that already sits somewhere
 * live (htmx restores an id it finds, and the search box is outside the
 * region) is left alone.
 *
 * @param {Document} doc the document.
 * @param {string|null} id the id focused before the swap.
 */
export function restoreFocus(doc, id) {
  if (!id) {
    return;
  }
  const active = doc.activeElement;
  if (active && active !== doc.body && active.isConnected) {
    return;
  }
  const target = doc.getElementById(id) || doc.getElementById(HEADING_ID);
  if (target) {
    target.focus();
  }
}

/**
 * Make the search box hold what the region says the search is, unless the
 * user is typing in it.
 *
 * @param {Document} doc the document.
 * @param {Element} region the current region.
 */
export function syncSearch(doc, region) {
  const input = doc.getElementById(SEARCH_ID);
  if (!input || !region || doc.activeElement === input) {
    return;
  }
  const value = region.dataset.search || "";
  if (input.value !== value) {
    input.value = value;
  }
}

/**
 * Wire the tab to htmx's events on `doc`.
 *
 * @param {Document} doc the document.
 * @param {{announceDelay: number}} options test seams.
 * @return {function(): void} removes the listeners again.
 */
export function bindTablesTab(doc, { announceDelay = 60 } = {}) {
  let focusedId = null;
  const isRegion = (event) =>
    event.detail && event.detail.target && event.detail.target.id === REGION_ID;

  const onConfigRequest = (event) => {
    const elt = event.detail.elt;
    if (!elt || elt.id !== SEARCH_ID) {
      return;
    }
    const parameters = event.detail.parameters;
    for (const key of Object.keys(parameters)) {
      delete parameters[key];
    }
    for (const [key, value] of searchParameters(
      doc.location.search,
      elt.value,
    )) {
      parameters[key] = value;
    }
  };

  const onBeforeSwap = (event) => {
    if (isRegion(event)) {
      focusedId = focusedIdWithin(doc, event.detail.target);
    }
  };

  const onAfterSettle = (event) => {
    if (!isRegion(event)) {
      return;
    }
    const region = doc.getElementById(REGION_ID);
    const live = doc.getElementById(LIVE_ID);
    if (region && live) {
      announce(live, region.dataset.announce || "", announceDelay);
    }
    syncSearch(doc, region);
    restoreFocus(doc, focusedId);
    focusedId = null;
  };

  const onHistoryRestore = () => {
    syncSearch(doc, doc.getElementById(REGION_ID));
  };

  const listeners = [
    ["htmx:configRequest", onConfigRequest],
    ["htmx:beforeSwap", onBeforeSwap],
    ["htmx:afterSettle", onAfterSettle],
    ["htmx:historyRestore", onHistoryRestore],
  ];
  for (const [name, listener] of listeners) {
    doc.body.addEventListener(name, listener);
  }
  const popovers = bindPopovers(doc);
  return () => {
    for (const [name, listener] of listeners) {
      doc.body.removeEventListener(name, listener);
    }
    popovers.unbind();
  };
}
