// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// What a scenario's input/output dataset field shows, and what it sends back.
//
// The field offers only the tables of the scenario topic, and a stored link
// is shown only when its label equals one of those options. The bundle update
// (factsheet/views.py) replaces the whole bundle with what the form sends, so
// anything the field drops on a change is deleted from the graph. A stored
// link the field cannot show -- an external address, a table that left the
// topic, a label that differs from the table's display name -- is therefore
// carried through untouched rather than lost (#2522).
//
// A link is stored as {key, idx, value: {label, url}}. The key becomes the
// node's IRI (.../oekg/{input,output}_datasets/<key>), so a kept link keeps
// its key, and a new one gets a freshly minted key: a key derived from the
// table id would be the same node in every bundle citing that table.

const matches = (link, option) => option.label === link.value?.label;

/** The options the field shows as selected for these stored links. */
export function visibleSelection(stored, options) {
  return stored
    .map((link) => options.find((option) => matches(link, option)))
    .filter(Boolean);
}

/** The stored links no option matches, which the field cannot show. */
export function unlistedLinks(stored, options) {
  return stored.filter(
    (link) => !options.some((option) => matches(link, option)),
  );
}

/**
 * The links to store after the user changed the field's selection.
 *
 * `selected` is what the field now shows (options only). Every link the field
 * could not show is appended unchanged; a kept link keeps its stored key and
 * value; a newly picked option gets `mint()` as its key.
 */
export function mergeSelection(stored, selected, options, mint) {
  const chosen = selected.map((option) => {
    const existing = stored.find((link) => matches(link, option));
    return existing ?? { key: mint(), value: option };
  });
  // A link written without a uuid reads back with a null key; the update view
  // builds the node's IRI from the key, so every link leaves here with one.
  return [...chosen, ...unlistedLinks(stored, options)].map((link, idx) => ({
    ...link,
    key: link.key || mint(),
    idx,
  }));
}
