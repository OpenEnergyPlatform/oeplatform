// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

import { describe, expect, it } from "vitest";

import {
  LONG_LIST_LIMIT,
  describeSetAside,
  restoreLongLists,
  setAsideLongLists,
} from "./long_lists.js";

function entries(count, prefix = "term") {
  return Array.from({ length: count }, (_, i) => ({
    "@id": null,
    name: `${prefix} ${i}`,
    value: `value ${i}`,
  }));
}

function metadata(fields, extra = {}) {
  return {
    name: "t",
    keywords: [],
    ...extra,
    resources: [{ name: "t", schema: { fields } }],
  };
}

describe("setAsideLongLists", () => {
  it("leaves a list at the limit in the form", () => {
    const doc = metadata([
      { name: "a", valueReference: entries(LONG_LIST_LIMIT) },
    ]);
    const { metadata: form, setAside } = setAsideLongLists(doc);
    expect(setAside).toEqual([]);
    expect(form).toEqual(doc);
  });

  it("takes a longer list out of the form and records it", () => {
    const long = entries(LONG_LIST_LIMIT + 1);
    const doc = metadata([
      { name: "a", type: "text", valueReference: long },
      { name: "b", isAbout: entries(3) },
    ]);
    const { metadata: form, setAside } = setAsideLongLists(doc);
    expect(form.resources[0].schema.fields[0].valueReference).toEqual([]);
    expect(form.resources[0].schema.fields[0].type).toBe("text");
    expect(form.resources[0].schema.fields[1].isAbout).toHaveLength(3);
    expect(setAside).toEqual([
      { resource: 0, field: "a", list: "valueReference", items: long },
    ]);
  });

  it("does not change the document it was given", () => {
    const doc = metadata([{ name: "a", isAbout: entries(500) }]);
    const before = JSON.stringify(doc);
    setAsideLongLists(doc);
    expect(JSON.stringify(doc)).toBe(before);
  });

  it("covers both annotation lists, on every field of every resource", () => {
    const doc = {
      resources: [
        { schema: { fields: [{ name: "a", isAbout: entries(300) }] } },
        {
          schema: {
            fields: [
              { name: "a", valueReference: entries(250) },
              { name: "b", isAbout: entries(201), valueReference: entries(9) },
            ],
          },
        },
      ],
    };
    const { setAside } = setAsideLongLists(doc);
    expect(
      setAside.map(({ resource, field, list, items }) => [
        resource,
        field,
        list,
        items.length,
      ])
    ).toEqual([
      [0, "a", "isAbout", 300],
      [1, "a", "valueReference", 250],
      [1, "b", "isAbout", 201],
    ]);
  });

  it("leaves other long lists alone: only annotations are set aside", () => {
    const keywords = Array.from({ length: 500 }, (_, i) => `k${i}`);
    const doc = metadata([{ name: "a" }], { keywords });
    const { metadata: form, setAside } = setAsideLongLists(doc);
    expect(setAside).toEqual([]);
    expect(form.keywords).toHaveLength(500);
  });

  it("copes with a document without resources or fields", () => {
    for (const doc of [
      {},
      { resources: [{}] },
      { resources: [{ schema: {} }] },
    ]) {
      expect(setAsideLongLists(doc).setAside).toEqual([]);
    }
  });
});

describe("restoreLongLists", () => {
  it("round-trips: an untouched form saves the original document", () => {
    const doc = metadata([
      { name: "a", valueReference: entries(1000) },
      { name: "b", isAbout: entries(2) },
    ]);
    const { metadata: form, setAside } = setAsideLongLists(doc);
    expect(restoreLongLists(form, setAside)).toEqual(doc);
  });

  it("finds the field by its name, not its position", () => {
    const long = entries(300);
    const { metadata: form, setAside } = setAsideLongLists(
      metadata([{ name: "a" }, { name: "b", valueReference: long }])
    );
    form.resources[0].schema.fields.reverse();
    const saved = restoreLongLists(form, setAside);
    const b = saved.resources[0].schema.fields.find((f) => f.name === "b");
    expect(b.valueReference).toEqual(long);
  });

  it("keeps entries added in the form, after the ones set aside", () => {
    const long = entries(300);
    const { metadata: form, setAside } = setAsideLongLists(
      metadata([{ name: "a", isAbout: long }])
    );
    const added = { "@id": "http://example.org/x", name: "x" };
    form.resources[0].schema.fields[0].isAbout.push(added);
    const saved = restoreLongLists(form, setAside);
    expect(saved.resources[0].schema.fields[0].isAbout).toEqual([
      ...long,
      added,
    ]);
  });

  it("brings back a field the form lost, with its list", () => {
    const long = entries(300);
    const { metadata: form, setAside } = setAsideLongLists(
      metadata([{ name: "a" }, { name: "b", valueReference: long }])
    );
    form.resources[0].schema.fields = [{ name: "a" }];
    const saved = restoreLongLists(form, setAside);
    expect(saved.resources[0].schema.fields).toEqual([
      { name: "a" },
      { name: "b", valueReference: long },
    ]);
  });

  it("does not change the form value it was given", () => {
    const { metadata: form, setAside } = setAsideLongLists(
      metadata([{ name: "a", valueReference: entries(300) }])
    );
    const before = JSON.stringify(form);
    restoreLongLists(form, setAside);
    expect(JSON.stringify(form)).toBe(before);
  });

  it("returns the form value unchanged when nothing was set aside", () => {
    const form = metadata([{ name: "a", isAbout: entries(2) }]);
    expect(restoreLongLists(form, [])).toEqual(form);
  });
});

describe("describeSetAside", () => {
  it("names the column, the kind of annotation and the count", () => {
    expect(
      describeSetAside({
        field: "iamc",
        list: "valueReference",
        items: entries(4525),
      })
    ).toBe("Column “iamc”: 4,525 value references");
    expect(
      describeSetAside({
        field: "region",
        list: "isAbout",
        items: entries(201),
      })
    ).toBe("Column “region”: 201 “is about” annotations");
  });
});
