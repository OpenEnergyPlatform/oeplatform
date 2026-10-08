// The literal scan: does a house component paint an OEP colour that no token
// controls? (#2636, spec #2632)
//
// It opens the component catalogue twice in headless Chrome:
//
// 1. under ?tokens=bootstrap, to learn what the stock tokens produce, and then
//    as the instance ships it, to learn the OEP colours: every colour declared
//    at :root by the page's stylesheets (Bootstrap's palette and the tokens,
//    -rgb twins included) plus every colour literal in theming/_variables.scss,
//    minus the colours the stock tokens produce themselves (white, ...);
// 2. under ?tokens=bootstrap again, where every token carries Bootstrap 5.2's
//    stock value, and lists each visible element inside a catalogue entry whose
//    computed colour (text, background, borders, outline, SVG fill and stroke,
//    shadows, ::before/::after) is one of those OEP colours.
//
// Any hit fails: that colour reaches the component through a literal or a
// Bootstrap palette variable, so an instance's tokens cannot change it. The
// scan also fails when it is blind: no entry on the page, the stock stylesheet
// not loaded, or no hit at all in the first rendering (where OEP colours are
// expected), because a scan that cannot see an OEP colour passes for nothing.
//
// Run it against a running server:
//
//   PUPPETEER=.../node_modules/puppeteer-core/lib/esm/puppeteer/puppeteer-core.js \
//   CHROME=.../chrome-headless-shell \
//   BASE=http://127.0.0.1:8000 \
//   node theming/literal_scan.mjs
//
// PUPPETEER defaults to the bare package name `puppeteer-core`. The catalogue
// workflow (.github/workflows/catalogue.yaml) runs it on every pull request
// that can change the look of the platform.

import { readFileSync } from "node:fs";

if (!process.env.CHROME || !process.env.BASE) {
  console.error("set CHROME and BASE, see the top of this file");
  process.exit(2);
}
const { default: puppeteer } = await import(
  process.env.PUPPETEER || "puppeteer-core"
);
const catalogue = new URL("styleguide/", process.env.BASE.replace(/\/?$/, "/"));
const literals = [
  ...readFileSync(new URL("./_variables.scss", import.meta.url), "utf8").matchAll(
    /#[0-9a-fA-F]{3,8}\b/g
  ),
].map((match) => match[0]);

// Runs in the page: every opaque-enough colour in a computed value, as
// "r, g, b". Chrome writes most colours as rgb()/rgba(), and a color-mix() (the
// re-map layer's shades) as color(srgb r g b) with channels from 0 to 1.
function computedTriples(value) {
  const found = [];
  for (const m of value.matchAll(/rgba?\(([\d.]+), ([\d.]+), ([\d.]+)(?:, ([\d.]+))?\)/g)) {
    if (m[4] === undefined || Number(m[4]) > 0) found.push([m[1], m[2], m[3]].map(Number));
  }
  for (const m of value.matchAll(/color\(srgb ([\d.e-]+) ([\d.e-]+) ([\d.e-]+)(?: \/ ([\d.]+))?\)/g)) {
    if (m[4] === undefined || Number(m[4]) > 0) {
      found.push([m[1], m[2], m[3]].map((c) => Number(c) * 255));
    }
  }
  return found.map((rgb) => rgb.map((c) => Math.round(c)).join(", "));
}

// Runs in the page: the colours (as "r, g, b") declared at :root by every
// stylesheet, or by the stock-token one only, plus `extra` literal values.
function rootColours({ onlyStock, extra }) {
  const probe = document.createElement("i");
  document.body.append(probe);
  const triple = (value) => {
    probe.style.color = "";
    probe.style.color = /^\d+\s*,\s*\d+\s*,\s*\d+$/.test(value) ? `rgb(${value})` : value;
    if (!probe.style.color) return null;
    return computedTriples(getComputedStyle(probe).color)[0] || null;
  };
  const names = new Set();
  const visit = (rules) => {
    for (const rule of rules) {
      if (rule.cssRules) visit(rule.cssRules);
      if (rule.selectorText === ":root") {
        for (const property of rule.style) {
          if (property.startsWith("--")) names.add(property);
        }
      }
    }
  };
  for (const sheet of document.styleSheets) {
    if (onlyStock && !(sheet.href || "").includes("stock_tokens")) continue;
    visit(sheet.cssRules);
  }
  const root = getComputedStyle(document.documentElement);
  const colours = new Set();
  for (const name of names) {
    const colour = triple(root.getPropertyValue(name).trim());
    if (colour) colours.add(colour);
  }
  for (const value of extra) {
    const colour = triple(value);
    if (colour) colours.add(colour);
  }
  probe.remove();
  return [...colours];
}

// Runs in the page: every visible element inside an entry painting one of
// `colours`.
function scan(colours) {
  const oep = new Set(colours);
  const triples = computedTriples;
  const hits = [];
  const entries = [...document.querySelectorAll(".styleguide-preview")];
  const check = (el, style, where) => {
    const painted = [
      ["color", style.color],
      ["background-color", style.backgroundColor],
      ["box-shadow", style.boxShadow],
      ["fill", style.fill],
      ["stroke", style.stroke],
    ];
    for (const side of ["Top", "Right", "Bottom", "Left"]) {
      if (parseFloat(style[`border${side}Width`]) > 0) {
        painted.push([`border-${side.toLowerCase()}-color`, style[`border${side}Color`]]);
      }
    }
    if (style.outlineStyle !== "none" && parseFloat(style.outlineWidth) > 0) {
      painted.push(["outline-color", style.outlineColor]);
    }
    if (style.textDecorationLine !== "none") {
      painted.push(["text-decoration-color", style.textDecorationColor]);
    }
    for (const [property, value] of painted) {
      for (const colour of triples(value || "")) {
        if (oep.has(colour)) {
          const name = el.closest(".styleguide-preview").dataset.entry;
          const cls = el.getAttribute("class") || "";
          hits.push(`${name}: ${property} rgb(${colour}) on <${el.tagName.toLowerCase()}${cls ? ` class="${cls}"` : ""}>${where}`);
        }
      }
    }
  };
  for (const entry of entries) {
    for (const el of entry.querySelectorAll("*")) {
      const box = el.getBoundingClientRect();
      const style = getComputedStyle(el);
      if (!box.width || !box.height || style.visibility === "hidden") continue;
      check(el, style, "");
      for (const pseudo of ["::before", "::after"]) {
        const ps = getComputedStyle(el, pseudo);
        if (ps.content && ps.content !== "none") check(el, ps, pseudo);
      }
    }
  }
  return {
    entries: entries.length,
    stock: !!document.querySelector('link[href*="stock_tokens"]'),
    hits: [...new Set(hits)],
  };
}

const browser = await puppeteer.launch({
  executablePath: process.env.CHROME,
  args: ["--no-sandbox"],
});
let failed = false;
const fail = (message) => {
  console.error(`::error::${message}`);
  failed = true;
};
try {
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });

  const open = async (url) => {
    const response = await page.goto(url, { waitUntil: "networkidle0" });
    if (!response.ok()) throw new Error(`${url} answers ${response.status()}`);
    await page.addScriptTag({ content: computedTriples.toString() });
  };
  const stock = new URL("?tokens=bootstrap", catalogue);
  const shipped = new URL("?tokens=theme", catalogue);

  await open(stock);
  const theirs = new Set(await page.evaluate(rootColours, { onlyStock: true, extra: [] }));
  await open(shipped);
  const ours = await page.evaluate(rootColours, { onlyStock: false, extra: literals });
  const oep = ours.filter((colour) => !theirs.has(colour));
  const seen = await page.evaluate(scan, oep);
  await open(stock);
  const result = await page.evaluate(scan, oep);

  console.log(
    `${oep.length} OEP colours; ${result.entries} entries; ` +
      `${seen.hits.length} OEP colours painted as shipped, ` +
      `${result.hits.length} under ?tokens=bootstrap.`
  );
  if (!result.entries) fail("The catalogue shows no entry, so nothing was scanned.");
  if (!result.stock) fail(`${stock} does not load the stock-token stylesheet.`);
  if (!oep.length || !seen.hits.length) {
    fail("The scan found no OEP colour in the catalogue as shipped, so it cannot tell a literal from a token.");
  }
  for (const hit of result.hits) {
    fail(`Under ?tokens=bootstrap, ${hit} is an OEP colour no token controls. Read a token instead (theming/README.md, "Design tokens").`);
  }
} finally {
  await browser.close();
}
process.exit(failed ? 1 : 0);
