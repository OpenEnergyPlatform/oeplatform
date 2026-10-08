<!--
SPDX-FileCopyrightText: 2025 Bryan Lancien <https://github.com/bmlancien> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: CC0-1.0
-->

# Design system

The platform is styled by a small set of **design tokens** and **house
components**, taken from the homepage and kept honest by the **component
catalogue**.

## The component catalogue is the reference

What ships is shown, live, on the catalogue page:

- [openenergyplatform.org/styleguide/ :fontawesome-solid-arrow-up-right-from-square:](https://openenergyplatform.org/styleguide/){:target="\_blank"}
- on a local setup: `http://localhost:8000/styleguide/`

It renders every house component from the platform's own templates and its
compiled stylesheet, and shows the source to copy beside each one. On top sits
the token table, with the value each token has **on the page you are looking
at**, so an instance that overrides tokens sees its own values. Add
`?tokens=bootstrap` to see every component with Bootstrap 5.2's stock values:
anything that still looks like the Open Energy Platform there paints a value no
token controls.

The page is public, not indexed by search engines, and linked from no menu.

## Principles

- **Plain, not boring.** Clean surfaces, the brand blue for the one main action
  of a view, soft shadows on what floats.
- **One look per thing.** A button, a tag, a dialog looks the same on every
  page. Use a component from the catalogue; if none fits, add one, with its
  entry.
- **Tokens, never literals.** A component reads `var(--bs-primary)`, never
  `#1F567D`. That is what lets an instance restyle the platform without forking
  it.
- **Colour means something.** Green, cyan and yellow are status only, red is
  danger; none of them is used to make an action stand out.
- **Accessible by default.** Real buttons and links, a visible focus ring,
  motion only for those who have not asked for less. See
  [accessibility](accessibility.md).
- The platform's values stay: quality, transparency, collaboration, open data.

## Add or change a component

A house component has one name, snake_case and singular, in up to three places:

| Place                                           | What                                   |
| ----------------------------------------------- | -------------------------------------- |
| `theming/scss/components/_<name>.scss`          | its styles, reading tokens only        |
| `base/templates/components/<name>.html`         | its markup, if it has any (an include) |
| `base/templates/styleguide/entries/<name>.html` | its catalogue entry                    |

The entry starts with a one-line when-to-use note, `{# use: ... #}`, followed by
the example the catalogue renders and shows as source. For an include, the entry
is the `{% include %}` call with example arguments. Files whose name starts with
`_` are helpers an entry includes, not entries.

The catalogue check workflow (`.github/workflows/catalogue.yaml`) fails a pull
request when

- a component has no entry (`python manage.py check_catalogue`, which you can
  run locally),
- the committed theme differs from what `npm run build:theme` builds, or
- under `?tokens=bootstrap` a component in the catalogue still paints an OEP
  colour (`theming/literal_scan.mjs`).

How to build the theme and where the tokens are defined is in the
[theming README :fontawesome-solid-arrow-up-right-from-square:](https://github.com/OpenEnergyPlatform/oeplatform/tree/develop/theming){:target="\_blank"}.

The theme's component partials from before the catalogue sit in
`theming/scss/legacy/`. Each one moves into `theming/scss/components/`, with its
entry, when it becomes a house component; add nothing new there.

## Figma is the design tool

New components and pages are drawn in
[Figma :fontawesome-solid-arrow-up-right-from-square:](https://www.figma.com/design/EAvBg7KuO1oit5Dry0U6WJ/Components?node-id=4940-344&t=Hsboi5ScY2Kmr8SU-1){:target="\_blank"}
before they are built (contact us if you need access). The catalogue, not Figma,
is the reference for what ships: when the two disagree, the catalogue shows the
platform as it is.
