// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// @vitest-environment happy-dom
//
// The terms of use's language switch (#2650): one language at a time, the
// title follows it, `#de` opens German, and nothing is hidden until the
// module runs.
import { afterEach, describe, expect, it, vi } from "vitest";

import { bindLanguageSwitch, languageAt } from "../language_switch.js";

// The page as base/terms_of_use.html renders it, shortened.
function renderPage() {
  document.body.innerHTML = `
    <h1>Terms of Use</h1>
    <div role="radiogroup" data-language-switch hidden>
      <input type="radio" class="btn-check" name="language" id="language-en"
             value="en" checked>
      <label class="btn btn-outline-primary" for="language-en">English</label>
      <input type="radio" class="btn-check" name="language" id="language-de"
             value="de">
      <label class="btn btn-outline-primary" for="language-de">Deutsch</label>
    </div>
    <ol>
      <li data-language="en"><a href="#en-users">The users</a></li>
      <li data-language="de"><a href="#de-users">Die Nutzer</a></li>
    </ol>
    <section id="en" lang="en" data-language="en">
      <h2>Terms of Use</h2><h3 id="en-users">The users</h3>
    </section>
    <section id="de" lang="de" data-language="de">
      <h2>Nutzungsbedingungen</h2><h3 id="de-users">Die Nutzer</h3>
    </section>`;
}

function at(hash) {
  window.history.replaceState(null, "", `/legal/tou/${hash}`);
}

const shown = () =>
  [...document.querySelectorAll("[data-language]")]
    .filter((part) => !part.hidden)
    .map((part) => part.dataset.language);
const title = () => document.querySelector("h1");
const radio = (language) => document.getElementById(`language-${language}`);

function choose(language) {
  radio(language).checked = true;
  radio(language).dispatchEvent(new Event("change", { bubbles: true }));
}

afterEach(() => {
  document.body.innerHTML = "";
  at("");
});

describe("before the module runs", () => {
  it("renders both languages and keeps the switch out of sight", () => {
    renderPage();
    expect(shown()).toEqual(["en", "de", "en", "de"]);
    expect(document.querySelector("[data-language-switch]").hidden).toBe(true);
  });
});

describe("bindLanguageSwitch", () => {
  it("shows English alone by default and reveals the switch", () => {
    renderPage();
    at("");
    bindLanguageSwitch(document);
    expect(shown()).toEqual(["en", "en"]);
    expect(document.querySelector("[data-language-switch]").hidden).toBe(false);
    expect(radio("en").checked).toBe(true);
    expect(title().textContent).toBe("Terms of Use");
  });

  it("opens German on #de, with the title in German", () => {
    renderPage();
    at("#de");
    bindLanguageSwitch(document);
    expect(shown()).toEqual(["de", "de"]);
    expect(radio("de").checked).toBe(true);
    expect(title().textContent).toBe("Nutzungsbedingungen");
    expect(title().lang).toBe("de");
  });

  it("opens the language of a heading the address points into", () => {
    renderPage();
    at("#de-users");
    bindLanguageSwitch(document);
    expect(shown()).toEqual(["de", "de"]);
  });

  it("switches language and title, and the address follows", () => {
    renderPage();
    at("");
    bindLanguageSwitch(document);

    choose("de");
    expect(shown()).toEqual(["de", "de"]);
    expect(title().textContent).toBe("Nutzungsbedingungen");
    expect(window.location.hash).toBe("#de");

    choose("en");
    expect(shown()).toEqual(["en", "en"]);
    expect(title().textContent).toBe("Terms of Use");
    expect(title().lang).toBe("en");
    expect(window.location.hash).toBe("");
    expect(window.location.pathname).toBe("/legal/tou/");
  });

  it("hides each section's heading from sight only, since the title reads it", () => {
    renderPage();
    bindLanguageSwitch(document);
    for (const heading of document.querySelectorAll("section > h2")) {
      expect(heading.classList.contains("visually-hidden")).toBe(true);
      expect(heading.hidden).toBe(false);
    }
  });

  it("follows a fragment that changes after load, and scrolls to it", () => {
    renderPage();
    at("");
    bindLanguageSwitch(document);
    const target = document.getElementById("de-users");
    const scroll = vi.fn();
    target.scrollIntoView = scroll;

    at("#de-users");
    window.dispatchEvent(new Event("hashchange"));
    expect(shown()).toEqual(["de", "de"]);
    expect(scroll).toHaveBeenCalled();
  });

  it("does nothing on a page without a switch", () => {
    document.body.innerHTML = `<h1>Other</h1><section data-language="en"></section>`;
    bindLanguageSwitch(document);
    expect(shown()).toEqual(["en"]);
    expect(title().textContent).toBe("Other");
  });
});

describe("languageAt", () => {
  it("is null for no fragment, an unknown id, or one outside a section", () => {
    renderPage();
    expect(languageAt(document, "")).toBeNull();
    expect(languageAt(document, "#nowhere")).toBeNull();
    document.body.insertAdjacentHTML("beforeend", '<p id="outside"></p>');
    expect(languageAt(document, "#outside")).toBeNull();
  });
});
