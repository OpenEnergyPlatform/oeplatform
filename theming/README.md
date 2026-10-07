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

## Build it

From the repository root:

```sh
npm install            # once, or after package.json changed
npm run build:theme    # theming/oepstrap.scss -> base/static/css/bootstrap.min.css
```

Commit the SCSS change **and** the rebuilt `bootstrap.min.css` together. Never
edit `bootstrap.min.css` by hand: the next rebuild drops the edit, and CI fails
the pull request before that.

### Why the compiled file is committed

The production image is built from `docker/Dockerfile`, which has no Node stage,
and the production host has no internet access. So the stylesheet must already
be in the tree when the image is built.

To keep the committed file honest, the **catalogue check** workflow
(`.github/workflows/catalogue.yaml`) runs on every pull request that touches
templates, CSS, the theme or the npm manifests. It runs `npm run build:theme` on
a clean checkout and fails when the result differs from the committed file.

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

| File                               | What it holds                                                                                     |
| ---------------------------------- | ------------------------------------------------------------------------------------------------- |
| `oepstrap.scss`                    | The entry point. One `@use` per component or layout.                                              |
| `_variables.scss`                  | The OEP values for Bootstrap variables (colours, radii, font sizes, ...).                         |
| `scss/base/_index.scss`            | Forwards Bootstrap, configured with those values. **Only variables listed here reach Bootstrap.** |
| `scss/base/_custom_variables.scss` | OEP-only variables (`$C--…`) that Bootstrap does not know.                                        |
| `scss/base/_mixins.scss`           | Shared mixins.                                                                                    |
| `scss/tokens/_root.scss`           | Emits the `--oep-*` design tokens at `:root`.                                                     |
| `scss/tokens/_remap.scss`          | The re-map layer: Bootstrap's component variables pointed at the tokens.                          |
| `scss/components/`                 | Components (buttons, cards, tags, ...).                                                           |
| `scss/layouts/`                    | Page layouts (database, profile, review, ...).                                                    |

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
`@use 'scss/components/<name>';` to `oepstrap.scss`, and rebuild.

## Review what a change did

Minified CSS is one long line, so a plain diff only says that it changed. Split
it at declarations first:

```sh
split_css() { sed 's/\([;}]\)/\1\n/g'; }
diff <(git show HEAD:base/static/css/bootstrap.min.css | split_css) \
     <(split_css < base/static/css/bootstrap.min.css)
```
