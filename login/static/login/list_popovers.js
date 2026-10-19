// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// Popovers in a dashboard list's cells: the Publish gate's reasons, the
// Datasets a Table is in, the Topics behind "+n". Nothing here knows about
// Tables, so another tab's list can use it as it is.
//
// The server renders both halves in the cell: a button carrying
// `data-dash-popover` and `aria-controls`, and the panel it names, `hidden`.
// What is left for the browser:
//
// - opening one closes any other;
// - an open panel takes focus (its first link or button, else the panel
//   itself), so the links inside are reachable by keyboard;
// - Escape closes it and gives focus back to its button;
// - a click outside, or focus moving elsewhere, closes it.
//
// The panel is placed with `position: fixed` beside its button, because the
// list scrolls sideways inside an `overflow` wrapper that would clip it.
// When htmx swaps the region an open panel goes with it; that is a close.

export const TRIGGER = "data-dash-popover";
const FOCUSABLE = "a[href], button:not([disabled]), input, select, textarea";

/**
 * The panel a trigger controls.
 *
 * @param {Element} trigger a `[data-dash-popover]` button.
 * @return {HTMLElement|null} the panel, or null.
 */
export function panelOf(trigger) {
  const id = trigger.getAttribute("aria-controls");
  return id ? trigger.ownerDocument.getElementById(id) : null;
}

/**
 * Place `panel` just below `trigger`, kept inside the viewport.
 *
 * @param {Element} trigger the button.
 * @param {HTMLElement} panel the panel.
 */
export function place(trigger, panel) {
  const view = trigger.ownerDocument.defaultView;
  const box = trigger.getBoundingClientRect();
  const width = panel.offsetWidth || 0;
  const left = Math.max(8, Math.min(box.left, view.innerWidth - width - 8));
  panel.style.position = "fixed";
  panel.style.top = `${box.bottom + 4}px`;
  panel.style.left = `${left}px`;
}

/**
 * Wire every list popover on `doc`.
 *
 * @param {Document} doc the document.
 * @return {{open: function(Element): void, close: function(boolean): void,
 *   current: function(): Element|null, unbind: function(): void}}
 */
export function bindPopovers(doc) {
  let trigger = null;

  const current = () => {
    if (trigger && !trigger.isConnected) {
      trigger = null;
    }
    return trigger;
  };

  const close = (returnFocus = false) => {
    const open = current();
    if (!open) {
      return;
    }
    const panel = panelOf(open);
    if (panel) {
      panel.hidden = true;
    }
    open.setAttribute("aria-expanded", "false");
    trigger = null;
    if (returnFocus) {
      open.focus();
    }
  };

  const open = (next) => {
    const panel = panelOf(next);
    if (!panel) {
      return;
    }
    close();
    panel.hidden = false;
    next.setAttribute("aria-expanded", "true");
    place(next, panel);
    trigger = next;
    (panel.querySelector(FOCUSABLE) || panel).focus();
  };

  const within = (node) => {
    const open = current();
    if (!open || !node) {
      return false;
    }
    const panel = panelOf(open);
    return open.contains(node) || (panel !== null && panel.contains(node));
  };

  const onClick = (event) => {
    const clicked = event.target.closest && event.target.closest(`[${TRIGGER}]`);
    if (clicked) {
      if (clicked === current()) {
        close(true);
      } else {
        open(clicked);
      }
      return;
    }
    if (!within(event.target)) {
      close();
    }
  };

  const onKeydown = (event) => {
    if (event.key === "Escape" && current()) {
      event.preventDefault();
      close(true);
    }
  };

  const onFocusin = (event) => {
    if (current() && !within(event.target)) {
      close();
    }
  };

  const listeners = [
    ["click", onClick],
    ["keydown", onKeydown],
    ["focusin", onFocusin],
  ];
  for (const [name, listener] of listeners) {
    doc.addEventListener(name, listener);
  }
  return {
    open,
    close,
    current,
    unbind() {
      for (const [name, listener] of listeners) {
        doc.removeEventListener(name, listener);
      }
    },
  };
}
