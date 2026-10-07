// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// The profile dashboard's tables tab, in the browser (spec #2551).
//
// What the tab does in the page is `dash_list.js`, which knows no Tables;
// this is its binding to the tables tab's ids (`tables-…` for the list,
// `table-…` for the action dialog and the access drawer), its events
// (`tables-changed`, `tables-refused`) and the parameter a bulk action sends
// the selection in (`tables`). The helpers keep the signatures they had
// before the split (#2617), bound to the tables tab, so the page and every
// test import them from here as before.

import {
  bindList,
  bootstrapDialog as listDialog,
  bootstrapDrawer as listDrawer,
  focusAfterAction as listFocusAfterAction,
  listConfig,
  loginLink as listLoginLink,
  renderSelection as listRenderSelection,
  restoreDrawerFocus as listRestoreDrawerFocus,
  restoreFocus as listRestoreFocus,
  showToast as listShowToast,
  syncFilters as listSyncFilters,
  visiblePageBox as listVisiblePageBox,
} from "./dash_list.js";

export {
  LOGGED_OUT,
  SELECTION_CLEARED,
  SERVER_FAILED,
  TOAST_TIMEOUT,
  UNREACHABLE,
  announce,
  controlValue,
  fetchMatchingNames,
  filterParameters,
  focusedIdWithin,
  isUnavailable,
  pageBoxes,
  rangeOf,
  rowBoxes,
  toggleFold,
  toggleMore,
} from "./dash_list.js";

export const TABLES = listConfig({
  plural: "tables",
  singular: "table",
  drawer: "access",
});

export const REGION_ID = TABLES.ids.region;
export const HEADING_ID = TABLES.ids.heading;
export const LIVE_ID = TABLES.ids.live;
export const SEARCH_ID = TABLES.ids.search;
export const FILTERS_ID = TABLES.ids.filters;
export const MORE_ID = TABLES.ids.more;
export const MORE_COUNT_ID = TABLES.ids.moreCount;
export const FOLD_ID = TABLES.ids.fold;
export const FOLD_COUNT_ID = TABLES.ids.foldCount;
export const TAB_ID = TABLES.ids.tab;
export const DIALOG_ID = TABLES.ids.dialog;
export const DIALOG_BODY_ID = TABLES.ids.dialogBody;
export const DRAWER_ID = TABLES.drawer.id;
export const DRAWER_BODY_ID = TABLES.drawer.body;
export const DRAWER_TITLE_ID = TABLES.drawer.title;
export const DRAWER_CONFIRM_ID = TABLES.drawer.confirm;
export const TOASTS_POLITE_ID = TABLES.ids.toastsPolite;
export const TOASTS_ASSERTIVE_ID = TABLES.ids.toastsAssertive;
export const BULK_IDLE_ID = TABLES.ids.bulkIdle;
export const BULK_NOTE_ID = TABLES.ids.bulkNote;
export const BULK_BAR_ID = TABLES.ids.bulkBar;
export const BULK_COUNT_ID = TABLES.ids.bulkCount;
export const BULK_CLEAR_ID = TABLES.ids.bulkClear;
export const SELECT_PAGE_ID = TABLES.ids.selectPage;
export const SELECT_PAGE_STACKED_ID = TABLES.ids.selectPageStacked;
export const SELECT_ALL_ID = TABLES.ids.selectAll;
export const SELECT_MATCHING_ID = TABLES.ids.selectMatching;
export const SELECT_NONE_ID = TABLES.ids.selectNone;

export const restoreFocus = (doc, id) => listRestoreFocus(doc, TABLES, id);
export const syncFilters = (doc, region) =>
  listSyncFilters(doc, TABLES, region);
export const focusAfterAction = (doc, id) =>
  listFocusAfterAction(doc, TABLES, id);
export const showToast = (doc, message, options) =>
  listShowToast(doc, TABLES, message, options);
export const loginLink = (doc) => listLoginLink(doc, TABLES);
export const bootstrapDialog = (doc) => listDialog(doc, TABLES);
export const bootstrapDrawer = (doc) => listDrawer(doc, TABLES);
export const restoreDrawerFocus = (doc, id) =>
  listRestoreDrawerFocus(doc, TABLES, id);
export const visiblePageBox = (doc) => listVisiblePageBox(doc, TABLES);
export const renderSelection = (doc, selection, options) =>
  listRenderSelection(doc, TABLES, selection, options);

/**
 * Wire the tables tab to htmx's events on `doc`.
 *
 * @param {Document} doc the document.
 * @param {object} options test seams, as `bindList` takes them.
 * @return {function(): void} removes the listeners again.
 */
export function bindTablesTab(doc, options = {}) {
  return bindList(doc, TABLES, options);
}
