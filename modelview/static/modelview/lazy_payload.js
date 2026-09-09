// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// The Model/Framework factsheet list page's lazy column payload.
//
// The page ships the eight default columns for every row and fetches the
// other 165 once, on the first column toggle or the first search keystroke.
// The search trigger is not optional: DataTables searches hidden columns too,
// so with eight columns loaded a search that used to find a model by its
// citation text would return nothing, with no indication why.
//
// "Once" is the whole contract, and it is browser state -- a Django test
// cannot see a second fetch. Hence a module with tests.

/**
 * Whether a group of columns needs data the initial payload does not carry.
 *
 * The sidebar toggles a labelled group of fields at a time, so one missing
 * field in the group is enough: the fetch brings all of them.
 *
 * @param {string[]|undefined} fields the group's field names.
 * @param {string[]} initialColumns the columns every row already carries.
 * @return {boolean} true when the full payload is needed.
 */
export function needsFullPayload(fields, initialColumns) {
  if (!fields || !fields.length) {
    return false;
  }
  const present = new Set(initialColumns);
  return fields.some((field) => !present.has(field));
}

/**
 * A "fetch the rest, once" function.
 *
 * Every caller gets the same promise, so overlapping calls -- which is what
 * typing produces -- share one request. A rejected fetch is NOT cached: a
 * dropped connection would otherwise leave the search box permanently unable
 * to match the columns it cannot see.
 *
 * @param {function(): Promise<object[]>} load fetches the full row payload.
 * @param {function(object[]): void} apply hands those rows to the table.
 * @return {function(): Promise<void>} call it as often as you like.
 */
export function createLoader(load, apply) {
  let pending = null;
  return function ensure() {
    if (!pending) {
      pending = Promise.resolve()
        .then(load)
        .then(apply)
        .catch((error) => {
          pending = null;
          throw error;
        });
    }
    return pending;
  };
}

/**
 * Show or hide a sidebar group's columns, fetching their data first if needed.
 *
 * Fetch *then* reveal: revealing first would show a column of empty cells for
 * as long as the request takes, which reads as a broken column rather than as
 * a loading one. A group already in the initial payload reveals synchronously
 * and asks for nothing, and hiding never fetches -- there is nothing to show.
 *
 * @param {string[]|undefined} fields the group's field names.
 * @param {boolean} checked whether the group's checkbox is now checked.
 * @param {string[]} initialColumns the columns every row already carries.
 * @param {function(): Promise<void>} ensure the loader from `createLoader`.
 * @param {function(string, boolean): void} setVisible shows or hides one
 *   column by field name.
 * @return {Promise<void>} resolved once the columns are shown or hidden.
 */
export function toggleColumns(
  fields,
  checked,
  initialColumns,
  ensure,
  setVisible
) {
  const show = () => (fields || []).forEach((f) => setVisible(f, checked));
  if (checked && needsFullPayload(fields, initialColumns)) {
    return ensure().then(show);
  }
  show();
  return Promise.resolve();
}

/**
 * Ask for the full payload the first time anyone types in the search box.
 *
 * DataTables searches hidden columns too, so with the initial payload alone a
 * search that used to match a model by its citation text returns nothing and
 * explains nothing. The box does not exist until the table has been
 * initialised, so call this after that.
 *
 * @param {ParentNode} root the element to search, usually `document`.
 * @param {function(): Promise<void>} ensure the loader from `createLoader`.
 * @return {boolean} whether a search box was found to bind.
 */
export function bindSearchTrigger(root, ensure) {
  const box = root.querySelector("#overview_filter input");
  if (!box) {
    return false;
  }
  box.addEventListener("input", () => ensure());
  return true;
}
