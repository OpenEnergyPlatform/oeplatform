<!--
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Eike Broda <https://github.com/ebroda>
SPDX-FileCopyrightText: 2025 Johann Wagner <https://github.com/johannwagner>  © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: CC0-1.0
-->

# The Bootstrap theme

The platform is styled by one stylesheet, `base/static/css/bootstrap.min.css`:
Bootstrap 5.2.0 with the OEP variables and the OEP components and layouts
compiled into it. This directory is its source.

Every house component and token is shown, live, in the **component catalogue**
at `/styleguide/` (on
[openenergyplatform.org](https://openenergyplatform.org/styleguide/), or
`http://localhost:8000/styleguide/` locally). How a component is named, where
its entry goes and what the catalogue check enforces is in
[docs/dev/frontend/design-system.md](../docs/dev/frontend/design-system.md).

## Build it

From the repository root:

```sh
npm install            # once, or after package.json changed
npm run build:theme    # theming/oepstrap.scss -> base/static/css/bootstrap.min.css
                       # theming/stock_tokens.scss -> base/static/styleguide/stock_tokens.css
```

Commit the SCSS change **and** the rebuilt files together. Never edit
`bootstrap.min.css` or `stock_tokens.css` by hand: the next rebuild drops the
edit, and CI fails the pull request before that.

### Why the compiled file is committed

The production image is built from `docker/Dockerfile`, which has no Node stage,
and the production host has no internet access. So the stylesheet must already
be in the tree when the image is built.

To keep the committed file honest, the **catalogue check** workflow
(`.github/workflows/catalogue.yaml`) runs on every pull request that touches
templates, CSS, the theme or the npm manifests. It runs `npm run build:theme` on
a clean checkout and fails when the result differs from the committed files. It
also runs the catalogue's two checks, `manage.py check_catalogue` and the
literal scan (see [Check a component](#check-a-component)).

### Pinned versions

`sass` and `bootstrap` are pinned to exact versions in `package.json` (no `^`),
because compressed output differs between Sass releases, and a floating version
would make the check fail without anyone having changed the theme. Bootstrap's
Sass sources come from `node_modules/bootstrap/scss` (the build passes
`--load-path=node_modules`; a `theming/bootstrap` clone left over from the old
Docker route is no longer read and can be deleted). Upgrading either package is
a deliberate change: bump it, rebuild, and review the diff of the compiled file
in the same pull request.

`--quiet-deps` silences the deprecation warnings that Bootstrap 5.2's own
sources raise under this Sass version. Warnings from the files in this directory
are still printed.

## What is where

| File                               | What it holds                                                                                                         |
| ---------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `oepstrap.scss`                    | The entry point. One `@use` per component or layout.                                                                  |
| `_variables.scss`                  | The OEP values for Bootstrap variables (colours, radii, font sizes, ...) and the `--oep-*` token defaults (`$oep-*`). |
| `scss/base/_index.scss`            | Forwards Bootstrap, configured with those values. **Only variables listed here reach Bootstrap.**                     |
| `scss/base/_custom_variables.scss` | OEP-only layout variables (`$C--…`) that are not tokens.                                                              |
| `scss/base/_mixins.scss`           | Shared mixins.                                                                                                        |
| `scss/tokens/_root.scss`           | Emits the `--oep-*` design tokens at `:root`.                                                                         |
| `scss/tokens/_remap.scss`          | The re-map layer: Bootstrap's component variables pointed at the tokens.                                              |
| `scss/components/`                 | House components only, one partial per component, each with its catalogue entry.                                      |
| `scss/legacy/`                     | The component partials from before the catalogue (buttons, cards, tags, ...). Still compiled; add nothing here.       |
| `scss/layouts/`                    | Page layouts (database, profile, review, ...) and the collapse and sidebar rules.                                     |
| `stock_tokens.scss`                | Every token at Bootstrap 5.2's stock value, for the catalogue's `?tokens=bootstrap`.                                  |
| `literal_scan.mjs`                 | The literal scan the catalogue check runs.                                                                            |

## Design tokens

The theme's colours, radii, shadows and a few sizes are **design tokens**: CSS
custom properties at `:root` that every stylesheet reads instead of a literal
value. Bootstrap's own names are used where Bootstrap has one (`--bs-primary`,
`--bs-body-color`, `--bs-border-color`, `--bs-border-radius`, ...); the rest are
a small `--oep-*` set (`--oep-text-muted`, `--oep-surface-subtle`,
`--oep-shadow-sm`, ...).

- **The defaults live in `_variables.scss`**, nowhere else: the Bootstrap
  variables (forwarded through `scss/base/_index.scss`) for the `--bs-*` tokens,
  and the `$oep-*` variables at the end of the file for the `--oep-*` ones,
  which `scss/tokens/_root.scss` emits.
- **Read a token, never a literal**, in the theme and in page CSS alike
  (`border: 1px solid var(--bs-border-color)`, not `#e9f0f5`). An instance that
  overrides a token in its own stylesheet then restyles your work too.
- **A token name is a promise to instances.** Keep the `--oep-*` set small; when
  a rename is forced, keep the old name as an alias for one release.

### The re-map layer

Bootstrap 5.2 compiles literal values into its component variables
(`.btn-primary{--bs-btn-bg:#1F567D}`), so overriding `--bs-primary` alone
recolours links but not one button. `scss/tokens/_remap.scss` restates those
variables as the tokens they came from, with hover and active shades computed by
`color-mix()` the way Bootstrap's `shade-color()` computes them. At the default
token values it changes nothing. When a house component starts using a Bootstrap
component that is not re-mapped yet, add its variables there.

The shades need `color-mix()` (Chrome and Edge 111, Firefox 113, Safari 16.2,
all from 2023). In an older browser a button's hover and active backgrounds fall
back to transparent rather than to Bootstrap's shade.

An instance's stylesheet must set a colour **and** its `-rgb` twin
(`--bs-primary` and `--bs-primary-rgb`): Bootstrap's utilities, among them the
navbar's `bg-primary`, read the twin, and CSS cannot derive one from the other.

## Check the homepage

The homepage is the design reference and must not change by a pixel when the
theme, a shell or shared CSS changes. `benchmarks/homepage/compare.mjs` takes
full-page screenshots (1440 and 390 px, signed out and in, plus an open navbar
menu) before and after a change and compares them pixel by pixel; how to run it
is at the top of the file. Run it for every such change and report the result in
the pull request.

## Change a Bootstrap variable

A Bootstrap variable takes the OEP value only if it is set in **both** places:

1. `_variables.scss`: set the value, e.g. `$blue-500: #2972A6;`
2. `scss/base/_index.scss`: forward it into Bootstrap, e.g.
   `$blue-500: $blue-500,`

A variable set in `_variables.scss` but missing from the forward list changes
nothing in Bootstrap: the theme's own partials see the OEP value, Bootstrap
keeps its default. Bootstrap's defaults for every variable are in
`node_modules/bootstrap/scss/_variables.scss`.

`$theme-colors` holds exactly Bootstrap's eight theme colours. Each entry there
becomes a button, alert, text, background, border and link variant, so the light
tints behind the theme's `.background-*` classes live in their own map,
`$theme-background-colors`.

## Add a component or layout

Create `scss/components/_<name>.scss` (or `scss/layouts/_<name>.scss`), start it
with `@use '../base/' as *;` like its neighbours, add
`@use 'scss/components/<name>';` to `oepstrap.scss`, and rebuild. A partial in
`scss/components/` is a house component: give it a catalogue entry,
`base/templates/styleguide/entries/<name>.html`, or the catalogue check fails.

The partials in `scss/legacy/` predate the catalogue. A ticket that turns one
into a house component moves it to `scss/components/` under its singular
snake_case name (`_alerts` becomes `_alert`) and adds its entry; the empty layer
is deleted at the end (#2660).

## Check a component

Open `/styleguide/?tokens=bootstrap`. It loads `stock_tokens.css` after the
theme, so every token carries Bootstrap 5.2's stock value and no instance
stylesheet applies. A component that still shows an OEP colour there reads a
literal or a Bootstrap palette variable (`--bs-gray-300`, ...) instead of a
token, and an instance cannot restyle it.

The catalogue check does the same mechanically. With a server running:

```sh
python manage.py check_catalogue        # every component has an entry, both modes render
PUPPETEER=.../puppeteer-core/lib/esm/puppeteer/puppeteer-core.js \
CHROME=.../chrome BASE=http://127.0.0.1:8000 \
node theming/literal_scan.mjs           # no component paints an OEP colour under stock tokens
```

The scan learns the OEP colours from the catalogue as shipped (every colour
declared at `:root`, plus every colour literal in `_variables.scss`) and then
lists each visible element inside a catalogue entry that still paints one under
`?tokens=bootstrap`. It looks at what is visible at rest, not at hover states.

A new token goes in three places: its default in `_variables.scss` (and
`scss/tokens/_root.scss` for an `--oep-*` one), its stock value in
`stock_tokens.scss`, and the catalogue's token table, `TOKENS` in
`base/styleguide.py`. `check_catalogue` fails when the three disagree.

## Review what a change did

Minified CSS is one long line, so a plain diff only says that it changed. Split
it at declarations first:

```sh
split_css() { sed 's/\([;}]\)/\1\n/g'; }
diff <(git show HEAD:base/static/css/bootstrap.min.css | split_css) \
     <(split_css < base/static/css/bootstrap.min.css)
```
