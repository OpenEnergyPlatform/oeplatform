// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later
import { describe, expect, it } from "vitest";

import { reviewPayload } from "./api.js";

describe("api.reviewPayload", () => {
  const review = { reviews: [{ key: "title" }] };

  it("wraps the review datamodel with the action type", () => {
    expect(reviewPayload("save", review)).toEqual({
      reviewType: "save",
      reviewData: review,
    });
  });

  it("merges extra fields (badge, review_id)", () => {
    expect(reviewPayload("finished", review, { reviewBadge: "gold" })).toEqual({
      reviewType: "finished",
      reviewData: review,
      reviewBadge: "gold",
    });
    expect(reviewPayload("delete", review, { review_id: 7 })).toEqual({
      reviewType: "delete",
      reviewData: review,
      review_id: 7,
    });
  });
});