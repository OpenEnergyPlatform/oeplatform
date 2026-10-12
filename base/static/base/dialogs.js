// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// The confirm dialog and the toasts (#2643): every confirmation on the
// platform asks through one dialog, and every error a script reports goes to
// one toast region, instead of the browser's `confirm()` and `alert()`.
// Every shell renders both (base/_feedback.html) and binds this module once.
//
// A template asks for a confirmation without any script of its own:
//
// - `hx-confirm="<what will happen>"` on an htmx element: the request is
//   sent only on confirm;
// - `data-confirm="<what will happen>"` on a plain button or link: its click
//   goes through only on confirm.
//
// Either may add `data-confirm-title` (names the action: "Delete table?"),
// `data-confirm-verb` (the button's label: "Delete table"; never "OK"),
// `data-confirm-danger` (it cannot be undone: a solid red button, focus on
// Cancel) and `data-confirm-typed="<text>"` (the user types it first).
//
// A script calls `window.oep.confirm({title, text, verb, danger, typed})`,
// which resolves true or false, and `window.oep.toast(text, {status,
// title})`. Module code may import the same two functions.

const DIALOG = "confirm-dialog";
const TOAST_TEMPLATE = "toast-template";
const STATUSES = ["success", "info", "warning", "danger"];
const TOAST_TIMEOUT = 6000;

/**
 * Bootstrap's modal around the dialog element. It is looked up when used,
 * because the shell loads Bootstrap as a classic script.
 */
function bootstrapModal(element) {
  const modal = () =>
    element.ownerDocument.defaultView.bootstrap.Modal.getOrCreateInstance(
      element
    );
  return { show: () => modal().show(), hide: () => modal().hide() };
}

/**
 * Ask in the shell's confirm dialog.
 *
 * @param {object} options `title`, `text`, `verb` (default "Confirm"),
 *     `danger`, `typed`; `doc` and `modal` (Bootstrap's by default) are test
 *     seams.
 * @return {Promise<boolean>} true on confirm; false on Cancel, the close
 *     button, Escape or the backdrop, and without a dialog on the page.
 */
export function confirmAction({
  title = "",
  text = "",
  verb = "Confirm",
  danger = false,
  typed = "",
  doc = document,
  modal = null,
} = {}) {
  const element = doc.getElementById(DIALOG);
  if (!element) {
    return Promise.resolve(false);
  }
  modal = modal || bootstrapModal(element);
  // A confirmation still open is answered "no" before the next one asks.
  if (element.oepSettle) {
    element.oepSettle(false);
  }
  const part = (name) => element.querySelector(`[data-confirm-${name}]`);
  const accept = part("accept");
  const cancel = element.querySelector(".modal-footer [data-confirm-cancel]");
  const input = part("input");

  part("title").textContent = title || `${verb}?`;
  part("text").textContent = text;
  accept.textContent = verb;
  accept.classList.toggle("btn-danger", danger);
  accept.classList.toggle("btn-primary", !danger);
  part("typed").hidden = !typed;
  part("expected").textContent = typed;
  input.value = "";
  accept.disabled = Boolean(typed);

  const opener = doc.activeElement;
  const listening = new AbortController();
  const on = (target, type, handler) =>
    target.addEventListener(type, handler, { signal: listening.signal });

  return new Promise((resolve) => {
    const settle = (answer) => {
      listening.abort();
      element.oepSettle = null;
      modal.hide();
      if (opener && opener !== doc.body && opener.isConnected) {
        opener.focus();
      }
      resolve(answer);
    };
    element.oepSettle = settle;

    on(accept, "click", () => !accept.disabled && settle(true));
    for (const button of element.querySelectorAll("[data-confirm-cancel]")) {
      on(button, "click", () => settle(false));
    }
    on(element, "keydown", (event) => {
      if (event.key === "Escape") {
        settle(false);
      } else if (event.key === "Enter" && event.target === input) {
        event.preventDefault();
        if (!accept.disabled) {
          settle(true);
        }
      }
    });
    on(input, "input", () => {
      accept.disabled = input.value !== typed;
    });
    // Bootstrap closing the dialog by itself (the backdrop) is a "no" too.
    on(element, "hidden.bs.modal", () => settle(false));

    // Focus: in the input for a typed confirmation, on Cancel for a
    // destructive one, otherwise on the confirm button. Bootstrap focuses
    // the dialog itself once shown, so this runs again then.
    const focus = () => (typed ? input : danger ? cancel : accept).focus();
    on(element, "shown.bs.modal", focus);
    modal.show();
    focus();
  });
}

/**
 * Add a toast to the shell's region. A success or an info removes itself
 * after a while; a warning or an error is announced at once and stays until
 * its close button is pressed.
 *
 * @param {string} text the message, written as text.
 * @param {object} options `status` (success, info, warning, danger; default
 *     info), `title`; `doc`, `timeout` and `schedule` are test seams.
 * @return {Element|null} the toast, or null without a toast region.
 */
export function showToast(
  text,
  {
    status = "info",
    title = "",
    doc = document,
    timeout = TOAST_TIMEOUT,
    schedule = setTimeout,
  } = {}
) {
  const lasting = status === "danger" || status === "warning";
  const region = doc.getElementById(
    lasting ? "toasts-assertive" : "toasts-polite"
  );
  const template = doc.getElementById(TOAST_TEMPLATE);
  if (!region || !template) {
    return null;
  }
  const toast = template.content.firstElementChild.cloneNode(true);
  toast.classList.remove(...STATUSES.map((name) => `toast--${name}`));
  toast.classList.add(`toast--${status}`);
  toast.querySelector(".toast__text").textContent = text;
  const heading = toast.querySelector(".toast__title");
  heading.textContent = title;
  heading.hidden = !title;
  toast
    .querySelector("[data-toast-close]")
    .addEventListener("click", () => toast.remove());
  region.append(toast);
  if (!lasting) {
    schedule(() => toast.remove(), timeout);
  }
  return toast;
}

/** What an element's `data-confirm-*` attributes ask for. */
function optionsFrom(element, text, doc, modal) {
  const data = element.dataset;
  return {
    title: data.confirmTitle,
    text,
    verb: data.confirmVerb || undefined,
    danger: "confirmDanger" in data,
    typed: data.confirmTyped || "",
    doc,
    modal,
  };
}

/**
 * Route every `hx-confirm` and `data-confirm` on the page through the
 * dialog, and offer both functions to classic scripts as `window.oep`.
 *
 * @param {Document} doc the document.
 * @param {object} options `modal`, a test seam.
 * @return {Function} unbinds both listeners again (for tests).
 */
export function bindDialogs(doc, { modal = null } = {}) {
  const bound = new AbortController();
  const view = doc.defaultView;
  view.oep = Object.assign(view.oep || {}, {
    confirm: (options = {}) => confirmAction({ doc, modal, ...options }),
    toast: (text, options = {}) => showToast(text, { doc, ...options }),
  });

  // htmx asks before every request it sends; one that carries a question
  // (`hx-confirm`) waits for the dialog. issueRequest(true) skips htmx's own
  // confirm(), which would otherwise ask a second time.
  doc.addEventListener(
    "htmx:confirm",
    (event) => {
      const { question, elt, issueRequest } = event.detail;
      if (!question) {
        return;
      }
      event.preventDefault();
      const source = elt.closest("[hx-confirm]") || elt;
      confirmAction(optionsFrom(source, question, doc, modal)).then(
        (confirmed) => confirmed && issueRequest(true)
      );
    },
    { signal: bound.signal }
  );

  // A plain button or link: its click is held back, and clicked again on
  // confirm, so whatever it does (submit its form, follow its link, a
  // script's handler) happens only then. Captured on the document, so no
  // handler on the button sees the first click.
  const confirmed = new WeakSet();
  doc.addEventListener(
    "click",
    (event) => {
      const opener = event.target.closest("[data-confirm]");
      if (!opener) {
        return;
      }
      if (confirmed.has(opener)) {
        confirmed.delete(opener);
        return;
      }
      event.preventDefault();
      event.stopImmediatePropagation();
      confirmAction(
        optionsFrom(opener, opener.dataset.confirm, doc, modal)
      ).then((answer) => {
        if (answer) {
          confirmed.add(opener);
          opener.click();
        }
      });
    },
    { capture: true, signal: bound.signal }
  );
  return () => bound.abort();
}
