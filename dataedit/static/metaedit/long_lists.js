// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

/*
Keeps very long annotation lists out of the metadata editor's form.

json-editor (the form library) builds an array one row at a time, and every
row it adds walks all the rows before it (``refreshValue`` and the change
notifications above it). Building n rows therefore costs about n² row
operations: measured on 2026-10-02, 1,600 entries took 17 s, and a column with
4,525 value references never finished loading. A newer json-editor (2.17.2)
behaves the same.

So, before the form is built, every ``isAbout`` and ``valueReference`` list of a
column that is longer than ``LONG_LIST_LIMIT`` is set aside and the form gets an
empty list in its place. Before saving or downloading, the set-aside entries
are put back in front of whatever the form holds there, so nothing is lost and
entries added in the form are kept. The field is found by its name, because
the save path rebuilds the fields by name too (``fixData`` in metaedit.js).

This is a stopgap until annotation has its own editor with search and paging.
*/

export const LONG_LIST_LIMIT = 200;

export const ANNOTATION_LISTS = ["isAbout", "valueReference"];

const LIST_NAMES = {
  isAbout: ["“is about” annotation", "“is about” annotations"],
  valueReference: ["value reference", "value references"],
};

function copy(value) {
  return JSON.parse(JSON.stringify(value));
}

function fieldsOf(resource) {
  const fields = resource && resource.schema && resource.schema.fields;
  return Array.isArray(fields) ? fields : [];
}

/*
Returns ``{metadata, setAside}``: a copy of ``metadata`` with every annotation
list longer than ``limit`` emptied, and one ``{resource, field, list, items}``
entry per emptied list (``resource`` is the index, ``field`` the column name).
The document passed in is not changed.
*/
export function setAsideLongLists(metadata, limit = LONG_LIST_LIMIT) {
  const form = copy(metadata);
  const setAside = [];
  (Array.isArray(form.resources) ? form.resources : []).forEach(
    (resource, index) => {
      fieldsOf(resource).forEach((field) => {
        ANNOTATION_LISTS.forEach((list) => {
          const items = field[list];
          if (Array.isArray(items) && items.length > limit) {
            setAside.push({ resource: index, field: field.name, list, items });
            field[list] = [];
          }
        });
      });
    }
  );
  return { metadata: form, setAside };
}

/*
Returns a copy of ``formValue`` (what the editor holds) with every set-aside
list put back, in front of the entries the form holds for that list. A field or
resource the form no longer has is recreated with just its name and the list,
so the save path, which merges fields by name, keeps the entries.
*/
export function restoreLongLists(formValue, setAside) {
  const saved = copy(formValue);
  setAside.forEach(({ resource, field, list, items }) => {
    if (!Array.isArray(saved.resources)) saved.resources = [];
    if (!saved.resources[resource]) saved.resources[resource] = {};
    const target = saved.resources[resource];
    if (!target.schema) target.schema = {};
    if (!Array.isArray(target.schema.fields)) target.schema.fields = [];
    let column = target.schema.fields.find((f) => f && f.name === field);
    if (!column) {
      column = { name: field };
      target.schema.fields.push(column);
    }
    const added = Array.isArray(column[list]) ? column[list] : [];
    column[list] = [...copy(items), ...added];
  });
  return saved;
}

/* "Column “x”: 4,525 value references" */
export function describeSetAside({ field, list, items }) {
  const [one, many] = LIST_NAMES[list] || [list, list];
  const count = items.length;
  return `Column “${field}”: ${count.toLocaleString("en")} ${count === 1 ? one : many}`;
}
