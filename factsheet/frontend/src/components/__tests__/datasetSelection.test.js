// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// The scenario form's dataset fields offer only the tables of the scenario
// topic, while a stored link can point anywhere: a databus URL, a table that
// left the topic, a table whose display name differs from the stored label.
// The bundle update replaces the whole bundle with what the form sends, so a
// link the field cannot show must still be sent back, or saving deletes it
// (#2522). That is a property of state the browser holds, so it lives here.
import { describe, expect, it } from "vitest";

import {
  mergeSelection,
  unlistedLinks,
  visibleSelection,
} from "../datasetSelection.js";

const options = [
  { id: 1, label: "Grid A", url: "https://oep/tables/grid_a", name: "grid_a" },
  { id: 2, label: "Grid B", url: "https://oep/tables/grid_b", name: "grid_b" },
];

const storedGridA = {
  key: "0b0c2c6e-stored-a",
  idx: "0",
  value: { label: "Grid A", url: "https://oep/tables/grid_a" },
};
const storedDatabus = {
  key: "7f1e-stored-databus",
  idx: "1",
  value: { label: "Databus thing", url: "https://databus.example/x" },
};

let counter = 0;
const mint = () => `minted-${++counter}`;

describe("visibleSelection", () => {
  it("shows the options that match a stored link", () => {
    expect(visibleSelection([storedGridA, storedDatabus], options)).toEqual([
      options[0],
    ]);
  });
});

describe("unlistedLinks", () => {
  it("returns the stored links no option matches", () => {
    expect(unlistedLinks([storedGridA, storedDatabus], options)).toEqual([
      storedDatabus,
    ]);
  });

  it("treats every link as unlisted while the option list is empty", () => {
    expect(unlistedLinks([storedGridA], [])).toEqual([storedGridA]);
  });
});

describe("mergeSelection", () => {
  it("keeps a link the field cannot show when another table is added", () => {
    const stored = [storedGridA, storedDatabus];
    const result = mergeSelection(stored, [options[0], options[1]], options, mint);
    expect(result.map((l) => l.value.url)).toContain("https://databus.example/x");
  });

  it("keeps a link the field cannot show when every visible one is removed", () => {
    const result = mergeSelection([storedGridA, storedDatabus], [], options, mint);
    expect(result).toEqual([{ ...storedDatabus, idx: 0 }]);
  });

  it("keeps the stored key and value of a link the user keeps", () => {
    const [kept] = mergeSelection([storedGridA], [options[0]], options, mint);
    expect(kept.key).toBe("0b0c2c6e-stored-a");
    expect(kept.value).toEqual(storedGridA.value);
  });

  it("mints a fresh key for a newly picked table, never one derived from its id", () => {
    const result = mergeSelection([], [options[1]], options, mint);
    expect(result).toHaveLength(1);
    expect(result[0].key).toMatch(/^minted-/);
    expect(result[0].key).not.toBe("dataset_2");
    expect(result[0].value).toBe(options[1]);
  });

  it("drops a visible link the user removed", () => {
    const result = mergeSelection([storedGridA], [], options, mint);
    expect(result).toEqual([]);
  });

  it("numbers the links in order", () => {
    const result = mergeSelection([storedGridA, storedDatabus], [options[0], options[1]], options, mint);
    expect(result.map((l) => l.idx)).toEqual([0, 1, 2]);
  });

  it("gives a key to a stored link that has none, since its IRI is built from it", () => {
    const keyless = { key: null, idx: null, value: { label: "Old", url: "https://x" } };
    const result = mergeSelection([keyless], [], options, mint);
    expect(result[0].key).toMatch(/^minted-/);
    expect(result[0].value).toEqual(keyless.value);
  });

  it("keeps every link when the option list has not loaded yet", () => {
    const result = mergeSelection([storedGridA, storedDatabus], [], [], mint);
    expect(result.map((l) => l.key)).toEqual([storedGridA.key, storedDatabus.key]);
  });
});
