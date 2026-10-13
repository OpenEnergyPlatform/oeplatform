// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// @vitest-environment happy-dom
//
// The edit-in-place card (#2654): focus follows the swap, and only a save
// shows the toast.
import { afterEach, describe, expect, it, vi } from "vitest";

import { bindEditInPlace } from "../edit_in_place.js";

const READING = `
  <h2>Manage Profile</h2>
  <a href="/edit" class="btn btn-primary" data-edit-in-place-trigger>Edit</a>`;
const EDITING = `
  <h2>Manage Profile</h2>
  <form>
    <input type="hidden" name="csrfmiddlewaretoken" value="x">
    <input type="file" name="profile_img" id="img">
    <input type="text" name="fullname" id="name" class="form-control INVALID">
    <a href="/settings" class="btn btn-secondary">Cancel</a>
    <button type="submit">Submit</button>
  </form>`;

let unbind = () => {};

afterEach(() => {
  unbind();
  document.body.innerHTML = "";
});

/** Swap the card's body as htmx would, and fire its afterSettle. */
function swap(body, verb, { invalid = false } = {}) {
  document.body.innerHTML = `
    <div id="profile-card" data-edit-in-place
         data-edit-in-place-saved="Profile saved.">
      ${body.replace("INVALID", invalid ? "is-invalid" : "")}
    </div>`;
  const card = document.getElementById("profile-card");
  card.dispatchEvent(
    new CustomEvent("htmx:afterSettle", {
      bubbles: true,
      detail: { requestConfig: { verb } },
    })
  );
}

function bound() {
  const toast = vi.fn();
  unbind = bindEditInPlace(document, { toast });
  return toast;
}

describe("the edit-in-place card", () => {
  it("moves the focus into the form when it opens", () => {
    const toast = bound();
    swap(EDITING, "get");
    expect(document.activeElement.id).toBe("img");
    expect(toast).not.toHaveBeenCalled();
  });

  it("moves the focus to the first invalid field after a refused save", () => {
    const toast = bound();
    swap(EDITING, "post", { invalid: true });
    expect(document.activeElement.id).toBe("name");
    expect(toast).not.toHaveBeenCalled();
  });

  it("returns the focus to Edit after Cancel, without a toast", () => {
    const toast = bound();
    swap(READING, "get");
    expect(document.activeElement.textContent).toBe("Edit");
    expect(toast).not.toHaveBeenCalled();
  });

  it("returns the focus to Edit after a save and says so", () => {
    const toast = bound();
    swap(READING, "post");
    expect(document.activeElement.textContent).toBe("Edit");
    expect(toast).toHaveBeenCalledWith("Profile saved.", { status: "success" });
  });

  it("leaves a swap outside a card alone", () => {
    const toast = bound();
    document.body.innerHTML = `<button id="b">B</button><div id="other"></div>`;
    document.getElementById("b").focus();
    document.getElementById("other").dispatchEvent(
      new CustomEvent("htmx:afterSettle", {
        bubbles: true,
        detail: { requestConfig: { verb: "post" } },
      })
    );
    expect(document.activeElement.id).toBe("b");
    expect(toast).not.toHaveBeenCalled();
  });

  it("stops when unbound", () => {
    const toast = bound();
    unbind();
    swap(READING, "post");
    expect(toast).not.toHaveBeenCalled();
  });
});
