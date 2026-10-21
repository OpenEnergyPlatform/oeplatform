// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// The language switch of a text that a page carries in two languages, the
// terms of use (#2650). The server renders both languages one after the
// other, each a `<section id="<language>" data-language="<language>">` that
// opens with its own heading, and the switch hidden: without this module a
// reader gets every word, and an address ending in `#de` scrolls to the
// German one.
//
// Bound, it only hides: it reveals the switch (radios named `language`, one
// per section, the first one the default), shows one language at a time
// together with every other `[data-language]` part of the page (the "On this
// page" entries), and lets the page's h1 read the shown section's heading,
// which it then hides from sight but not from a screen reader, so the outline
// stays h1 > h2 > h3. The address follows the choice: `#de` opens German,
// any address inside a section opens that section's language.

const SECTION = "section[data-language]";

/** The element the fragment `hash` names, or null (also for one that does not decode). */
function targetOf(doc, hash) {
  try {
    const id = decodeURIComponent((hash || "").slice(1));
    return id ? doc.getElementById(id) : null;
  } catch {
    return null;
  }
}

const byLanguage = (nodes, language, key = (n) => n.dataset.language) =>
  [...nodes].find((node) => key(node) === language);

/** The language of the section the fragment `hash` points into, or null. */
export function languageAt(doc, hash) {
  return targetOf(doc, hash)?.closest(SECTION)?.dataset.language ?? null;
}

/** Show `language` alone and let the page's title follow it. */
export function showLanguage(doc, language) {
  for (const part of doc.querySelectorAll("[data-language]")) {
    part.hidden = part.dataset.language !== language;
  }
  const section = byLanguage(doc.querySelectorAll(SECTION), language);
  const heading = section?.querySelector("h2");
  const title = doc.querySelector("h1.page-header__title");
  if (title && heading) {
    title.textContent = heading.textContent.trim();
    title.lang = language;
  }
  const radios = doc.querySelectorAll('input[name="language"]');
  const radio = byLanguage(radios, language, (r) => r.value);
  if (radio) radio.checked = true;
}

export function bindLanguageSwitch(doc = document) {
  const win = doc.defaultView;
  const control = doc.querySelector("[data-language-switch]");
  if (!control) return;
  const fallback = control.querySelector('input[name="language"]').value;
  for (const heading of doc.querySelectorAll(`${SECTION} > h2`)) {
    heading.classList.add("visually-hidden");
  }
  control.hidden = false;

  const open = (hash) => {
    showLanguage(doc, languageAt(doc, hash) ?? fallback);
    // The browser scrolled while both languages were shown, so the place it
    // chose has moved: a heading is scrolled to again, a language's own
    // address (#de) opens at the top like the page itself.
    const target = targetOf(doc, hash);
    if (target?.matches(SECTION)) win.scrollTo(0, 0);
    else target?.scrollIntoView();
  };

  control.addEventListener("change", (event) => {
    const language = event.target.value;
    showLanguage(doc, language);
    const { pathname, search } = win.location;
    const hash = language === fallback ? "" : `#${language}`;
    win.history.replaceState(null, "", pathname + search + hash);
  });
  win.addEventListener("hashchange", () => {
    const language = languageAt(doc, win.location.hash);
    const shown = doc.querySelector(`${SECTION}:not([hidden])`);
    if (language && language !== shown?.dataset.language) open(win.location.hash);
  });
  open(win.location.hash);
}
