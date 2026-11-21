// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// A show/hide button beside every password field of the account pages (log
// in, sign up, set, reset and change password). The server renders plain
// password inputs; bound, each one moves into an input group with a button
// that switches the field between hidden and readable. A field's error
// messages move into the group with it, because Bootstrap shows an
// `.invalid-feedback` only as a sibling of the invalid input.

const SHOW = "Show password";
const HIDE = "Hide password";

function reveal(input, button, shown) {
  input.type = shown ? "text" : "password";
  button.setAttribute("aria-pressed", String(shown));
  button.setAttribute("aria-label", shown ? HIDE : SHOW);
  button.title = shown ? HIDE : SHOW;
  button.querySelector("i").className = shown ? "fas fa-eye-slash" : "fas fa-eye";
}

/** Give every password input under `root` a show/hide button. */
export function bindPasswordReveal(root) {
  for (const input of root.querySelectorAll('input[type="password"]')) {
    const doc = input.ownerDocument;
    const group = doc.createElement("div");
    group.className = "input-group has-validation";
    const feedback = [...input.parentElement.children].filter(
      (el) => el.classList.contains("invalid-feedback"),
    );
    input.before(group);
    input.classList.add("form-control");

    const button = doc.createElement("button");
    button.type = "button";
    button.className = "btn btn-secondary";
    button.setAttribute("aria-controls", input.id);
    button.append(doc.createElement("i"));
    button.querySelector("i").setAttribute("aria-hidden", "true");
    reveal(input, button, false);
    button.addEventListener("click", () =>
      reveal(input, button, input.type === "password"),
    );

    group.append(input, button, ...feedback);
    // Hide it again on submit, so no browser keeps the password as form history.
    input.form?.addEventListener("submit", () => reveal(input, button, false));
  }
}
