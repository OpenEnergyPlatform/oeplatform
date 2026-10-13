// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// The edit-in-place card (#2654): one card, two states, swapped by htmx so
// the address never changes. The card's root carries `data-edit-in-place`
// and the htmx target, select and swap its Edit button, form and Cancel
// inherit; reading, it holds the Edit button (`data-edit-in-place-trigger`),
// editing, the form. The edit view answers an htmx GET and an invalid save
// with the card alone and a valid save with a redirect to the reading page,
// whose card the request selects. Without JavaScript the same card is a page
// of its own (login/partials/profile_card.html is the first one).
//
// Bound, this moves the focus with the swap: into the form when it opens (to
// the first invalid field after a refused save), back to Edit after a save
// or Cancel. A save also says so in a toast, `data-edit-in-place-saved`.

const FIELD = "input:not([type=hidden]), select, textarea";

/** Focus the card that htmx has just swapped in; `verb` is the request's. */
function settle(card, verb, toast) {
  const form = card.querySelector("form");
  if (form) {
    (form.querySelector(".is-invalid") ?? form.querySelector(FIELD))?.focus();
    return;
  }
  card.querySelector("[data-edit-in-place-trigger]")?.focus();
  if (verb === "post" && card.dataset.editInPlaceSaved) {
    toast(card.dataset.editInPlaceSaved, { status: "success" });
  }
}

/**
 * Follow every edit-in-place card of `doc` through its swaps.
 *
 * @param {Document} doc the page.
 * @param {object} options `toast(text, options)`, by default the shell's
 *     `window.oep.toast` (base/static/base/dialogs.js).
 * @return {Function} unbinds.
 */
export function bindEditInPlace(
  doc,
  { toast = (text, options) => window.oep?.toast(text, options) } = {}
) {
  const onSettle = (event) => {
    const card = event.target.closest?.("[data-edit-in-place]");
    if (card) settle(card, event.detail?.requestConfig?.verb, toast);
  };
  doc.addEventListener("htmx:afterSettle", onSettle);
  return () => doc.removeEventListener("htmx:afterSettle", onSettle);
}
