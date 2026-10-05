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
//   "More filters (n)" follows `data-more` and "Filters (n)" `data-folded`.
// - "Sort by": a list too narrow for its column headers (its rows stack, by
//   CSS container queries) sorts with a select inside the region. Its
//   request is rewritten like a filter's, so it keeps every filter and
//   returns to page 1, as a click on a header does.
// - "Filters (n)": on a list too narrow for the bar on one line everything
//   but Search folds behind one toggle. The module only flips its
//   `aria-expanded`; the CSS reads that to show the panel, and on a wider
//   list shows it regardless, so a toggle left open by a narrow window
//   cannot hide anything on a wide one.
// - actions (#2561): a row's ⋯ entry loads the action's preflight into the
//   one dialog, which opens once it is filled. A refusal (409, or 403 for
//   an Organization action) or an unusable parameter (400) is swapped into
//   the still-open dialog rather
//   than treated as an error. A success answers `HX-Trigger:
//   tables-changed`: the dialog closes, a polite toast says what happened
//   and goes after a few seconds, the region re-fetches itself (declared in
//   the region, `hx-trigger="tables-changed from:body"`), and focus goes to
//   the row's ⋯ once it has settled, or to the list heading if the row is
//   gone. `tables-refused` and every failed request leave an assertive toast
//   that stays until dismissed; a 401 says the user was logged out and links
//   to the login page with `next` set to this view. A `tables-changed` that
//   carries `warning` (a delete whose database table stayed behind, #2562)
//   was done, but not cleanly: its message is an assertive warning that
//   stays, never a success that goes.
// - the access drawer (#2566): an Access cell or "Manage access" loads the
//   Table's Holders into the one drawer, which opens once it is filled.
//   Every write in it answers with the drawer again, swapped in place, so
//   it stays open; a refusal (409), a "not an Admin" (403) and an unusable
//   request (400) are swapped like a success. Focus stays in the drawer: on
//   a confirmation question when there is one, else on the control with the
//   same id, else on the drawer's title. A done change sends
//   `tables-changed` with `stay`: a toast says what happened and the region
//   re-fetches behind the drawer, but nothing closes and focus does not
//   move. Closed, focus goes back to what opened it, or to the list heading
//   when that row has left the list.
// - menu entries above the user's role carry `aria-disabled="true"` and
//   their reason as text. They stay in the keyboard order, unlike
//   Bootstrap's `.disabled`; their clicks are swallowed here.
// - the selection (#2564): an explicit list of Table names in page memory,
//   never in the URL, so a bulk action sends exactly the names its dialog
//   showed. A row's checkbox adds or removes its name, Shift+click a range
//   from the last row clicked, the page's checkbox the page (tri-state). The
//   page's checkbox is the header's, and where the rows stack and the header
//   row is hidden it is "Select this page" above the list (#2596): every
//   `data-select-page` box is one control, read and set alike. Once
//   the page is ticked, the region's banner offers "Select all N matching
//   tables", which fetches the names once. The selection survives paging,
//   sorting and actions, because the region's `data-scope` (its filters,
//   without sort and page) stays the same; a swap to another scope clears it
//   and says so in the bulk bar's slot. Names that left the dashboard
//   (`gone` in `tables-changed`) leave the selection. After every swap the
//   boxes are ticked again from the selection.
// - the bulk bar: outside the region, its slot reserved by a muted line
//   while nothing is selected, then "n selected · Clear" and the actions. An
//   action's preflight is POSTed with the selection as its `tables`
//   parameter, comma-joined, and opens the one dialog, as a row's ⋯ entry does; after the
//   action focus goes back to the bar. A bulk success lists the Tables under
//   "Show tables" in its message, which then stays until dismissed.
//
// Newer requests replace older ones through `hx-sync` on the tab, so a
// stale response never overwrites a newer state. The dialog and the drawer
// sit outside the tab, so their requests never cancel the list's. The cells' popovers are
// `list_popovers.js`, wired here so the page has one thing to bind.

import { bindPopovers } from "./list_popovers.js";

export const REGION_ID = "tables-results";
export const HEADING_ID = "tables-heading";
export const LIVE_ID = "tables-live";
export const SEARCH_ID = "tables-search";
export const FILTERS_ID = "tables-filters";
export const MORE_ID = "tables-more";
export const MORE_COUNT_ID = "tables-more-count";
export const FOLD_ID = "tables-fold";
export const FOLD_COUNT_ID = "tables-fold-count";
export const TAB_ID = "tables-tab";
export const DIALOG_ID = "table-action";
export const DIALOG_BODY_ID = "table-action-body";
export const DRAWER_ID = "table-access";
export const DRAWER_BODY_ID = "table-access-body";
export const DRAWER_TITLE_ID = "table-access-title";
export const DRAWER_CONFIRM_ID = "table-access-confirm-box";
export const TOASTS_POLITE_ID = "tables-toasts-polite";
export const TOASTS_ASSERTIVE_ID = "tables-toasts-assertive";
export const BULK_IDLE_ID = "tables-bulk-idle";
export const BULK_NOTE_ID = "tables-bulk-note";
export const BULK_BAR_ID = "tables-bulk-bar";
export const BULK_COUNT_ID = "tables-bulk-count";
export const BULK_CLEAR_ID = "tables-bulk-clear";
export const SELECT_PAGE_ID = "select-page";
export const SELECT_PAGE_STACKED_ID = "select-page-stacked";
export const SELECT_ALL_ID = "tables-select-all";
export const SELECT_MATCHING_ID = "tables-select-matching";
export const SELECT_NONE_ID = "tables-select-none";

// What the bulk bar's slot says once a filter change has cleared the
// selection.
export const SELECTION_CLEARED =
  "The filters changed, so the selection was cleared.";

// How long a success message stays, in ms. Refusals and failures stay.
export const TOAST_TIMEOUT = 5000;

// Statuses an action answers with the dialog itself: a refused request
// (409, the check run again; 403 when sharing with or removing an
// Organization was refused because the user is not a Table admin on one of
// the Tables) and an unusable parameter (400).
const DIALOG_STATUSES = [400, 403, 409];
// Statuses a write in the access drawer answers with the drawer itself:
// an unusable request (400), a viewer who is not a Table admin (403) and
// the last-admin guard (409).
const DRAWER_STATUSES = [400, 403, 409];

export const LOGGED_OUT = "You have been logged out.";
const RELOAD =
  "The change may not have been made; reload the page to see the current state.";
export const SERVER_FAILED = `Something went wrong on the server. ${RELOAD}`;
export const UNREACHABLE = `The server could not be reached. ${RELOAD}`;

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
  for (const [id, n] of [
    [MORE_COUNT_ID, region.dataset.more],
    [FOLD_COUNT_ID, region.dataset.folded],
  ]) {
    const count = doc.getElementById(id);
    if (count) {
      const applied = Number(n || 0);
      count.textContent = applied ? ` (${applied})` : "";
    }
  }
}

/**
 * Move focus after an action, whatever holds it now: to the element with
 * `id` (the row's ⋯), or to the list heading when that row is gone.
 *
 * @param {Document} doc the document.
 * @param {string|null} id the element to focus.
 */
export function focusAfterAction(doc, id) {
  const target =
    (id && doc.getElementById(id)) || doc.getElementById(HEADING_ID);
  if (target) {
    target.focus();
  }
}

/**
 * Whether a click landed on something marked unavailable
 * (`aria-disabled="true"`), and so must do nothing.
 *
 * @param {EventTarget} target the click's target.
 * @return {boolean} true when the click must be swallowed.
 */
export function isUnavailable(target) {
  return Boolean(
    target && target.closest && target.closest('[aria-disabled="true"]'),
  );
}

/**
 * Add a message to the page's toast region. A success goes to the polite
 * region and removes itself after `timeout`; an error or a warning goes to
 * the assertive one and stays until dismissed.
 *
 * @param {Document} doc the document.
 * @param {string} message the text, from the server or this module.
 * A bulk success passes the Tables it changed as `details`: "Show tables"
 * lists them, and a message the user has opened that way, or holds focus in,
 * stays until dismissed rather than vanishing while being read.
 *
 * @param {object} options `error`, `warning`, an optional `link`
 *     ({href, text}), `details` (strings listed under "Show tables"),
 *     `timeout` and `schedule` (setTimeout, a test seam).
 * @return {Element|null} the toast, or null without a toast region.
 */
export function showToast(
  doc,
  message,
  {
    error = false,
    warning = false,
    link = null,
    details = null,
    timeout = TOAST_TIMEOUT,
    schedule = setTimeout,
  } = {},
) {
  const lasting = error || warning;
  const region = doc.getElementById(
    lasting ? TOASTS_ASSERTIVE_ID : TOASTS_POLITE_ID,
  );
  if (!region) {
    return null;
  }
  const toast = doc.createElement("div");
  const kind = error
    ? "dash-toast--error"
    : warning
      ? "dash-toast--warning"
      : "dash-toast--ok";
  toast.className = `toast show dash-toast ${kind}`;
  const row = doc.createElement("div");
  row.className = "d-flex";
  const body = doc.createElement("div");
  body.className = "toast-body";
  body.textContent = message;
  if (link) {
    const anchor = doc.createElement("a");
    anchor.href = link.href;
    anchor.textContent = link.text;
    body.append(" ", anchor);
  }
  if (details && details.length) {
    const toggle = doc.createElement("button");
    toggle.type = "button";
    toggle.className = "btn btn-link btn-sm dash-toast__more";
    toggle.textContent = "Show tables";
    toggle.setAttribute("aria-expanded", "false");
    const list = doc.createElement("ul");
    list.className = "dash-toast__list";
    list.hidden = true;
    for (const detail of details) {
      const item = doc.createElement("li");
      item.textContent = detail;
      list.append(item);
    }
    toggle.addEventListener("click", () => {
      const open = list.hidden;
      list.hidden = !open;
      toggle.setAttribute("aria-expanded", String(open));
      toggle.textContent = open ? "Hide tables" : "Show tables";
      toast.dataset.kept = "true";
    });
    body.append(" ", toggle, list);
  }
  const close = doc.createElement("button");
  close.type = "button";
  close.className = "btn-close me-2 m-auto";
  close.setAttribute("aria-label", "Dismiss");
  close.addEventListener("click", () => toast.remove());
  row.append(body, close);
  toast.append(row);
  region.append(toast);
  if (!lasting && timeout) {
    schedule(() => {
      if (!toast.dataset.kept && !toast.contains(doc.activeElement)) {
        toast.remove();
      }
    }, timeout);
  }
  return toast;
}

/**
 * The login link a 401 offers: the login page, coming back to this view.
 *
 * @param {Document} doc the document.
 * @return {{href: string, text: string}} the link.
 */
export function loginLink(doc) {
  const tab = doc.getElementById(TAB_ID);
  const login = (tab && tab.dataset.loginUrl) || "/accounts/login/";
  const here = doc.location.pathname + doc.location.search;
  return {
    href: `${login}?next=${encodeURIComponent(here)}`,
    text: "Log in again",
  };
}

/**
 * The action dialog as Bootstrap's modal. Tests pass their own object with
 * the same three members.
 *
 * @param {Document} doc the document.
 * @return {{open: function(), close: function(), onHidden: function(function())}}
 */
export function bootstrapDialog(doc) {
  const element = () => doc.getElementById(DIALOG_ID);
  const modal = () => {
    const bootstrap = doc.defaultView && doc.defaultView.bootstrap;
    return element() && bootstrap
      ? bootstrap.Modal.getOrCreateInstance(element())
      : null;
  };
  return {
    open: () => modal() && modal().show(),
    close: () => modal() && modal().hide(),
    onHidden: (callback) =>
      element() && element().addEventListener("hidden.bs.modal", callback),
  };
}

/**
 * The access drawer as Bootstrap's offcanvas, with the members of
 * `bootstrapDialog`.
 *
 * @param {Document} doc the document.
 * @return {{open: function(), close: function(), onHidden: function(function())}}
 */
export function bootstrapDrawer(doc) {
  const element = () => doc.getElementById(DRAWER_ID);
  const offcanvas = () => {
    const bootstrap = doc.defaultView && doc.defaultView.bootstrap;
    return element() && bootstrap
      ? bootstrap.Offcanvas.getOrCreateInstance(element())
      : null;
  };
  return {
    open: () => offcanvas() && offcanvas().show(),
    close: () => offcanvas() && offcanvas().hide(),
    onHidden: (callback) =>
      element() && element().addEventListener("hidden.bs.offcanvas", callback),
  };
}

/**
 * Put focus back inside the drawer after its contents were replaced, if it
 * was inside before: on the confirmation question when the server asks
 * one, else on the control with the same id, else on the drawer's title.
 *
 * @param {Document} doc the document.
 * @param {string|null} id the id focused in the drawer before the swap.
 */
export function restoreDrawerFocus(doc, id) {
  if (!id) {
    return;
  }
  const target =
    doc.getElementById(DRAWER_CONFIRM_ID) ||
    doc.getElementById(id) ||
    doc.getElementById(DRAWER_TITLE_ID);
  if (target) {
    target.focus();
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
 * Open or close "Filters (n)". Only `aria-expanded` changes: the CSS shows
 * the panel from it on a narrow list and always on a wide one.
 *
 * @param {Element} button the "Filters (n)" button.
 */
export function toggleFold(button) {
  const open = button.getAttribute("aria-expanded") !== "true";
  button.setAttribute("aria-expanded", String(open));
}

/**
 * The region's row checkboxes, in the order the page lists them.
 *
 * @param {Element|null} region the results region.
 * @return {HTMLInputElement[]} one box per row; its value is the name.
 */
export function rowBoxes(region) {
  return region ? [...region.querySelectorAll("input[data-select-row]")] : [];
}

/**
 * The page's checkboxes: the header's and "Select this page", which takes
 * its place where the rows stack. The CSS shows one of them at a time.
 *
 * @param {Document} doc the document.
 * @return {HTMLInputElement[]} every `data-select-page` box.
 */
export function pageBoxes(doc) {
  return [...doc.querySelectorAll("input[data-select-page]")];
}

/**
 * The page's checkbox the user can see, where focus goes after the selection
 * is cleared: the first one shown, else the header's.
 *
 * @param {Document} doc the document.
 * @return {HTMLInputElement|null} the box, or null on a page without one.
 */
export function visiblePageBox(doc) {
  const boxes = pageBoxes(doc);
  const shown = boxes.find(
    (box) => !box.checkVisibility || box.checkVisibility(),
  );
  return shown || doc.getElementById(SELECT_PAGE_ID) || boxes[0] || null;
}

/**
 * The names from one row to another, both included, in page order: what a
 * Shift+click ticks or unticks. Just `to` when `from` is not on this page.
 *
 * @param {HTMLInputElement[]} boxes the page's row boxes.
 * @param {string|null} from the name clicked before.
 * @param {string} to the name clicked now.
 * @return {string[]} the names of the range.
 */
export function rangeOf(boxes, from, to) {
  const names = boxes.map((box) => box.value);
  const start = names.indexOf(from);
  const end = names.indexOf(to);
  if (start < 0 || end < 0) {
    return [to];
  }
  return names.slice(Math.min(start, end), Math.max(start, end) + 1);
}

/**
 * Show the selection: tick the page's boxes from it, set the page's boxes
 * (checked, indeterminate or neither), offer the banner's "Select all N
 * matching tables" once the page is ticked or say that all of them are, and
 * turn the bulk bar's slot into the bar while anything is selected.
 *
 * @param {Document} doc the document.
 * @param {Set<string>} selection the selected names.
 * @param {object} options `matching`, the names "Select all" fetched under
 *     this scope (or null), and `note`, what the empty slot says instead of
 *     its muted line.
 */
export function renderSelection(
  doc,
  selection,
  { matching = null, note = "" } = {},
) {
  const boxes = rowBoxes(doc.getElementById(REGION_ID));
  for (const box of boxes) {
    box.checked = selection.has(box.value);
  }
  const ticked = boxes.filter((box) => box.checked).length;
  const pageFull = boxes.length > 0 && ticked === boxes.length;
  for (const header of pageBoxes(doc)) {
    header.checked = pageFull;
    header.indeterminate = ticked > 0 && !pageFull;
  }

  const banner = doc.getElementById(SELECT_ALL_ID);
  if (banner) {
    const total = Number(banner.dataset.total || 0);
    const allMatching =
      matching !== null &&
      matching.length === total &&
      matching.every((name) => selection.has(name));
    let mode = "";
    if (pageFull && total > boxes.length) {
      mode = allMatching ? "all" : "page";
    }
    banner.hidden = !mode;
    for (const part of banner.querySelectorAll("[data-when]")) {
      part.hidden = part.dataset.when !== mode;
    }
  }

  const count = selection.size;
  const bar = doc.getElementById(BULK_BAR_ID);
  const idle = doc.getElementById(BULK_IDLE_ID);
  const said = doc.getElementById(BULK_NOTE_ID);
  if (bar) {
    bar.hidden = count === 0;
  }
  const counter = doc.getElementById(BULK_COUNT_ID);
  if (counter) {
    counter.textContent = `${count.toLocaleString("en")} selected`;
  }
  const showNote = count === 0 && Boolean(note);
  if (said) {
    // always present and only its text changes: a live region that is
    // shown when it gets its text is not announced reliably
    said.textContent = showNote ? note : "";
  }
  if (idle) {
    idle.hidden = count > 0 || showNote;
  }
}

/**
 * The names of every Table the list's filters select, from the banner's
 * `data-names-url` (login:table-names). Rejects with the HTTP status on a
 * refusal, so a 401 can say the user was logged out.
 *
 * @param {string} url the names endpoint with the scope's query.
 * @return {Promise<string[]>} the names.
 */
export async function fetchMatchingNames(url) {
  const response = await fetch(url, {
    credentials: "same-origin",
    headers: { Accept: "application/json", "HX-Request": "true" },
  });
  if (!response.ok) {
    const error = new Error(`names: ${response.status}`);
    error.status = response.status;
    throw error;
  }
  return (await response.json()).names;
}

/**
 * Wire the tab to htmx's events on `doc`.
 *
 * @param {Document} doc the document.
 * @param {object} options test seams: `announceDelay`, `dialog` (see
 *     `bootstrapDialog`), `drawer` (see `bootstrapDrawer`), `schedule`
 *     (setTimeout, for the toasts) and `fetchNames` (see
 *     `fetchMatchingNames`).
 * @return {function(): void} removes the listeners again.
 */
export function bindTablesTab(
  doc,
  {
    announceDelay = 60,
    dialog = bootstrapDialog(doc),
    drawer = bootstrapDrawer(doc),
    schedule = setTimeout,
    fetchNames = fetchMatchingNames,
  } = {},
) {
  let focusedId = null;
  // the selection: names in page memory, the scope they were chosen under,
  // the last row clicked (a Shift+click's other end), what "Select all
  // matching" fetched, and what the bulk bar's empty slot says
  const selection = new Set();
  const scopeOf = (region) => (region ? region.dataset.scope || "" : "");
  let scope = scopeOf(doc.getElementById(REGION_ID));
  let anchor = null;
  let matching = null;
  let note = "";
  const render = () => renderSelection(doc, selection, { matching, note });
  const select = (names, on) => {
    note = "";
    for (const name of names) {
      if (on) {
        selection.add(name);
      } else {
        selection.delete(name);
      }
    }
    render();
  };
  const clearSelection = () => {
    note = "";
    selection.clear();
    render();
  };
  // A region of another scope (a filter, the search or the status changed)
  // clears the selection, and the slot says so; paging and sorting keep it.
  const followScope = (region) => {
    const now = scopeOf(region);
    if (now !== scope) {
      scope = now;
      matching = null;
      anchor = null;
      if (selection.size) {
        selection.clear();
        note = SELECTION_CLEARED;
      }
    }
    render();
  };
  // after a clear: the page's box the user can see, whichever layout
  const focusPageBox = () => {
    const shown = visiblePageBox(doc);
    focusAfterAction(doc, shown ? shown.id : SELECT_PAGE_ID);
  };
  const forget = (names) => {
    for (const name of names || []) {
      selection.delete(name);
    }
    if (matching !== null && names && names.length) {
      matching = matching.filter((name) => !names.includes(name));
    }
    render();
  };
  // what opened the drawer, and the control focused in it before a swap
  let drawerOrigin = null;
  let drawerFocusedId = null;
  // the row whose ⋯ opened the dialog, and where focus goes after an action
  let origin = null;
  let afterAction = null;
  const isRegion = (event) =>
    event.detail && event.detail.target && event.detail.target.id === REGION_ID;
  const isDialog = (event) =>
    event.detail &&
    event.detail.target &&
    event.detail.target.id === DIALOG_BODY_ID;
  const isDrawer = (event) =>
    event.detail &&
    event.detail.target &&
    event.detail.target.id === DRAWER_BODY_ID;
  const status = (event) => event.detail.xhr && event.detail.xhr.status;

  const onConfigRequest = (event) => {
    const elt = event.detail.elt;
    const bar = doc.getElementById(FILTERS_ID);
    if (elt && elt.hasAttribute && elt.hasAttribute("data-bulk-action")) {
      // a bulk action's preflight: exactly the selected names, in one
      // comma-joined field (Django refuses more than 1,000 parameters)
      event.detail.parameters.tables = [...selection].join(",");
      return;
    }
    if (!elt || !elt.name) {
      return;
    }
    const isSort = elt.hasAttribute("data-list-sort");
    if (!isSort && !(bar && bar.contains(elt))) {
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

  const selectMatching = async (banner) => {
    const asked = scope;
    let names;
    try {
      names = await fetchNames(banner.dataset.namesUrl);
    } catch (error) {
      if (error && error.status === 401) {
        showToast(doc, LOGGED_OUT, { error: true, link: loginLink(doc) });
      } else if (error && error.status) {
        showToast(doc, SERVER_FAILED, { error: true });
      } else {
        showToast(doc, UNREACHABLE, { error: true });
      }
      return;
    }
    if (asked !== scope) {
      // the filters changed while the names were on their way
      return;
    }
    matching = names;
    select(names, true);
    const next = doc.getElementById(SELECT_NONE_ID);
    if (next) {
      next.focus();
    }
  };

  const onSelect = (event) => {
    const target = event.target;
    const row = target.closest("input[data-select-row]");
    if (row) {
      const region = doc.getElementById(REGION_ID);
      const names =
        event.shiftKey && anchor
          ? rangeOf(rowBoxes(region), anchor, row.value)
          : [row.value];
      select(names, row.checked);
      anchor = row.value;
      return true;
    }
    if (target.closest("input[data-select-page]")) {
      const boxes = rowBoxes(doc.getElementById(REGION_ID));
      select(
        boxes.map((box) => box.value),
        target.checked,
      );
      return true;
    }
    const banner = target.closest(`#${SELECT_ALL_ID}`);
    if (target.closest(`#${SELECT_MATCHING_ID}`) && banner) {
      selectMatching(banner);
      return true;
    }
    if (target.closest(`#${SELECT_NONE_ID}`)) {
      clearSelection();
      focusPageBox();
      return true;
    }
    if (target.closest(`#${BULK_CLEAR_ID}`)) {
      clearSelection();
      focusPageBox();
      return true;
    }
    return false;
  };

  const onClick = (event) => {
    if (!event.target.closest) {
      return;
    }
    if (onSelect(event)) {
      return;
    }
    const more = event.target.closest(`#${MORE_ID}`);
    if (more) {
      toggleMore(doc, more);
    }
    const fold = event.target.closest(`#${FOLD_ID}`);
    if (fold) {
      toggleFold(fold);
    }
  };

  const onGuard = (event) => {
    if (isUnavailable(event.target)) {
      event.preventDefault();
      event.stopPropagation();
    }
  };

  const onBeforeSwap = (event) => {
    if (isRegion(event)) {
      focusedId = focusedIdWithin(doc, event.detail.target);
    } else if (isDialog(event) && DIALOG_STATUSES.includes(status(event))) {
      event.detail.shouldSwap = true;
      event.detail.isError = false;
    } else if (isDrawer(event)) {
      drawerFocusedId = focusedIdWithin(doc, event.detail.target);
      if (DRAWER_STATUSES.includes(status(event))) {
        event.detail.shouldSwap = true;
        event.detail.isError = false;
      }
    }
  };

  const onAfterSwap = (event) => {
    if (!isDialog(event) && !isDrawer(event)) {
      return;
    }
    // htmx sets `detail.elt` to the swap target; what sent the request is
    // `requestConfig.elt`
    const config = event.detail.requestConfig;
    const elt = config && config.elt;
    const data = (elt && elt.dataset) || {};
    if (isDialog(event) && data.actionOrigin) {
      origin = data.actionOrigin;
      dialog.open();
    } else if (isDrawer(event) && data.accessOrigin) {
      drawerOrigin = data.accessOrigin;
      drawer.open();
    }
  };

  const onAfterSettle = (event) => {
    if (isDrawer(event)) {
      restoreDrawerFocus(doc, drawerFocusedId);
      drawerFocusedId = null;
      return;
    }
    if (!isRegion(event)) {
      return;
    }
    const region = doc.getElementById(REGION_ID);
    const live = doc.getElementById(LIVE_ID);
    if (region && live) {
      announce(live, region.dataset.announce || "", announceDelay);
    }
    syncFilters(doc, region);
    followScope(region);
    if (afterAction !== null) {
      focusAfterAction(doc, afterAction);
      afterAction = null;
    } else {
      restoreFocus(doc, focusedId);
    }
    focusedId = null;
  };

  const onChanged = (event) => {
    const detail = event.detail || {};
    // Tables that left the dashboard leave the selection
    forget(detail.gone);
    if (detail.stay) {
      // a change in the drawer: it stays open and keeps focus
      if (detail.message) {
        showToast(doc, detail.message, { schedule });
      }
      return;
    }
    afterAction = detail.focus || origin || "";
    origin = null;
    dialog.close();
    if (detail.message) {
      showToast(doc, detail.message, {
        warning: Boolean(detail.warning),
        details: detail.tables || null,
        schedule,
      });
    }
  };

  const onRefused = (event) => {
    const detail = event.detail || {};
    if (detail.message) {
      showToast(doc, detail.message, { error: true });
    }
  };

  const onResponseError = (event) => {
    const status = event.detail && event.detail.xhr && event.detail.xhr.status;
    if (status === 401) {
      showToast(doc, LOGGED_OUT, { error: true, link: loginLink(doc) });
    } else {
      showToast(doc, SERVER_FAILED, { error: true });
    }
  };

  const onSendError = () => {
    showToast(doc, UNREACHABLE, { error: true });
  };

  // Cancelled: focus goes back to the ⋯ that opened the dialog. After an
  // action the region's settle does that instead.
  dialog.onHidden(() => {
    if (afterAction === null && origin) {
      const target = doc.getElementById(origin);
      if (target) {
        target.focus();
      }
    }
    origin = null;
  });

  // Closed: focus goes back to what opened the drawer, or to the list
  // heading when that row has left the list.
  drawer.onHidden(() => {
    if (drawerOrigin !== null) {
      focusAfterAction(doc, drawerOrigin);
    }
    drawerOrigin = null;
  });

  const onHistoryRestore = () => {
    const region = doc.getElementById(REGION_ID);
    syncFilters(doc, region);
    followScope(region);
  };

  const listeners = [
    ["htmx:configRequest", onConfigRequest],
    ["htmx:beforeSwap", onBeforeSwap],
    ["htmx:afterSwap", onAfterSwap],
    ["htmx:afterSettle", onAfterSettle],
    ["htmx:historyRestore", onHistoryRestore],
    ["htmx:responseError", onResponseError],
    ["htmx:sendError", onSendError],
    ["tables-changed", onChanged],
    ["tables-refused", onRefused],
    ["click", onClick],
  ];
  for (const [name, listener] of listeners) {
    doc.body.addEventListener(name, listener);
  }
  // in the capture phase, so the swallowed click reaches neither htmx nor
  // Bootstrap's dropdown, which would close the menu and hide the reason
  doc.body.addEventListener("click", onGuard, true);
  const popovers = bindPopovers(doc);
  render();
  return () => {
    for (const [name, listener] of listeners) {
      doc.body.removeEventListener(name, listener);
    }
    doc.body.removeEventListener("click", onGuard, true);
    popovers.unbind();
  };
}
