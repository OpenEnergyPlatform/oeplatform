// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later
import { describe, expect, it } from "vitest";

import {
  contributorTargets,
  isReviewerComplete,
  nonEmptyFields,
  reviewProgress,
  reviewerHasChanges,
} from "./selectors.js";

const stateWith = (fields, fieldState) => ({ fields, fieldState });

describe("selectors", () => {
  it("nonEmptyFields drops empty fields", () => {
    const s = stateWith(
      [
        { key: "a", isEmpty: false },
        { key: "b", isEmpty: true },
      ],
      {}
    );
    expect(nonEmptyFields(s).map((f) => f.key)).toEqual(["a"]);
  });

  it("reviewProgress counts accepted over non-empty fields", () => {
    const s = stateWith(
      [
        { key: "a", isEmpty: false },
        { key: "b", isEmpty: false },
        { key: "c", isEmpty: true },
      ],
      { a: "ok", b: "suggestion" }
    );
    expect(reviewProgress(s)).toEqual({ total: 2, accepted: 1, percent: 50 });
  });

  it("isReviewerComplete requires every non-empty field reviewed", () => {
    expect(
      isReviewerComplete(stateWith([{ key: "a", isEmpty: false }], { a: "ok" }))
    ).toBe(true);
    expect(
      isReviewerComplete(
        stateWith(
          [
            { key: "a", isEmpty: false },
            { key: "b", isEmpty: false },
          ],
          { a: "ok" }
        )
      )
    ).toBe(false);
  });

  it("reviewerHasChanges detects suggestion/rejected", () => {
    expect(
      reviewerHasChanges(stateWith([{ key: "a", isEmpty: false }], { a: "ok" }))
    ).toBe(false);
    expect(
      reviewerHasChanges(stateWith([{ key: "a", isEmpty: false }], { a: "rejected" }))
    ).toBe(true);
  });

  it("contributorTargets are only the reviewer-flagged fields", () => {
    const s = stateWith(
      [
        { key: "a", isEmpty: false },
        { key: "b", isEmpty: false },
        { key: "c", isEmpty: false },
      ],
      { a: "ok", b: "suggestion", c: "rejected" }
    );
    expect(contributorTargets(s).map((f) => f.key)).toEqual(["b", "c"]);
  });
});