// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// The profile dashboard's datasets tab, in the browser (spec #2613).
//
// What the tab does in the page is `dash_list.js`, which knows no Datasets:
// live filters, the count announced from the live region outside the
// swapped region, focus put back by id after a swap. This is its binding to
// the datasets tab's ids (`datasets-…` for the list, `dataset-…` for the
// action dialog and the members drawer) and its events (`datasets-changed`,
// `datasets-refused`). The members drawer is page state in the address,
// `?members=<name>`, and opens by itself after a Create.

import { bindList, listConfig } from "./dash_list.js";

export const DATASETS = listConfig({
  plural: "datasets",
  singular: "dataset",
  drawer: "members",
  // the members drawer is in the address, `?members=<name>` (#2625)
  drawerParam: "members",
  // after a Create the drawer opens on the new Dataset, ready to add to it
  createdFocus: "dataset-members-add-search",
});

/**
 * Wire the datasets tab to htmx's events on `doc`.
 *
 * @param {Document} doc the document.
 * @param {object} options test seams, as `bindList` takes them.
 * @return {function(): void} removes the listeners again.
 */
export function bindDatasetsTab(doc, options = {}) {
  return bindList(doc, DATASETS, options);
}
