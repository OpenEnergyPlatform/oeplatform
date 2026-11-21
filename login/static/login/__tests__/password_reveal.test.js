// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// @vitest-environment happy-dom
import { beforeEach, describe, expect, it } from "vitest";

import { bindPasswordReveal } from "../password_reveal.js";

describe("bindPasswordReveal", () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <form class="login"><div class="mb-3">
        <label for="pw">Password</label>
        <input id="pw" name="pw" type="password" class="form-control is-invalid" />
        <div class="invalid-feedback">Too short.</div>
      </div><input id="user" type="text" /></form>`;
    bindPasswordReveal(document.querySelector(".login"));
  });

  it("toggles the field between hidden and readable", () => {
    const input = document.getElementById("pw");
    const button = input.parentElement.querySelector("button");
    expect(button.getAttribute("aria-label")).toBe("Show password");
    button.click();
    expect(input.type).toBe("text");
    expect(button.getAttribute("aria-pressed")).toBe("true");
    button.click();
    expect(input.type).toBe("password");
  });

  it("keeps the error beside the input and leaves other fields alone", () => {
    const group = document.getElementById("pw").parentElement;
    expect(group.classList.contains("input-group")).toBe(true);
    expect(group.querySelector(".invalid-feedback")).not.toBeNull();
    expect(document.querySelectorAll("button")).toHaveLength(1);
  });

  it("hides the password again on submit", () => {
    const input = document.getElementById("pw");
    input.parentElement.querySelector("button").click();
    input.form.dispatchEvent(new Event("submit"));
    expect(input.type).toBe("password");
  });
});
