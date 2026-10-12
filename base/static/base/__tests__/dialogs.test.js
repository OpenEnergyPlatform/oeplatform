// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// @vitest-environment happy-dom
//
// The confirm dialog and the toasts (#2643). Bootstrap's modal is replaced by
// a stand-in that shows and hides the element and sends Bootstrap's two
// events, so these tests prove what the module does around it: what the
// dialog says, which answer each way out gives, where focus goes, and that
// an htmx request or a plain button's action runs only on confirm.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { bindDialogs, confirmAction, showToast } from "../dialogs.js";

// The shell's piece, as base/_feedback.html renders it.
function renderShell(content = "") {
  document.body.innerHTML = `
    ${content}
    <div id="confirm-dialog" class="modal confirm-dialog fade" tabindex="-1"
         aria-hidden="true" data-confirm-dialog>
      <div class="modal-dialog"><div class="modal-content">
        <div class="modal-header">
          <h2 class="modal-title" id="confirm-dialog-title" data-confirm-title></h2>
          <button type="button" class="btn-close" aria-label="Cancel"
                  data-confirm-cancel></button>
        </div>
        <div class="modal-body">
          <p id="confirm-dialog-text" data-confirm-text></p>
          <div data-confirm-typed hidden>
            <label for="confirm-dialog-input">Type
              <strong data-confirm-expected></strong> to confirm</label>
            <input id="confirm-dialog-input" type="text" data-confirm-input />
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary"
                  data-confirm-cancel>Cancel</button>
          <button type="button" class="btn btn-primary"
                  data-confirm-accept>Confirm</button>
        </div>
      </div></div>
    </div>
    <div class="toast-region">
      <div id="toasts-polite" role="status" aria-live="polite"></div>
      <div id="toasts-assertive" role="alert" aria-live="assertive"></div>
    </div>
    <template id="toast-template">
      <div class="toast show toast--info">
        <div class="d-flex">
          <div class="toast-body">
            <strong class="toast__title" hidden></strong>
            <span class="toast__text"></span>
          </div>
          <button type="button" class="btn-close" aria-label="Close"
                  data-toast-close></button>
        </div>
      </div>
    </template>`;
}

// Bootstrap's modal, as far as the module uses it.
function fakeModal() {
  const element = document.getElementById("confirm-dialog");
  return {
    show() {
      element.classList.add("show");
      element.dispatchEvent(new Event("shown.bs.modal"));
    },
    hide() {
      if (!element.classList.contains("show")) return;
      element.classList.remove("show");
      element.dispatchEvent(new Event("hidden.bs.modal"));
    },
  };
}

const dialog = () => document.getElementById("confirm-dialog");
const accept = () => dialog().querySelector("[data-confirm-accept]");
const cancel = () =>
  dialog().querySelector(".modal-footer [data-confirm-cancel]");
const closeButton = () => dialog().querySelector(".btn-close");
const input = () => dialog().querySelector("[data-confirm-input]");

function ask(options = {}) {
  return confirmAction({ modal: fakeModal(), ...options });
}

function pressEscape() {
  dialog().dispatchEvent(
    new KeyboardEvent("keydown", { key: "Escape", bubbles: true })
  );
}

let unbind = () => {};

afterEach(() => {
  unbind();
  document.body.innerHTML = "";
  delete window.oep;
});

describe("confirmAction", () => {
  beforeEach(() => renderShell('<button id="opener">Delete</button>'));

  it("says what is confirmed, with the verb on the button", () => {
    ask({
      title: "Delete table?",
      text: "The table and its data are deleted.",
      verb: "Delete table",
    });

    expect(dialog().classList.contains("show")).toBe(true);
    expect(dialog().querySelector("[data-confirm-title]").textContent).toBe(
      "Delete table?"
    );
    expect(dialog().querySelector("[data-confirm-text]").textContent).toBe(
      "The table and its data are deleted."
    );
    expect(accept().textContent).toBe("Delete table");
  });

  it("writes text, never markup", () => {
    ask({ title: "<img src=x>", text: "<b>bold</b>" });

    expect(dialog().querySelector("img, b")).toBeNull();
  });

  it("resolves true on confirm, and closes", async () => {
    const answer = ask({ verb: "Delete" });
    accept().click();

    expect(await answer).toBe(true);
    expect(dialog().classList.contains("show")).toBe(false);
  });

  it.each([
    ["Cancel", () => cancel().click()],
    ["the close button", () => closeButton().click()],
    ["Escape", pressEscape],
    [
      "Bootstrap closing it (a click on the backdrop)",
      () => fakeModal().hide(),
    ],
  ])("resolves false on %s", async (_, wayOut) => {
    const answer = ask();
    wayOut();

    expect(await answer).toBe(false);
    expect(dialog().classList.contains("show")).toBe(false);
  });

  it("answers once, however many ways out are taken", async () => {
    const answer = ask();
    accept().click();
    cancel().click();

    expect(await answer).toBe(true);
  });

  it("is solid danger for an irreversible action, with focus on Cancel", () => {
    ask({ danger: true });

    expect(accept().classList.contains("btn-danger")).toBe(true);
    expect(accept().classList.contains("btn-primary")).toBe(false);
    expect(document.activeElement).toBe(cancel());
  });

  it("is primary otherwise, with focus on the confirm button", () => {
    ask({ danger: true });
    cancel().click();
    ask();

    expect(accept().classList.contains("btn-primary")).toBe(true);
    expect(accept().classList.contains("btn-danger")).toBe(false);
    expect(document.activeElement).toBe(accept());
  });

  it("gives focus back to the opener", async () => {
    const opener = document.getElementById("opener");
    opener.focus();
    const answer = ask({ danger: true });
    pressEscape();
    await answer;

    expect(document.activeElement).toBe(opener);
  });

  describe("typed", () => {
    it("starts in the input and keeps the button disabled until the text matches", async () => {
      const answer = ask({ typed: "wind_farms", danger: true });

      expect(dialog().querySelector("[data-confirm-typed]").hidden).toBe(false);
      expect(
        dialog().querySelector("[data-confirm-expected]").textContent
      ).toBe("wind_farms");
      expect(document.activeElement).toBe(input());
      expect(accept().disabled).toBe(true);

      for (const value of ["wind", "Wind_farms", "wind_farms "]) {
        input().value = value;
        input().dispatchEvent(new Event("input", { bubbles: true }));
        expect(accept().disabled).toBe(true);
      }
      accept().click();
      input().value = "wind_farms";
      input().dispatchEvent(new Event("input", { bubbles: true }));
      expect(accept().disabled).toBe(false);
      accept().click();

      expect(await answer).toBe(true);
    });

    it("starts empty the next time, and an untyped one has no input", () => {
      ask({ typed: "a" });
      input().value = "a";
      cancel().click();
      ask();

      expect(input().value).toBe("");
      expect(dialog().querySelector("[data-confirm-typed]").hidden).toBe(true);
      expect(accept().disabled).toBe(false);
    });
  });

  it("answers false for the first when a second confirmation opens", async () => {
    const first = ask();
    const second = ask();
    accept().click();

    expect(await first).toBe(false);
    expect(await second).toBe(true);
  });

  describe("while Bootstrap fades the dialog in or out", () => {
    // Bootstrap's modal ignores show() and hide() during its fade, and sends
    // its event only when the fade ends (`finish`).
    function fadingModal() {
      const element = dialog();
      let fading = null;
      return {
        show() {
          if (fading || element.classList.contains("show")) return;
          fading = "shown";
          element.classList.add("show");
        },
        hide() {
          if (fading || !element.classList.contains("show")) return;
          fading = "hidden";
          element.classList.remove("show");
        },
        finish() {
          const event = fading;
          fading = null;
          element.dispatchEvent(new Event(`${event}.bs.modal`));
        },
        get fading() {
          return fading;
        },
      };
    }

    it("closes once open when answered while still opening", async () => {
      const modal = fadingModal();
      const answer = ask({ modal });
      pressEscape();
      expect(await answer).toBe(false);

      modal.finish(); // shown: now it can close
      expect(modal.fading).toBe("hidden");
      modal.finish();
      expect(dialog().classList.contains("show")).toBe(false);
    });

    it("waits for one answered while it still fades in before opening the next", async () => {
      const modal = fadingModal();
      const first = ask({ modal });
      cancel().click(); // answered mid fade-in
      const second = ask({ modal, title: "Second?" });
      expect(await first).toBe(false);

      modal.finish(); // the first is shown, and starts to close
      expect(modal.fading).toBe("hidden");
      modal.finish(); // closed: the second opens
      expect(modal.fading).toBe("shown");
      modal.finish();
      expect(dialog().querySelector("[data-confirm-title]").textContent).toBe(
        "Second?"
      );
      accept().click();
      expect(await second).toBe(true);
    });

    it("opens the next once the last has closed, and the last's close does not answer it", async () => {
      const modal = fadingModal();
      const first = ask({ modal });
      modal.finish();
      cancel().click(); // fading out
      const second = ask({ modal, title: "Second?" });
      expect(await first).toBe(false);

      modal.finish(); // hidden: the second opens now
      expect(modal.fading).toBe("shown");
      modal.finish();
      expect(dialog().classList.contains("show")).toBe(true);
      accept().click();
      expect(await second).toBe(true);
    });
  });

  it("answers false without a dialog on the page", async () => {
    document.body.innerHTML = "";

    expect(await confirmAction({ modal: { show() {}, hide() {} } })).toBe(
      false
    );
  });
});

describe("bindDialogs", () => {
  function htmxConfirm(element, question) {
    const issueRequest = vi.fn();
    const event = new CustomEvent("htmx:confirm", {
      bubbles: true,
      cancelable: true,
      detail: { elt: element, question, issueRequest },
    });
    element.dispatchEvent(event);
    return { event, issueRequest };
  }

  beforeEach(() => {
    renderShell(`
      <form id="remove" hx-post="/remove" hx-confirm="Remove Ada from the team?"
            data-confirm-title="Remove member?" data-confirm-verb="Remove"
            data-confirm-danger>
        <button id="remove-button" class="btn btn-outline-danger">Remove</button>
      </form>
      <a id="refresh" hx-get="/refresh">Refresh</a>
      <button id="plain" data-confirm="The tag goes from 3 objects."
              data-confirm-title="Delete tag?" data-confirm-verb="Delete tag"
              data-confirm-danger data-confirm-typed="wind">Delete</button>`);
    unbind = bindDialogs(document, { modal: fakeModal() });
  });

  it("routes an hx-confirm through the dialog and issues the request on confirm", async () => {
    const { event, issueRequest } = htmxConfirm(
      document.getElementById("remove-button"),
      "Remove Ada from the team?"
    );

    expect(event.defaultPrevented).toBe(true);
    expect(dialog().classList.contains("show")).toBe(true);
    expect(dialog().querySelector("[data-confirm-title]").textContent).toBe(
      "Remove member?"
    );
    expect(dialog().querySelector("[data-confirm-text]").textContent).toBe(
      "Remove Ada from the team?"
    );
    expect(accept().textContent).toBe("Remove");
    expect(accept().classList.contains("btn-danger")).toBe(true);
    expect(issueRequest).not.toHaveBeenCalled();

    accept().click();
    await vi.waitFor(() => expect(issueRequest).toHaveBeenCalledTimes(1));
    // true: skip htmx's own confirm(), which would ask a second time
    expect(issueRequest).toHaveBeenCalledWith(true);
  });

  it("issues no request when the hx-confirm is cancelled", async () => {
    const { issueRequest } = htmxConfirm(
      document.getElementById("remove-button"),
      "Remove Ada from the team?"
    );
    cancel().click();
    await Promise.resolve();

    expect(issueRequest).not.toHaveBeenCalled();
  });

  it("leaves a request without hx-confirm alone", () => {
    const { event } = htmxConfirm(document.getElementById("refresh"), null);

    expect(event.defaultPrevented).toBe(false);
    expect(dialog().classList.contains("show")).toBe(false);
  });

  it("opens the dialog for a data-confirm button and acts only on confirm", async () => {
    const plain = document.getElementById("plain");
    const action = vi.fn();
    plain.addEventListener("click", action);

    plain.click();
    expect(action).not.toHaveBeenCalled();
    expect(dialog().querySelector("[data-confirm-text]").textContent).toBe(
      "The tag goes from 3 objects."
    );
    expect(document.activeElement).toBe(input());

    input().value = "wind";
    input().dispatchEvent(new Event("input", { bubbles: true }));
    accept().click();
    await vi.waitFor(() => expect(action).toHaveBeenCalledTimes(1));

    // the next click asks again
    plain.click();
    expect(action).toHaveBeenCalledTimes(1);
    expect(dialog().classList.contains("show")).toBe(true);
  });

  it("does not act on a cancelled data-confirm button", async () => {
    const plain = document.getElementById("plain");
    const action = vi.fn();
    plain.addEventListener("click", action);

    plain.click();
    cancel().click();
    await Promise.resolve();

    expect(action).not.toHaveBeenCalled();
  });

  it("offers both to classic scripts as window.oep", () => {
    expect(typeof window.oep.confirm).toBe("function");
    expect(typeof window.oep.toast).toBe("function");
  });
});

describe("showToast", () => {
  beforeEach(() => renderShell());

  it("adds one toast to the polite region", () => {
    const toast = showToast("Saved.", { status: "success", title: "Profile" });

    const region = document.getElementById("toasts-polite");
    expect(region.querySelectorAll(".toast")).toHaveLength(1);
    expect(region.contains(toast)).toBe(true);
    expect(toast.classList.contains("toast--success")).toBe(true);
    expect(toast.classList.contains("toast--info")).toBe(false);
    expect(toast.querySelector(".toast__text").textContent).toBe("Saved.");
    expect(toast.querySelector(".toast__title").textContent).toBe("Profile");
    expect(toast.querySelector(".toast__title").hidden).toBe(false);
    expect(document.getElementById("toasts-assertive").children).toHaveLength(
      0
    );
  });

  it("puts an error in the assertive region, as text", () => {
    const toast = showToast("<img src=x>", { status: "danger" });

    expect(document.getElementById("toasts-assertive").contains(toast)).toBe(
      true
    );
    expect(toast.querySelector("img")).toBeNull();
    expect(toast.querySelector(".toast__title").hidden).toBe(true);
  });

  it("removes a success by itself, but keeps an error until it is closed", () => {
    const timers = [];
    const schedule = (callback) => timers.push(callback);

    const ok = showToast("Saved.", { status: "success", schedule });
    const error = showToast("Failed.", { status: "danger", schedule });
    expect(timers).toHaveLength(1);
    timers[0]();

    expect(ok.isConnected).toBe(false);
    expect(error.isConnected).toBe(true);
    error.querySelector("[data-toast-close]").click();
    expect(error.isConnected).toBe(false);
  });

  it("answers null without a toast region", () => {
    document.body.innerHTML = "";

    expect(showToast("Saved.")).toBeNull();
  });
});
