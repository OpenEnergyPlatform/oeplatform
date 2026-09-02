// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later
import { beforeEach, describe, expect, it } from "vitest";

import {
  _resetStore,
  getState,
  initStore,
  selectField,
  setDraftState,
  setFieldReview,
  setFinished,
  subscribe,
} from "../core/store.js";

describe("store", () => {
  beforeEach(() => _resetStore());

  it("initStore sets config/role/fields and notifies subscribers", () => {
    let calls = 0;
    subscribe(() => (calls += 1));

    initStore({
      config: { table: "t" },
      role: "reviewer",
      fields: [{ key: "a", isEmpty: false }],
    });

    expect(getState().config.table).toBe("t");
    expect(getState().role).toBe("reviewer");
    expect(getState().fields).toHaveLength(1);
    expect(calls).toBe(1);
  });

  it("setFieldReview upserts one entry per key and mirrors fieldState", () => {
    initStore({});
    setFieldReview("a", "general", { state: "ok" });
    expect(getState().review.reviews).toHaveLength(1);
    expect(getState().fieldState.a).toBe("ok");

    setFieldReview("a", "general", { state: "rejected" });
    expect(getState().review.reviews).toHaveLength(1);
    expect(getState().fieldState.a).toBe("rejected");
  });

  it("selectField sets the selection and clears the draft state", () => {
    initStore({});
    setDraftState("suggestion");
    selectField({ fieldKey: "a", fieldValue: "v", category: "general" });
    expect(getState().selection.fieldKey).toBe("a");
    expect(getState().selection.category).toBe("general");
    expect(getState().selection.draftState).toBeNull();
  });

  it("setFinished records reviewFinished and the badge", () => {
    initStore({});
    setFinished(true, "gold");
    expect(getState().review.reviewFinished).toBe(true);
    expect(getState().review.grantedBadge).toBe("gold");
  });

  it("unsubscribe stops notifications", () => {
    let calls = 0;
    const off = subscribe(() => (calls += 1));
    off();
    initStore({});
    expect(calls).toBe(0);
  });
});
