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
// - the filter bar, which sits outside the region so typing and an open
//   "More filters" panel survive a swap. Each control's request keeps every
//   other part of the URL state and returns to page 1; a multi-valued filter
//   sends its ticked values comma-joined. After a swap every control follows
//   the region's `data-filters` (what the URL holds) unless the user is in
//   it, so a chip removed or a Reset inside the region shows in the bar, and
//   "More filters (n)" follows `data-more`.
//
// Newer requests replace older ones through `hx-sync` on the tab, so a
// stale response never overwrites a newer state. The cells' popovers are
// `list_popovers.js`, wired here so the page has one thing to bind.

import { bindPopovers } from "./list_popovers.js";

export const REGION_ID = "tables-results";
export const HEADING_ID = "tables-heading";
export const LIVE_ID = "tables-live";
export const SEARCH_ID = "tables-search";
export const FILTERS_ID = "tables-filters";
export const MORE_ID = "tables-more";
export const MORE_COUNT_ID = "tables-more-count";

/**
 * The query a changed filter sends: every other parameter of the current
 * state kept, the page dropped (a filter change returns to page 1), an empty
 * value left out (defaults are never written).
 *
 * @param {string} currentSearch the current `location.search`.
 * @param {string} name the filter's parameter.
 * @param {string} value its new value, comma-joined if several.
 * @return {URLSearchParams} the parameters of the new request.
 */
export function filterParameters(currentSearch, name, value) {
  const params = new URLSearchParams(currentSearch);
  const trimmed = value.trim();
  if (trimmed) {
    params.set(name, trimmed);
  } else {
    params.delete(name);
  }
  params.delete("page");
  return params;
}

/**
 * What a bar control says its filter is: the ticked values of its group for
 * a checkbox, in the order the bar lists them, otherwise its value.
 *
 * @param {Element} bar the filter bar.
 * @param {Element} control the control that changed.
 * @return {string} the filter's new value.
 */
export function controlValue(bar, control) {
  if (control.type !== "checkbox") {
    return control.value;
  }
  return [...bar.querySelectorAll('input[type="checkbox"]')]
    .filter((box) => box.name === control.name && box.checked)
    .map((box) => box.value)
    .join(",");
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
 * Make every bar control hold what the region says the URL holds, except the
 * one the user is in. A select whose value is not among its options (a value
 * that no longer applies) shows its blank option.
 *
 * @param {Document} doc the document.
 * @param {Element} region the current region.
 */
export function syncFilters(doc, region) {
  const bar = doc.getElementById(FILTERS_ID);
  if (!bar || !region) {
    return;
  }
  let state = {};
  try {
    state = JSON.parse(region.dataset.filters || "{}");
  } catch {
    state = {};
  }
  for (const control of bar.querySelectorAll("[name]")) {
    if (control === doc.activeElement && control.type !== "checkbox") {
      continue;
    }
    const value = state[control.name] || "";
    if (control.type === "checkbox") {
      control.checked = value.split(",").includes(control.value);
    } else if (control.tagName === "SELECT") {
      const known = [...control.options].some((o) => o.value === value);
      control.value = known ? value : "";
    } else if (control.value !== value) {
      control.value = value;
    }
  }
  const count = doc.getElementById(MORE_COUNT_ID);
  if (count) {
    const more = Number(region.dataset.more || 0);
    count.textContent = more ? ` (${more})` : "";
  }
}

/**
 * Open or close the "More filters" panel.
 *
 * @param {Document} doc the document.
 * @param {Element} button the "More filters" button.
 */
export function toggleMore(doc, button) {
  const panel = doc.getElementById(button.getAttribute("aria-controls"));
  if (!panel) {
    return;
  }
  const open = button.getAttribute("aria-expanded") !== "true";
  button.setAttribute("aria-expanded", String(open));
  panel.hidden = !open;
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
    const bar = doc.getElementById(FILTERS_ID);
    if (!elt || !elt.name || !bar || !bar.contains(elt)) {
      return;
    }
    const parameters = event.detail.parameters;
    for (const key of Object.keys(parameters)) {
      delete parameters[key];
    }
    for (const [key, value] of filterParameters(
      doc.location.search,
      elt.name,
      controlValue(bar, elt),
    )) {
      parameters[key] = value;
    }
  };

  const onClick = (event) => {
    const button = event.target.closest && event.target.closest(`#${MORE_ID}`);
    if (button) {
      toggleMore(doc, button);
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
    syncFilters(doc, region);
    restoreFocus(doc, focusedId);
    focusedId = null;
  };

  const onHistoryRestore = () => {
    syncFilters(doc, doc.getElementById(REGION_ID));
  };

  const listeners = [
    ["htmx:configRequest", onConfigRequest],
    ["htmx:beforeSwap", onBeforeSwap],
    ["htmx:afterSettle", onAfterSettle],
    ["htmx:historyRestore", onHistoryRestore],
    ["click", onClick],
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
