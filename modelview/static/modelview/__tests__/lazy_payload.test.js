// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// @vitest-environment happy-dom
//
// The list page ships eight columns and fetches the other 165 on demand. The
// property that matters is "once": a column toggle and every search keystroke
// both ask for the full payload, and the table must not refetch 2 MB per
// keystroke. That is state, it lives in the browser, and no Django test can
// see it -- so it lives in a module with tests.
import { describe, expect, it, vi } from "vitest";

import {
  bindSearchTrigger,
  createLoader,
  needsFullPayload,
  toggleColumns,
} from "../lazy_payload.js";

describe("needsFullPayload", () => {
  it("is false for a group already in the initial payload", () => {
    expect(needsFullPayload(["acronym"], ["acronym", "license"])).toBe(false);
  });

  it("is true as soon as one field of the group is missing", () => {
    expect(needsFullPayload(["acronym", "montecarlo"], ["acronym"])).toBe(true);
  });

  it("is true for a group of only missing fields", () => {
    expect(needsFullPayload(["montecarlo"], ["acronym"])).toBe(true);
  });

  it("is false for an empty group", () => {
    expect(needsFullPayload([], ["acronym"])).toBe(false);
  });

  it("treats a missing group as nothing to fetch", () => {
    expect(needsFullPayload(undefined, ["acronym"])).toBe(false);
  });
});

describe("createLoader", () => {
  it("fetches on the first call", async () => {
    const load = vi.fn(async () => ["row"]);
    const apply = vi.fn();

    await createLoader(load, apply)();

    expect(load).toHaveBeenCalledTimes(1);
    expect(apply).toHaveBeenCalledWith(["row"]);
  });

  it("does not fetch again on a second call", async () => {
    const load = vi.fn(async () => ["row"]);
    const apply = vi.fn();
    const ensure = createLoader(load, apply);

    await ensure();
    await ensure();
    await ensure();

    expect(load).toHaveBeenCalledTimes(1);
    expect(apply).toHaveBeenCalledTimes(1);
  });

  it("shares one fetch between calls that overlap", async () => {
    // What typing does: several keystrokes land before the first response.
    let release;
    const load = vi.fn(() => new Promise((resolve) => (release = resolve)));
    const apply = vi.fn();
    const ensure = createLoader(load, apply);

    const first = ensure();
    const second = ensure();
    await Promise.resolve();  // the loader calls `load` in a microtask
    release(["row"]);
    await Promise.all([first, second]);

    expect(load).toHaveBeenCalledTimes(1);
    expect(apply).toHaveBeenCalledTimes(1);
  });

  it("lets a failed fetch be retried", async () => {
    // A dropped connection must not leave the search box permanently unable
    // to match the 165 columns it cannot see.
    const load = vi
      .fn()
      .mockRejectedValueOnce(new Error("offline"))
      .mockResolvedValueOnce(["row"]);
    const apply = vi.fn();
    const ensure = createLoader(load, apply);

    await expect(ensure()).rejects.toThrow("offline");
    await ensure();

    expect(load).toHaveBeenCalledTimes(2);
    expect(apply).toHaveBeenCalledTimes(1);
  });

  it("does not fetch before it is asked to", () => {
    const load = vi.fn();

    createLoader(load, vi.fn());

    expect(load).not.toHaveBeenCalled();
  });
});

describe("toggleColumns", () => {
  /**
   * Record what was shown or hidden.
   *
   * @return {{calls: [string, boolean][], setVisible: function}} the spy.
   */
  function recorder() {
    const calls = [];
    return { calls, setVisible: (field, visible) => calls.push([field, visible]) };
  }

  it("reveals a group already in the initial payload without fetching", async () => {
    const ensure = vi.fn();
    const spy = recorder();

    await toggleColumns(["acronym"], true, ["acronym"], ensure, spy.setVisible);

    expect(ensure).not.toHaveBeenCalled();
    expect(spy.calls).toEqual([["acronym", true]]);
  });

  it("fetches before revealing a group the initial payload lacks", async () => {
    const order = [];
    const ensure = vi.fn(async () => order.push("fetch"));
    const setVisible = (field) => order.push("show:" + field);

    await toggleColumns(["montecarlo"], true, ["acronym"], ensure, setVisible);

    // Reveal-then-fill would show a column of empty cells for the length of
    // the request, which reads as broken rather than as loading.
    expect(order).toEqual(["fetch", "show:montecarlo"]);
  });

  it("reveals every field of the group", async () => {
    const spy = recorder();

    await toggleColumns(
      ["montecarlo", "interfaces"],
      true,
      [],
      vi.fn(async () => {}),
      spy.setVisible
    );

    expect(spy.calls).toEqual([
      ["montecarlo", true],
      ["interfaces", true],
    ]);
  });

  it("hides without fetching, even for a group it does not have", async () => {
    const ensure = vi.fn();
    const spy = recorder();

    await toggleColumns(["montecarlo"], false, ["acronym"], ensure, spy.setVisible);

    expect(ensure).not.toHaveBeenCalled();
    expect(spy.calls).toEqual([["montecarlo", false]]);
  });

  it("does nothing for an unknown group", async () => {
    const ensure = vi.fn();
    const spy = recorder();

    await toggleColumns(undefined, true, [], ensure, spy.setVisible);

    expect(ensure).not.toHaveBeenCalled();
    expect(spy.calls).toEqual([]);
  });
});

describe("bindSearchTrigger", () => {
  it("asks for the full payload on the first keystroke", () => {
    document.body.innerHTML =
      '<div id="overview_filter"><input type="search"></div>';
    const ensure = vi.fn();

    expect(bindSearchTrigger(document, ensure)).toBe(true);
    document
      .querySelector("#overview_filter input")
      .dispatchEvent(new Event("input"));

    expect(ensure).toHaveBeenCalledTimes(1);
  });

  it("says so when there is no search box to bind", () => {
    document.body.innerHTML = "";

    expect(bindSearchTrigger(document, vi.fn())).toBe(false);
  });
});
