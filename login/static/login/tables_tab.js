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
//   one dialog, which opens once it is filled. A refusal (409) or an
//   unusable parameter (400) is swapped into the still-open dialog rather
//   than treated as an error. A success answers `HX-Trigger:
//   tables-changed`: the dialog closes, a polite toast says what happened
//   and goes after a few seconds, the region re-fetches itself (declared in
//   the region, `hx-trigger="tables-changed from:body"`), and focus goes to
//   the row's ⋯ once it has settled, or to the list heading if the row is
//   gone. `tables-refused` and every failed request leave an assertive toast
//   that stays until dismissed; a 401 says the user was logged out and links
//   to the login page with `next` set to this view.
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

// How long a success message stays, in ms. Refusals and failures stay.
export const TOAST_TIMEOUT = 5000;

// Statuses an action answers with the dialog itself: a refused request
// (409, the check run again) and an unusable parameter (400).
const DIALOG_STATUSES = [400, 409];
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
 * region and removes itself after `timeout`; an error goes to the assertive
 * one and stays until dismissed.
 *
 * @param {Document} doc the document.
 * @param {string} message the text, from the server or this module.
 * @param {object} options `error`, an optional `link` ({href, text}),
 *     `timeout` and `schedule` (setTimeout, a test seam).
 * @return {Element|null} the toast, or null without a toast region.
 */
export function showToast(
  doc,
  message,
  {
    error = false,
    link = null,
    timeout = TOAST_TIMEOUT,
    schedule = setTimeout,
  } = {},
) {
  const region = doc.getElementById(
    error ? TOASTS_ASSERTIVE_ID : TOASTS_POLITE_ID,
  );
  if (!region) {
    return null;
  }
  const toast = doc.createElement("div");
  const kind = error ? "dash-toast--error" : "dash-toast--ok";
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
  const close = doc.createElement("button");
  close.type = "button";
  close.className = "btn-close me-2 m-auto";
  close.setAttribute("aria-label", "Dismiss");
  close.addEventListener("click", () => toast.remove());
  row.append(body, close);
  toast.append(row);
  region.append(toast);
  if (!error && timeout) {
    schedule(() => toast.remove(), timeout);
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
 * Wire the tab to htmx's events on `doc`.
 *
 * @param {Document} doc the document.
 * @param {object} options test seams: `announceDelay`, `dialog` (see
 *     `bootstrapDialog`), `drawer` (see `bootstrapDrawer`) and `schedule`
 *     (setTimeout, for the toasts).
 * @return {function(): void} removes the listeners again.
 */
export function bindTablesTab(
  doc,
  {
    announceDelay = 60,
    dialog = bootstrapDialog(doc),
    drawer = bootstrapDrawer(doc),
    schedule = setTimeout,
  } = {},
) {
  let focusedId = null;
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

  const onClick = (event) => {
    if (!event.target.closest) {
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
      showToast(doc, detail.message, { schedule });
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
    syncFilters(doc, doc.getElementById(REGION_ID));
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
  return () => {
    for (const [name, listener] of listeners) {
      doc.body.removeEventListener(name, listener);
    }
    doc.body.removeEventListener("click", onGuard, true);
    popovers.unbind();
  };
}
