// How wide the tables tab's list must be for each set of columns, and
// whether anything scrolls sideways at common screen widths (#2555).
//
// happy-dom has no layout, so the container-query thresholds in
// login/static/login/tables_tab.css are measured here, once, in a real
// browser on the real row partial, and written beside the queries. A slice
// that adds a column re-runs this and moves them.
//
// Needs a running dev server whose database holds the seeded accounts
// (seed.py), and puppeteer-core with a Chrome:
//
//   PUPPETEER=.../node_modules/puppeteer-core/lib/puppeteer/puppeteer-core.js \
//   CHROME=.../chrome-headless-shell \
//   BASE=http://127.0.0.1:8655 \
//   ACCOUNTS='{"p90":[1,"<sessionid>"],"max":[6,"<sessionid>"]}' \
//   node benchmarks/tables_tab/widths.mjs
//
// ACCOUNTS maps an account to its user id and a session cookie (log the
// owner in with django.test.Client().force_login and read
// cookies["sessionid"]). Optional:
//
// - FONT_DIR: a directory holding Segoe UI (segoeui.ttf, seguisb.ttf,
//   segoeuib.ttf, e.g. /mnt/c/Windows/Fonts under WSL), injected as a web
//   font. The page uses the system font stack, and a Linux headless Chrome
//   falls back to DejaVu Sans, which is wider than what most visitors see.
// - STAND_INS=1: also measure with stand-ins for whichever of ☐, Modified,
//   Created and the ⋯ button the row does not have yet, shaped like the
//   prototype's cells, so a threshold can be set for the complete row.
// - PAGES: how many pages of each account (default 6).
//
// Prints JSON: "min" is the narrowest list each set of columns fits, worst
// page of any account (table plus the wrapper's border); "bar" the filter
// bar's one-line width; "screens" the list width, the active set of
// columns and any overflow at each screen width, sidebar shown.

import { readFileSync } from "node:fs";

const { default: puppeteer } = await import(process.env.PUPPETEER);
const BASE = process.env.BASE || "http://127.0.0.1:8655";
const ACCOUNTS = JSON.parse(process.env.ACCOUNTS);
const PAGES = Number(process.env.PAGES || 6);
const SCREENS = [1920, 1440, 1280, 1024, 800, 390];
const SETS = {
  every: [],
  withoutTopics: [".c-created", ".c-topics"],
  withoutReview: [".c-created", ".c-topics", ".c-review", ".c-ds"],
};

const FONT_CSS = process.env.FONT_DIR
  ? [
      ["segoeui.ttf", 400],
      ["seguisb.ttf", 600],
      ["segoeuib.ttf", 700],
    ]
      .map(([file, weight]) => {
        const data = readFileSync(`${process.env.FONT_DIR}/${file}`).toString("base64");
        return `@font-face{font-family:"Probe";font-weight:${weight};src:url(data:font/ttf;base64,${data})}`;
      })
      .join("") + 'body,body *:not(.dash-tname){font-family:"Probe",sans-serif!important}'
  : "";

const browser = await puppeteer.launch({
  executablePath: process.env.CHROME,
  args: ["--no-sandbox"],
});
const page = await browser.newPage();
const errors = [];
page.on("pageerror", (e) => errors.push(String(e)));

async function go(uid, query = "") {
  await page.goto(`${BASE}/user/profile/${uid}/tables${query}`, {
    waitUntil: "networkidle0",
  });
  if (FONT_CSS) {
    await page.addStyleTag({ content: FONT_CSS });
    await page.evaluate(() => document.fonts.ready);
  }
}

function addStandIns() {
  // only for the columns the row does not have yet
  const table = document.querySelector(".dash-table");
  const has = (cls) => !!table.querySelector(`thead .${cls}`);
  const head = table.querySelector("thead tr");
  const missing = { select: !has("c-select"), modified: !has("c-modified"), created: !has("c-created") };
  if (missing.select) {
    head.insertAdjacentHTML(
      "afterbegin",
      '<th class="c-select"><input type="checkbox" class="form-check-input"></th>',
    );
  }
  head
    .querySelector(".c-menu")
    .insertAdjacentHTML(
      "beforebegin",
      (missing.modified
        ? '<th class="c-modified"><a class="dash-sort dash-sort--active" href="#">Modified <span>↓</span></a></th>'
        : "") +
        (missing.created
          ? '<th class="c-created"><a class="dash-sort" href="#">Created <span>↕</span></a></th>'
          : ""),
    );
  table.querySelectorAll("tbody tr").forEach((tr, i) => {
    if (missing.select) {
      tr.insertAdjacentHTML(
        "afterbegin",
        '<td class="c-select"><input type="checkbox" class="form-check-input"></td>',
      );
    }
    const menu = tr.querySelector(".c-menu");
    menu.insertAdjacentHTML(
      "beforebegin",
      (missing.modified
        ? `<td class="c-modified"><span>28 Sep 2026</span>${i % 3 ? "" : ' <span class="dash-muted">data</span>'}</td>`
        : "") +
        (missing.created
          ? `<td class="c-created">${i % 2 ? '<span class="dash-muted">before Nov 2025</span>' : "<span>14 Mar 2026</span>"}</td>`
          : ""),
    );
    if (!menu.children.length) {
      menu.innerHTML = '<button class="btn btn-sm btn-outline-secondary">⋯</button>';
    }
  });
}

function minWidth(hide) {
  const style = document.createElement("style");
  style.textContent =
    ".dash-table{width:min-content!important}" +
    (hide.length ? `${hide.join(",")}{display:none!important}` : "");
  document.head.appendChild(style);
  const wrap = document.querySelector(".dash-table-wrap");
  const table = document.querySelector(".dash-table");
  const width =
    Math.ceil(table.getBoundingClientRect().width) + wrap.offsetWidth - wrap.clientWidth;
  const columns = [...table.querySelectorAll("thead th")]
    .filter((th) => getComputedStyle(th).display !== "none")
    .map((th) => `${th.classList[0]}:${Math.round(th.getBoundingClientRect().width)}`);
  style.remove();
  return { width, columns };
}

function barWidth() {
  const row = document.querySelector(".dash-filters__row");
  row.style.flexWrap = "nowrap";
  const search = document.querySelector("#tables-search");
  search.style.flex = "0 0 auto";
  search.style.width = getComputedStyle(search).minWidth;
  const items = [
    ...row.querySelectorAll(":scope > input, :scope > .dash-fold > select, :scope > .dash-fold > button"),
  ];
  const gap = parseFloat(getComputedStyle(row).columnGap);
  return Math.ceil(
    items.reduce((sum, e) => sum + e.getBoundingClientRect().width, 0) +
      gap * (items.length - 1),
  );
}

function screen() {
  const shown = (selector) => {
    const cell = document.querySelector(`tbody ${selector}`);
    return !!cell && getComputedStyle(cell).display !== "none";
  };
  const stacked = getComputedStyle(document.querySelector("tbody tr")).display === "grid";
  const wrap = document.querySelector(".dash-table-wrap");
  const root = document.documentElement;
  return {
    list: Math.round(document.querySelector(".dash").getBoundingClientRect().width),
    columns: stacked
      ? "stacked"
      : shown(".c-topics")
        ? "every"
        : shown(".c-review")
          ? "withoutTopics"
          : "withoutReview",
    barFolded: !!document.querySelector("#tables-fold").offsetParent,
    tableOverflow: wrap.scrollWidth - wrap.clientWidth,
    pageOverflow: root.scrollWidth - root.clientWidth,
  };
}

const result = { min: {}, bar: 0, screens: [], errors };
await page.setViewport({ width: 2560, height: 900 });
for (const [key, [uid, cookie]] of Object.entries(ACCOUNTS)) {
  await page.setCookie({ name: "sessionid", value: cookie, url: BASE });
  // a filter behind "More filters" applied, so its count shows too
  await go(uid, "?topics=grid");
  result.bar = Math.max(result.bar, await page.evaluate(barWidth));
  for (const standIns of process.env.STAND_INS ? [false, true] : [false]) {
    for (let n = 1; n <= PAGES; n++) {
      await go(uid, `?page=${n}`);
      if (standIns) await page.evaluate(addStandIns);
      for (const [set, hide] of Object.entries(SETS)) {
        const slot = `${standIns ? "withStandIns" : "realRow"}.${set}`;
        const measured = await page.evaluate(minWidth, hide);
        if (!result.min[slot] || measured.width > result.min[slot].width) {
          result.min[slot] = { ...measured, account: key, page: n };
        }
      }
    }
  }
}

for (const [key, [uid, cookie]] of Object.entries(ACCOUNTS)) {
  await page.setCookie({ name: "sessionid", value: cookie, url: BASE });
  for (const width of SCREENS) {
    await page.setViewport({ width, height: 900 });
    let worst = null;
    for (let n = 1; n <= PAGES; n++) {
      await go(uid, `?page=${n}`);
      const seen = { ...(await page.evaluate(screen)), page: n };
      const excess = (s) => s.tableOverflow + s.pageOverflow;
      if (!worst || excess(seen) > excess(worst)) worst = seen;
    }
    result.screens.push({ account: key, screen: width, ...worst });
  }
}

console.log(JSON.stringify(result, null, 1));
await browser.close();
