// Does the homepage still render pixel for pixel as it did? (#2635)
//
// Every stage-2 slice that touches the design tokens, a shell or shared CSS
// must leave the homepage unchanged (spec #2632, "the homepage does not
// change"). This takes the same screenshots before and after a change and
// compares them pixel by pixel. It is a local check, not part of CI: run it
// on the base of the branch and on the branch, and report the result in the
// pull request.
//
//   PUPPETEER=.../node_modules/puppeteer-core/lib/puppeteer/puppeteer-core.js \
//   CHROME=.../chrome-headless-shell \
//   BASE=http://127.0.0.1:8635 SESSION=<sessionid> \
//   node benchmarks/homepage/compare.mjs shoot <dir>
//
//   node benchmarks/homepage/compare.mjs diff <before-dir> <after-dir>
//
// `shoot` writes, for signed out and signed in (SESSION, a session cookie:
// log a user in with django.test.Client().force_login and read
// cookies["sessionid"]), at 1440 and 390 px:
//
// - home-<auth>-<width>.png: the whole page, nothing masked;
// - menu-<auth>-1440.png: the window with a navbar dropdown open and its
//   second item hovered (the dropdown's border, radius, shadow and hover
//   tint are in the navbar's styles, not on the page at rest);
// - burger-<auth>-390.png: the window with the collapsed menu open.
//
// The screenshots are taken with prefers-reduced-motion, so the homepage's
// scroll fade-in shows every section at once instead of only those scrolled
// past. The server should serve the source stylesheets, not a compressed
// copy built from another checkout: run it with COMPRESS_ENABLED = False and
// a STATIC_ROOT of its own.
//
// `diff` compares every PNG of the first directory with its namesake in the
// second, prints one line per shot, writes a diff image (changed pixels in
// red over a faded copy) for each that differs, and exits 1 if any differs.
// With CHROME and PUPPETEER set it decodes the PNGs in the browser, so it
// needs no image library.

import {
  readdirSync,
  readFileSync,
  writeFileSync,
  mkdirSync,
  existsSync,
} from "node:fs";
import { join } from "node:path";

const { default: puppeteer } = await import(process.env.PUPPETEER);
const launch = () =>
  puppeteer.launch({
    executablePath: process.env.CHROME,
    args: ["--no-sandbox"],
  });

const [mode, ...dirs] = process.argv.slice(2);

async function settle(page) {
  await page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all(
      [...document.images].map((img) =>
        img.complete
          ? null
          : new Promise((done) =>
              img.addEventListener("load", done, { once: true })
            )
      )
    );
  });
}

async function shoot(out) {
  const BASE = process.env.BASE || "http://127.0.0.1:8635";
  mkdirSync(out, { recursive: true });
  const browser = await launch();
  const auths = [["out", null]];
  if (process.env.SESSION) auths.push(["in", process.env.SESSION]);
  else console.warn("SESSION is not set: signed-in shots skipped");

  async function open(width, session) {
    const page = await browser.newPage();
    await page.setViewport({ width, height: 900 });
    await page.emulateMediaFeatures([
      { name: "prefers-reduced-motion", value: "reduce" },
    ]);
    if (session) {
      await page.setCookie({ name: "sessionid", value: session, url: BASE });
    }
    await page.goto(`${BASE}/`, { waitUntil: "networkidle0" });
    await settle(page);
    return page;
  }

  for (const [auth, session] of auths) {
    for (const width of [1440, 390]) {
      const page = await open(width, session);
      await page.screenshot({
        path: join(out, `home-${auth}-${width}.png`),
        fullPage: true,
      });
      await page.close();
    }

    let page = await open(1440, session);
    await page.click("#navbarDropdownDatabase");
    await page.hover(
      '[aria-labelledby="navbarDropdownDatabase"] .dropdown-item:nth-child(2)'
    );
    await new Promise((done) => setTimeout(done, 500));
    await page.screenshot({ path: join(out, `menu-${auth}-1440.png`) });
    await page.close();

    page = await open(390, session);
    await page.click(".navbar-toggler");
    await new Promise((done) => setTimeout(done, 800));
    await page.screenshot({ path: join(out, `burger-${auth}-390.png`) });
    await page.close();
  }
  await browser.close();
  console.log(
    `written to ${out}: ${readdirSync(out)
      .filter((f) => f.endsWith(".png"))
      .join(", ")}`
  );
}

async function diff(before, after) {
  const browser = await launch();
  const page = await browser.newPage();
  const outDir = join(after, "diff");
  let differs = 0;
  for (const name of readdirSync(before)
    .filter((f) => f.endsWith(".png"))
    .sort()) {
    if (!existsSync(join(after, name))) {
      console.log(`${name}: MISSING in ${after}`);
      differs += 1;
      continue;
    }
    const a = readFileSync(join(before, name));
    const b = readFileSync(join(after, name));
    if (a.equals(b)) {
      console.log(`${name}: identical (byte for byte)`);
      continue;
    }
    const result = await page.evaluate(
      async (srcA, srcB) => {
        const load = (src) =>
          new Promise((done, fail) => {
            const img = new Image();
            img.onload = () => done(img);
            img.onerror = fail;
            img.src = src;
          });
        const [imgA, imgB] = await Promise.all([load(srcA), load(srcB)]);
        if (imgA.width !== imgB.width || imgA.height !== imgB.height) {
          return {
            size: `${imgA.width}x${imgA.height} vs ${imgB.width}x${imgB.height}`,
          };
        }
        const pixels = (img) => {
          const canvas = new OffscreenCanvas(img.width, img.height);
          const ctx = canvas.getContext("2d");
          ctx.drawImage(img, 0, 0);
          return ctx.getImageData(0, 0, img.width, img.height);
        };
        const pa = pixels(imgA).data;
        const imageB = pixels(imgB);
        const pb = imageB.data;
        let changed = 0;
        let top = Infinity;
        let bottom = -1;
        for (let i = 0; i < pa.length; i += 4) {
          const same =
            pa[i] === pb[i] &&
            pa[i + 1] === pb[i + 1] &&
            pa[i + 2] === pb[i + 2] &&
            pa[i + 3] === pb[i + 3];
          const y = Math.floor(i / 4 / imgA.width);
          if (same) {
            pb[i] = 255 - (255 - pb[i]) / 4;
            pb[i + 1] = 255 - (255 - pb[i + 1]) / 4;
            pb[i + 2] = 255 - (255 - pb[i + 2]) / 4;
          } else {
            changed += 1;
            top = Math.min(top, y);
            bottom = Math.max(bottom, y);
            pb.set([255, 0, 0, 255], i);
          }
        }
        if (!changed) return { changed };
        const canvas = document.createElement("canvas");
        canvas.width = imgA.width;
        canvas.height = imgA.height;
        canvas.getContext("2d").putImageData(imageB, 0, 0);
        return {
          changed,
          total: pa.length / 4,
          top,
          bottom,
          png: canvas.toDataURL("image/png"),
        };
      },
      `data:image/png;base64,${a.toString("base64")}`,
      `data:image/png;base64,${b.toString("base64")}`
    );
    if (result.size) {
      console.log(`${name}: DIFFERENT size, ${result.size}`);
      differs += 1;
    } else if (!result.changed) {
      console.log(
        `${name}: identical (pixel for pixel; the files differ only in encoding)`
      );
    } else {
      mkdirSync(outDir, { recursive: true });
      writeFileSync(
        join(outDir, name),
        Buffer.from(result.png.split(",")[1], "base64")
      );
      const where = `rows ${result.top}-${result.bottom}`;
      console.log(
        `${name}: DIFFERENT, ${result.changed} of ${result.total} pixels, ${where},` +
          ` see ${join(outDir, name)}`
      );
      differs += 1;
    }
  }
  await browser.close();
  console.log(differs ? `${differs} shot(s) differ` : "no difference");
  process.exit(differs ? 1 : 0);
}

if (mode === "shoot" && dirs.length === 1) await shoot(dirs[0]);
else if (mode === "diff" && dirs.length === 2) await diff(dirs[0], dirs[1]);
else {
  console.error(
    "usage: compare.mjs shoot <dir> | compare.mjs diff <before-dir> <after-dir>"
  );
  process.exit(2);
}
