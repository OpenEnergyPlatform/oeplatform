// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// The Model/Framework factsheet list page's tag filter.
//
// Extracted from the inline script in `modellist.html` because the two bugs
// this filter shipped were both here, and both invisible to a Django test:
// the "Download CSV" link carried the checkbox DOM ids where the endpoint
// filters on raw primary keys (so a filtered download silently returned a
// header-only file), and the checkbox restored from the URL rendered with no
// tick, because the input is `display: none` and the tick comes from a class
// that `oep-tags.js` only toggles on click.
//
// Everything here is either pure or takes its DOM root as an argument, so it
// can be tested without a page. The DataTables wiring stays in the template,
// where the payload lives.

/**
 * Add or remove `value` from the active selection.
 *
 * @param {string[]} activeTags currently selected tag primary keys.
 * @param {string} value the tag primary key the checkbox carries.
 * @param {boolean} checked whether that checkbox is now checked.
 * @return {string[]} a new selection; the input is not modified.
 */
export function toggleTag(activeTags, value, checked) {
  const without = activeTags.filter((tag) => tag !== value);
  return checked ? without.concat([value]) : without;
}

/**
 * The `?tags=` query string for a selection, or "" when nothing is selected.
 *
 * Raw primary keys, the one format the page, the URL and the CSV download all
 * share. An empty selection yields no parameter at all rather than `?tags=`,
 * so an unfiltered URL is the plain page URL.
 *
 * @param {string[]} activeTags currently selected tag primary keys.
 * @return {string} the query string, including the leading "?".
 */
export function filterQuery(activeTags) {
  return activeTags.length ? "?tags=" + activeTags.join(",") : "";
}

/**
 * The page URL with only its `tags` parameter rewritten.
 *
 * Every other parameter and the fragment survive: rebuilding the whole query
 * string from the selection would silently drop them.
 *
 * @param {{pathname: string, search: string, hash: string}} location the
 *   current location, or anything shaped like it.
 * @param {string[]} activeTags currently selected tag primary keys.
 * @return {string} the URL to hand to `history.replaceState`.
 */
export function filteredUrl(location, activeTags) {
  const params = new URLSearchParams(location.search || "");
  if (activeTags.length) {
    params.set("tags", activeTags.join(","));
  } else {
    params.delete("tags");
  }
  const query = params.toString();
  return location.pathname + (query ? "?" + query : "") + (location.hash || "");
}

/**
 * Whether a table row carries every tag in the active selection.
 *
 * AND semantics, deliberately: selecting two tags narrows to the factsheets
 * carrying both. Compares raw primary keys on both sides -- comparing a
 * prefixed id against a bare key is what made the filter and the CSV download
 * disagree.
 *
 * @param {{pk: string}[]} rowTags the tags the row carries.
 * @param {string[]} activeTags currently selected tag primary keys.
 * @return {boolean} true when the row should stay visible.
 */
export function rowMatchesTags(rowTags, activeTags) {
  if (!activeTags.length) {
    return true;
  }
  if (!rowTags) {
    return false;
  }
  const present = new Set(rowTags.map((tag) => tag.pk));
  return activeTags.every((required) => present.has(required));
}

/**
 * The primary keys of the tag checkboxes currently checked in `root`.
 *
 * This is how the selection is seeded on load: the server renders the
 * checkboxes from `?tags=`, and the page reads its state back off them rather
 * than parsing the URL a second time in a second format.
 *
 * @param {ParentNode} root the element to search, usually `document`.
 * @return {string[]} the checked tags' primary keys, in document order.
 */
export function checkedTagValues(root) {
  return Array.from(root.querySelectorAll(".tag-checkbox:checked")).map(
    (box) => box.value
  );
}

/**
 * Give every checked tag checkbox its visible tick.
 *
 * The input itself is `display: none`; the tick is drawn from
 * `tag-checkbox-checked` on the surrounding label, and `oep-tags.js` only ever
 * toggles that on click. Without this, a filter restored from the URL filters
 * the table while the sidebar renders as though nothing were selected.
 *
 * @param {ParentNode} root the element to search, usually `document`.
 * @return {void}
 */
export function showCheckedTags(root) {
  root.querySelectorAll(".tag-checkbox").forEach((box) => {
    box.parentElement.classList.toggle("tag-checkbox-checked", box.checked);
  });
}
