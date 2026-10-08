// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// A profile dashboard list, in the browser: what the tables tab (spec #2551)
// does in the page, made generic for the datasets tab (spec #2613). Nothing
// here knows about Tables. Every id, the two event names, the parameter a
// bulk action sends the selection in and the drawer come from a config,
// `listConfig`; `tables_tab.js` is the tables tab's binding of it.
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
//   A multi-valued filter in the primary row is a dropdown of checkboxes,
//   whose button counts what is ticked; it follows every change.
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
//   an action the user's role does not allow) or an unusable parameter (400)
//   is swapped into the still-open dialog rather than treated as an error. A
//   success answers with the list's changed event (`tables-changed` on the
//   tables tab): the dialog closes, a polite toast says what happened and
//   goes after a few seconds, the region re-fetches itself (declared in the
//   region, `hx-trigger="tables-changed from:body"`), and focus goes to the
//   row's ⋯ once it has settled, or to the list heading if the row is gone.
//   The refused event and every failed request leave an assertive toast
//   that stays until dismissed; a 401 says the user was logged out and links
//   to the login page with `next` set to this view. A changed event that
//   carries `warning` (a delete whose database table stayed behind, #2562)
//   was done, but not cleanly: its message is an assertive warning that
//   stays, never a success that goes.
// - close before open (#2623): a modal cannot open a drawer or another
//   modal while it is showing, so a link in the dialog that opens something
//   else carries `data-close-then` and `hx-trigger="dialog-closed"`
//   (`DIALOG_CLOSED`). Its click closes the dialog and nothing else; once
//   the dialog has closed (Bootstrap's `hidden.bs.modal`), the link is sent
//   `dialog-closed`, and htmx sends its request then. Focus is left to what
//   that request opens, which says where it came from as any opener does
//   (`data-action-origin`, the drawer's origin attribute).
// - the drawer, when the list has one (the tables tab's access drawer,
//   #2566): a cell or a menu entry loads it, and it opens once it is filled.
//   Every write in it answers with the drawer again, swapped in place, so
//   it stays open; a refusal (409), a forbidden write (403) and an unusable
//   request (400) are swapped like a success. Focus stays in the drawer: on
//   a confirmation question when there is one, else on the control with the
//   same id, else on the drawer's title. A done change sends the changed
//   event with `stay`: a toast says what happened and the region re-fetches
//   behind the drawer, but nothing closes and focus does not move. Closed,
//   focus goes back to what opened it, or to the list heading when that row
//   has left the list. The server may name the control to focus instead of
//   the one that went (`data-drawer-focus`, the next Remove after a member
//   was removed) and what to say (`data-announce`, through the drawer's live
//   region outside its swapped contents).
// - the drawer in the address (#2625), when the config names a parameter
//   (`?members=<name>` on the datasets tab): page state, not list state. It
//   is written with `replaceState` when the drawer opens, on the key its
//   contents carry (`data-drawer-key`), and removed when it closes, so it adds
//   no history entry; htmx replacing or pushing the list's own address while
//   the drawer is open puts it back, and no filter or sort request carries
//   it. On a load or a history restore the drawer reopens when the page says
//   the parameter names something of the user's (`data-open` on the drawer,
//   which the server sets only then) and the address still holds it. A
//   changed event carrying `created` (a Create) opens the drawer on the new
//   item once the dialog has closed, with focus where the config says.
// - menu entries the user may not use carry `aria-disabled="true"` and
//   their reason as text. They stay in the keyboard order, unlike
//   Bootstrap's `.disabled`; their clicks are swallowed here.
// - the selection (#2564): an explicit list of names in page memory, never
//   in the URL, so a bulk action sends exactly the names its dialog showed.
//   A row's checkbox adds or removes its name, Shift+click a range from the
//   last row clicked, the page's checkbox the page (tri-state). The page's
//   checkbox is the header's, and where the rows stack and the header row is
//   hidden it is "Select this page" above the list (#2596): every
//   `data-select-page` box is one control, read and set alike. Once the page
//   is ticked, the region's banner offers "Select all N matching", which
//   fetches the names once. The selection survives paging, sorting and
//   actions, because the region's `data-scope` (its filters, without sort
//   and page) stays the same; a swap to another scope clears it and says so
//   in the bulk bar's slot. Names that left the dashboard (`gone` in the
//   changed event) leave the selection. After every swap the boxes are
//   ticked again from the selection.
// - the bulk bar: outside the region, its slot reserved by a muted line
//   while nothing is selected, then "n selected · Clear" and the actions. An
//   action's preflight is POSTed with the selection as one parameter
//   (`tables` on the tables tab), comma-joined, and opens the one dialog, as
//   a row's ⋯ entry does; after the action focus goes back to the bar. A
//   bulk success lists what it changed under "Show tables" (the list's own
//   noun) in its message, which then stays until dismissed.
//
// Newer requests replace older ones through `hx-sync` on the tab, so a
// stale response never overwrites a newer state. The dialog and the drawer
// sit outside the tab, so their requests never cancel the list's. The cells' popovers are
// `list_popovers.js`, wired here so the page has one thing to bind.

import { bindPopovers } from "./list_popovers.js";

/**
 * A list's ids and names, from its nouns: the list's own ids, events and
 * selection parameter take the plural (`tables-results`, `tables-changed`,
 * `tables`), what acts on one item the singular (`table-action`). The page's
 * checkboxes are `select-page` and `select-page-stacked` on every list: a
 * page holds one list.
 *
 * @param {object} nouns `plural` and `singular` (lower case, as the ids
 *     spell them), and `drawer`, the drawer's name (`access` gives
 *     `table-access`, opened by an element with `data-access-origin`), or
 *     null for a list without one. `drawerParam` puts the open drawer in the
 *     address under that parameter (page state, `?members=<name>`), and
 *     `createdFocus` is the id to focus in a drawer opened on a newly created
 *     item.
 * @return {object} the config `bindList` and the helpers here take.
 */
export function listConfig({
  plural,
  singular,
  drawer = null,
  drawerParam = null,
  createdFocus = null,
}) {
  const own = (name) => `${plural}-${name}`;
  const ids = {
    region: own("results"),
    heading: own("heading"),
    live: own("live"),
    search: own("search"),
    filters: own("filters"),
    more: own("more"),
    moreCount: own("more-count"),
    fold: own("fold"),
    foldCount: own("fold-count"),
    tab: own("tab"),
    dialog: `${singular}-action`,
    dialogBody: `${singular}-action-body`,
    toastsPolite: own("toasts-polite"),
    toastsAssertive: own("toasts-assertive"),
    bulkIdle: own("bulk-idle"),
    bulkNote: own("bulk-note"),
    bulkBar: own("bulk-bar"),
    bulkCount: own("bulk-count"),
    bulkClear: own("bulk-clear"),
    selectPage: "select-page",
    selectPageStacked: "select-page-stacked",
    selectAll: own("select-all"),
    selectMatching: own("select-matching"),
    selectNone: own("select-none"),
  };
  const drawerId = drawer && `${singular}-${drawer}`;
  return Object.freeze({
    ids: Object.freeze(ids),
    drawer: drawer
      ? Object.freeze({
          id: drawerId,
          body: `${drawerId}-body`,
          title: `${drawerId}-title`,
          confirm: `${drawerId}-confirm-box`,
          live: `${drawerId}-live`,
          // the opener's `data-<drawer>-origin`, as `dataset` spells it
          origin: `${drawer.replace(/-(\w)/g, (_, c) => c.toUpperCase())}Origin`,
          param: drawerParam,
          createdFocus,
        })
      : null,
    changedEvent: own("changed"),
    refusedEvent: own("refused"),
    selectionParam: plural,
    // the key a changed event lists a batch's changed items under
    itemsKey: plural,
    // what "Show tables" says it shows
    noun: plural,
  });
}

// What the bulk bar's slot says once a filter change has cleared the
// selection.
export const SELECTION_CLEARED =
  "The filters changed, so the selection was cleared.";

// How long a success message stays, in ms. Refusals and failures stay.
export const TOAST_TIMEOUT = 5000;

// Statuses an action answers with the dialog itself: a refused request
// (409, the check run again; 403 when the user's role does not allow it,
// e.g. sharing Tables with an Organization without being a Table admin on
// one of them) and an unusable parameter (400).
const DIALOG_STATUSES = [400, 403, 409];
// Statuses a write in the drawer answers with the drawer itself: an
// unusable request (400), a viewer who may not make it (403; on the tables
// tab, not a Table admin) and a guard (409; the last-admin guard).
const DRAWER_STATUSES = [400, 403, 409];

// What a link marked `data-close-then` is sent once the dialog it sits in
// has closed: the event its `hx-trigger` names.
export const DIALOG_CLOSED = "dialog-closed";

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
 * @param {object} config the list's, from `listConfig`.
 * @param {string|null} id the id focused before the swap.
 */
export function restoreFocus(doc, config, id) {
  if (!id) {
    return;
  }
  const active = doc.activeElement;
  if (active && active !== doc.body && active.isConnected) {
    return;
  }
  const target =
    doc.getElementById(id) || doc.getElementById(config.ids.heading);
  if (target) {
    target.focus();
  }
}

/**
 * What a dropdown of a multi-valued filter says on its button: the blank
 * text, or how many are ticked, "Topic (2)", the way "More filters (n)"
 * counts. The server says the same on render (`FilterControl.summary`).
 *
 * @param {string} label the filter's label, "Topic".
 * @param {string} blank what it says with nothing ticked, "Topic: any".
 * @param {number} ticked how many options are ticked.
 * @return {string} the button's text.
 */
export function multiSummary(label, blank, ticked) {
  return ticked ? `${label} (${ticked})` : blank;
}

/**
 * Bring every dropdown button of a multi-valued filter in the bar
 * (`data-multi-summary`, naming the filter's parameter) in step with its
 * checkboxes.
 *
 * @param {Element} bar the filter bar.
 */
export function summarizeMulti(bar) {
  for (const button of bar.querySelectorAll("[data-multi-summary]")) {
    const name = button.dataset.multiSummary;
    const ticked = [
      ...bar.querySelectorAll(`input[type="checkbox"][name="${name}"]`),
    ].filter((box) => box.checked).length;
    button.textContent = multiSummary(
      button.dataset.label || name,
      button.dataset.blank || "",
      ticked
    );
  }
}

/**
 * Make every bar control hold what the region says the URL holds, except the
 * one the user is in. A select whose value is not among its options (a value
 * that no longer applies) shows its blank option.
 *
 * @param {Document} doc the document.
 * @param {object} config the list's, from `listConfig`.
 * @param {Element} region the current region.
 */
export function syncFilters(doc, config, region) {
  const bar = doc.getElementById(config.ids.filters);
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
    [config.ids.moreCount, region.dataset.more],
    [config.ids.foldCount, region.dataset.folded],
  ]) {
    const count = doc.getElementById(id);
    if (count) {
      const applied = Number(n || 0);
      count.textContent = applied ? ` (${applied})` : "";
    }
  }
  summarizeMulti(bar);
}

/**
 * Move focus after an action, whatever holds it now: to the element with
 * `id` (the row's ⋯), or to the list heading when that row is gone.
 *
 * @param {Document} doc the document.
 * @param {object} config the list's, from `listConfig`.
 * @param {string|null} id the element to focus.
 */
export function focusAfterAction(doc, config, id) {
  const target =
    (id && doc.getElementById(id)) || doc.getElementById(config.ids.heading);
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
    target && target.closest && target.closest('[aria-disabled="true"]')
  );
}

/**
 * Add a message to the page's toast region. A success goes to the polite
 * region and removes itself after `timeout`; an error or a warning goes to
 * the assertive one and stays until dismissed.
 *
 * A bulk success passes what it changed as `details`: "Show tables" (the
 * list's noun) lists them, and a message the user has opened that way, or
 * holds focus in, stays until dismissed rather than vanishing while being
 * read.
 *
 * @param {Document} doc the document.
 * @param {object} config the list's, from `listConfig`.
 * @param {string} message the text, from the server or this module.
 * @param {object} options `error`, `warning`, an optional `link`
 *     ({href, text}), `details` (strings listed under "Show tables"),
 *     `timeout` and `schedule` (setTimeout, a test seam).
 * @return {Element|null} the toast, or null without a toast region.
 */
export function showToast(
  doc,
  config,
  message,
  {
    error = false,
    warning = false,
    link = null,
    details = null,
    timeout = TOAST_TIMEOUT,
    schedule = setTimeout,
  } = {}
) {
  const lasting = error || warning;
  const region = doc.getElementById(
    lasting ? config.ids.toastsAssertive : config.ids.toastsPolite
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
    toggle.textContent = `Show ${config.noun}`;
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
      toggle.textContent = `${open ? "Hide" : "Show"} ${config.noun}`;
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
 * @param {object} config the list's, from `listConfig`.
 * @return {{href: string, text: string}} the link.
 */
export function loginLink(doc, config) {
  const tab = doc.getElementById(config.ids.tab);
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
 * @param {object} config the list's, from `listConfig`.
 * @return {{open: function(), close: function(), onHidden: function(function())}}
 */
export function bootstrapDialog(doc, config) {
  const element = () => doc.getElementById(config.ids.dialog);
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
 * The list's drawer as Bootstrap's offcanvas, with the members of
 * `bootstrapDialog` and `onShown`. On a list without a drawer it does
 * nothing.
 *
 * @param {Document} doc the document.
 * @param {object} config the list's, from `listConfig`.
 * @return {{open: function(), close: function(), onHidden: function(function())}}
 */
export function bootstrapDrawer(doc, config) {
  const element = () => config.drawer && doc.getElementById(config.drawer.id);
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
    // once shown: Bootstrap focuses the drawer itself then, so a control is
    // focused only after that
    onShown: (callback) =>
      element() && element().addEventListener("shown.bs.offcanvas", callback),
  };
}

/**
 * Put focus back inside the drawer after its contents were replaced, if it
 * was inside before: on the confirmation question when the server asks
 * one, else on the control the server named instead of the one that went
 * (`data-drawer-focus`), else on the control with the same id, else on the
 * drawer's title.
 *
 * @param {Document} doc the document.
 * @param {object} config the list's, from `listConfig`.
 * @param {string|null} id the id focused in the drawer before the swap.
 */
export function restoreDrawerFocus(doc, config, id) {
  if (!id || !config.drawer) {
    return;
  }
  const named = drawerMark(doc, config, "drawerFocus");
  const target =
    doc.getElementById(config.drawer.confirm) ||
    (named && doc.getElementById(named)) ||
    doc.getElementById(id) ||
    doc.getElementById(config.drawer.title);
  if (target) {
    target.focus();
  }
}

/**
 * What the drawer's current contents say about themselves, read off the
 * element carrying the `data-` attribute `key` names (`drawerKey`,
 * `drawerFocus`, `announce`).
 *
 * @param {Document} doc the document.
 * @param {object} config the list's, from `listConfig`.
 * @param {string} key the attribute, as `dataset` spells it.
 * @return {string|null} its value, or null when nothing carries it.
 */
export function drawerMark(doc, config, key) {
  const body = config.drawer && doc.getElementById(config.drawer.body);
  if (!body) {
    return null;
  }
  const attribute = key.replace(/[A-Z]/g, (c) => `-${c.toLowerCase()}`);
  const element = body.querySelector(`[data-${attribute}]`);
  return element ? element.dataset[key] : null;
}

/**
 * The current address with the drawer's parameter set to `key`, or removed
 * for null: what the address bar holds while the drawer is open or after
 * it closed. Everything else in it is kept.
 *
 * @param {string} href the current address.
 * @param {string} param the drawer's parameter.
 * @param {string|null} key what the open drawer shows.
 * @return {string} the path, query and hash to write.
 */
export function withDrawerParam(href, param, key) {
  const url = new URL(href);
  if (key) {
    url.searchParams.set(param, key);
  } else {
    url.searchParams.delete(param);
  }
  return url.pathname + url.search + url.hash;
}

/**
 * Fill the drawer from `url` through htmx, which then swaps it like an
 * opener's request. Tests pass their own function.
 *
 * @param {Document} doc the document.
 * @param {object} config the list's, from `listConfig`.
 * @return {function(string)} loads the drawer's contents from a URL.
 */
export function htmxDrawerLoader(doc, config) {
  return (url) => {
    const htmx = doc.defaultView && doc.defaultView.htmx;
    if (htmx && config.drawer) {
      htmx.ajax("GET", url, {
        target: `#${config.drawer.body}`,
        swap: "innerHTML",
      });
    }
  };
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
 * @param {object} config the list's, from `listConfig`.
 * @return {HTMLInputElement|null} the box, or null on a page without one.
 */
export function visiblePageBox(doc, config) {
  const boxes = pageBoxes(doc);
  const shown = boxes.find(
    (box) => !box.checkVisibility || box.checkVisibility()
  );
  return shown || doc.getElementById(config.ids.selectPage) || boxes[0] || null;
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
 * matching" once the page is ticked or say that all of them are, and turn
 * the bulk bar's slot into the bar while anything is selected.
 *
 * @param {Document} doc the document.
 * @param {object} config the list's, from `listConfig`.
 * @param {Set<string>} selection the selected names.
 * @param {object} options `matching`, the names "Select all" fetched under
 *     this scope (or null), and `note`, what the empty slot says instead of
 *     its muted line.
 */
export function renderSelection(
  doc,
  config,
  selection,
  { matching = null, note = "" } = {}
) {
  const { ids } = config;
  const boxes = rowBoxes(doc.getElementById(ids.region));
  for (const box of boxes) {
    box.checked = selection.has(box.value);
  }
  const ticked = boxes.filter((box) => box.checked).length;
  const pageFull = boxes.length > 0 && ticked === boxes.length;
  for (const header of pageBoxes(doc)) {
    header.checked = pageFull;
    header.indeterminate = ticked > 0 && !pageFull;
  }

  const banner = doc.getElementById(ids.selectAll);
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
  const bar = doc.getElementById(ids.bulkBar);
  const idle = doc.getElementById(ids.bulkIdle);
  const said = doc.getElementById(ids.bulkNote);
  if (bar) {
    bar.hidden = count === 0;
  }
  const counter = doc.getElementById(ids.bulkCount);
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
 * The names of everything the list's filters select, from the banner's
 * `data-names-url` (login:table-names on the tables tab). Rejects with the
 * HTTP status on a refusal, so a 401 can say the user was logged out.
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
 * Wire a list to htmx's events on `doc`.
 *
 * @param {Document} doc the document.
 * @param {object} config the list's ids and names, from `listConfig`.
 * @param {object} options test seams: `announceDelay`, `dialog` (see
 *     `bootstrapDialog`), `drawer` (see `bootstrapDrawer`; `onShown` is
 *     optional), `schedule` (setTimeout, for the toasts), `fetchNames` (see
 *     `fetchMatchingNames`) and `loadDrawer` (see `htmxDrawerLoader`).
 * @return {function(): void} removes the listeners again.
 */
export function bindList(
  doc,
  config,
  {
    announceDelay = 60,
    dialog = bootstrapDialog(doc, config),
    drawer = bootstrapDrawer(doc, config),
    schedule = setTimeout,
    fetchNames = fetchMatchingNames,
    loadDrawer = htmxDrawerLoader(doc, config),
  } = {}
) {
  const { ids } = config;
  let focusedId = null;
  // the selection: names in page memory, the scope they were chosen under,
  // the last row clicked (a Shift+click's other end), what "Select all
  // matching" fetched, and what the bulk bar's empty slot says
  const selection = new Set();
  const scopeOf = (region) => (region ? region.dataset.scope || "" : "");
  let scope = scopeOf(doc.getElementById(ids.region));
  let anchor = null;
  let matching = null;
  let note = "";
  const render = () =>
    renderSelection(doc, config, selection, { matching, note });
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
    const shown = visiblePageBox(doc, config);
    focusAfterAction(doc, config, shown ? shown.id : ids.selectPage);
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
  // what the open drawer shows (its `data-drawer-key`), null while closed;
  // a drawer this module asked for itself ({origin, focus}) until it comes;
  // the control to focus once it is shown; an item to open it on once the
  // dialog has closed (a Create: {key, origin})
  let drawerKey = null;
  let pendingDrawer = null;
  let drawerFocus = null;
  let created = null;
  const drawerParam = config.drawer && config.drawer.param;
  const history = doc.defaultView && doc.defaultView.history;
  const writeDrawerParam = (key) => {
    if (drawerParam && history) {
      history.replaceState(
        history.state,
        "",
        withDrawerParam(doc.location.href, drawerParam, key)
      );
    }
  };
  const drawerElement = () =>
    config.drawer && doc.getElementById(config.drawer.id);
  // open the drawer on `key` by itself, through its address template
  const openDrawerOn = (key, origin, focus = null) => {
    const element = drawerElement();
    const template = element && element.dataset.urlTemplate;
    if (!template || !key) {
      return;
    }
    pendingDrawer = { origin: origin || "", focus };
    loadDrawer(template.replace("__key__", encodeURIComponent(key)));
  };
  // a load or a history restore: reopen the drawer when the server says the
  // address names something of the user's, and the address still says so
  const reopenFromAddress = () => {
    const element = drawerElement();
    if (!drawerParam || !element || !element.dataset.open) {
      return;
    }
    const named = new URLSearchParams(doc.location.search).get(drawerParam);
    if (named === element.dataset.open) {
      openDrawerOn(named, element.dataset.openOrigin);
    }
  };
  // the row whose ⋯ opened the dialog, and where focus goes after an action
  let origin = null;
  let afterAction = null;
  // a link in the dialog waiting for it to close (`data-close-then`)
  let thenOpen = null;
  const isRegion = (event) =>
    event.detail &&
    event.detail.target &&
    event.detail.target.id === ids.region;
  const isDialog = (event) =>
    event.detail &&
    event.detail.target &&
    event.detail.target.id === ids.dialogBody;
  const isDrawer = (event) =>
    Boolean(config.drawer) &&
    event.detail &&
    event.detail.target &&
    event.detail.target.id === config.drawer.body;
  const status = (event) => event.detail.xhr && event.detail.xhr.status;

  const onConfigRequest = (event) => {
    const elt = event.detail.elt;
    const bar = doc.getElementById(ids.filters);
    if (elt && elt.hasAttribute && elt.hasAttribute("data-bulk-action")) {
      // a bulk action's preflight: exactly the selected names, in one
      // comma-joined field (Django refuses more than 1,000 parameters)
      event.detail.parameters[config.selectionParam] = [...selection].join(",");
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
      controlValue(bar, elt)
    )) {
      parameters[key] = value;
    }
    if (drawerParam) {
      // the open drawer is page state: no list request carries it
      delete parameters[drawerParam];
    }
  };

  const selectMatching = async (banner) => {
    const asked = scope;
    let names;
    try {
      names = await fetchNames(banner.dataset.namesUrl);
    } catch (error) {
      if (error && error.status === 401) {
        showToast(doc, config, LOGGED_OUT, {
          error: true,
          link: loginLink(doc, config),
        });
      } else if (error && error.status) {
        showToast(doc, config, SERVER_FAILED, { error: true });
      } else {
        showToast(doc, config, UNREACHABLE, { error: true });
      }
      return;
    }
    if (asked !== scope) {
      // the filters changed while the names were on their way
      return;
    }
    matching = names;
    select(names, true);
    const next = doc.getElementById(ids.selectNone);
    if (next) {
      next.focus();
    }
  };

  const onSelect = (event) => {
    const target = event.target;
    const row = target.closest("input[data-select-row]");
    if (row) {
      const region = doc.getElementById(ids.region);
      const names =
        event.shiftKey && anchor
          ? rangeOf(rowBoxes(region), anchor, row.value)
          : [row.value];
      select(names, row.checked);
      anchor = row.value;
      return true;
    }
    if (target.closest("input[data-select-page]")) {
      const boxes = rowBoxes(doc.getElementById(ids.region));
      select(
        boxes.map((box) => box.value),
        target.checked
      );
      return true;
    }
    const banner = target.closest(`#${ids.selectAll}`);
    if (target.closest(`#${ids.selectMatching}`) && banner) {
      selectMatching(banner);
      return true;
    }
    if (target.closest(`#${ids.selectNone}`)) {
      clearSelection();
      focusPageBox();
      return true;
    }
    if (target.closest(`#${ids.bulkClear}`)) {
      clearSelection();
      focusPageBox();
      return true;
    }
    return false;
  };

  // a link in the dialog that opens something else: close the dialog, and
  // send the link its event once the dialog has closed (`dialog.onHidden`)
  const onCloseThen = (event) => {
    const link = event.target.closest("[data-close-then]");
    const body = doc.getElementById(ids.dialogBody);
    if (!link || !body || !body.contains(link)) {
      return false;
    }
    event.preventDefault();
    thenOpen = link;
    dialog.close();
    return true;
  };

  const onClick = (event) => {
    if (!event.target.closest) {
      return;
    }
    if (onCloseThen(event) || onSelect(event)) {
      return;
    }
    const more = event.target.closest(`#${ids.more}`);
    if (more) {
      toggleMore(doc, more);
    }
    const fold = event.target.closest(`#${ids.fold}`);
    if (fold) {
      toggleFold(fold);
    }
  };

  // a ticked or unticked option renames its dropdown's button at once,
  // before the list comes back
  const onChange = (event) => {
    const bar = doc.getElementById(ids.filters);
    if (bar && event.target && bar.contains(event.target)) {
      summarizeMulti(bar);
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
    const request = event.detail.requestConfig;
    const elt = request && request.elt;
    const data = (elt && elt.dataset) || {};
    if (isDialog(event) && data.actionOrigin) {
      origin = data.actionOrigin;
      dialog.open();
      return;
    }
    if (!isDrawer(event)) {
      return;
    }
    const opener = data[config.drawer.origin];
    if (opener || pendingDrawer) {
      drawerOrigin = opener || pendingDrawer.origin;
      drawerFocus = opener ? null : pendingDrawer.focus;
      pendingDrawer = null;
      drawer.open();
    }
    if (drawerOrigin !== null) {
      drawerKey = drawerMark(doc, config, "drawerKey");
      writeDrawerParam(drawerKey);
    }
  };

  const onAfterSettle = (event) => {
    if (isDrawer(event)) {
      restoreDrawerFocus(doc, config, drawerFocusedId);
      drawerFocusedId = null;
      const live = doc.getElementById(config.drawer.live);
      const said = drawerMark(doc, config, "announce");
      if (live && said) {
        announce(live, said, announceDelay);
      }
      return;
    }
    if (!isRegion(event)) {
      return;
    }
    const region = doc.getElementById(ids.region);
    const live = doc.getElementById(ids.live);
    if (region && live) {
      announce(live, region.dataset.announce || "", announceDelay);
    }
    syncFilters(doc, config, region);
    followScope(region);
    if (afterAction !== null) {
      focusAfterAction(doc, config, afterAction);
      afterAction = null;
    } else {
      restoreFocus(doc, config, focusedId);
    }
    focusedId = null;
  };

  const onChanged = (event) => {
    const detail = event.detail || {};
    // what left the dashboard leaves the selection
    forget(detail.gone);
    if (detail.stay) {
      // a change in the drawer: it stays open and keeps focus
      if (detail.message) {
        showToast(doc, config, detail.message, { schedule });
      }
      return;
    }
    afterAction = detail.focus || origin || "";
    origin = null;
    const drawerHere = drawerElement();
    if (detail.created && drawerHere && drawerHere.dataset.urlTemplate) {
      // a Create: the drawer opens on the new item once the dialog has
      // closed and holds focus from there on; closed, focus goes where the
      // event says (the new row's ⋯). A page without the drawer focuses
      // that at once.
      created = { key: detail.created, origin: afterAction };
      afterAction = null;
    }
    dialog.close();
    if (detail.message) {
      showToast(doc, config, detail.message, {
        warning: Boolean(detail.warning),
        details: detail[config.itemsKey] || null,
        schedule,
      });
    }
  };

  const onRefused = (event) => {
    const detail = event.detail || {};
    if (detail.message) {
      showToast(doc, config, detail.message, { error: true });
    }
  };

  const onResponseError = (event) => {
    const status = event.detail && event.detail.xhr && event.detail.xhr.status;
    if (status === 401) {
      showToast(doc, config, LOGGED_OUT, {
        error: true,
        link: loginLink(doc, config),
      });
    } else {
      showToast(doc, config, SERVER_FAILED, { error: true });
    }
  };

  const onSendError = () => {
    showToast(doc, config, UNREACHABLE, { error: true });
  };

  // Cancelled: focus goes back to the ⋯ that opened the dialog. After an
  // action the region's settle does that instead, and after a link that
  // opens something else, what it opens.
  dialog.onHidden(() => {
    if (created) {
      const { key, origin: returnTo } = created;
      created = null;
      origin = null;
      openDrawerOn(key, returnTo, config.drawer.createdFocus);
      return;
    }
    if (thenOpen) {
      const link = thenOpen;
      thenOpen = null;
      origin = null;
      link.dispatchEvent(new CustomEvent(DIALOG_CLOSED));
      return;
    }
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
      focusAfterAction(doc, config, drawerOrigin);
    }
    drawerOrigin = null;
    drawerFocus = null;
    if (drawerKey !== null) {
      drawerKey = null;
      writeDrawerParam(null);
    }
  });

  // Shown: a drawer opened on a new item puts focus where the config says
  // (the add search), after Bootstrap has focused the drawer itself.
  if (drawer.onShown) {
    drawer.onShown(() => {
      const target = drawerFocus && doc.getElementById(drawerFocus);
      drawerFocus = null;
      if (target) {
        target.focus();
      }
    });
  }

  // htmx wrote the list's own address, which never carries the drawer: put
  // it back while the drawer is open
  const onAddressWritten = () => {
    if (drawerKey !== null) {
      writeDrawerParam(drawerKey);
    }
  };

  // Bootstrap's modal ignores `autofocus` and focuses itself: a dialog
  // that is a form (Create and Edit) gets focus on the field marked so once
  // it is shown; a confirmation keeps Bootstrap's focus
  const onDialogShown = (event) => {
    if (!event.target || event.target.id !== ids.dialog) {
      return;
    }
    const field = event.target.querySelector("[autofocus]");
    if (field) {
      field.focus();
    }
  };

  const onHistoryRestore = () => {
    const region = doc.getElementById(ids.region);
    syncFilters(doc, config, region);
    followScope(region);
    // the page was put back, its drawer closed with it
    drawerKey = null;
    drawerOrigin = null;
    reopenFromAddress();
  };

  const listeners = [
    ["htmx:configRequest", onConfigRequest],
    ["htmx:beforeSwap", onBeforeSwap],
    ["htmx:afterSwap", onAfterSwap],
    ["htmx:afterSettle", onAfterSettle],
    ["htmx:historyRestore", onHistoryRestore],
    ["htmx:pushedIntoHistory", onAddressWritten],
    ["htmx:replacedInHistory", onAddressWritten],
    ["htmx:responseError", onResponseError],
    ["htmx:sendError", onSendError],
    [config.changedEvent, onChanged],
    [config.refusedEvent, onRefused],
    ["click", onClick],
    ["change", onChange],
    ["shown.bs.modal", onDialogShown],
  ];
  for (const [name, listener] of listeners) {
    doc.body.addEventListener(name, listener);
  }
  // in the capture phase, so the swallowed click reaches neither htmx nor
  // Bootstrap's dropdown, which would close the menu and hide the reason
  doc.body.addEventListener("click", onGuard, true);
  const popovers = bindPopovers(doc);
  render();
  // htmx processes the page once it has loaded; a drawer it is asked to
  // fill before then would not open
  if (doc.readyState === "loading") {
    doc.addEventListener("DOMContentLoaded", reopenFromAddress, { once: true });
  } else {
    reopenFromAddress();
  }
  return () => {
    for (const [name, listener] of listeners) {
      doc.body.removeEventListener(name, listener);
    }
    doc.body.removeEventListener("click", onGuard, true);
    popovers.unbind();
  };
}
