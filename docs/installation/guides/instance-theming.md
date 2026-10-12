<!--
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: CC0-1.0
-->

# Theming an instance

You run your own instance of the platform and want it in your colours, with your
name and logo and your own privacy policy, without forking the code. Two
settings do that:

| Setting                  | What it does                                                                                                               |
| ------------------------ | -------------------------------------------------------------------------------------------------------------------------- |
| `INSTANCE_STYLESHEETS`   | A list of static paths. Each is linked on every page, after every stylesheet of the platform, so your values win.          |
| `INSTANCE_TEMPLATE_DIRS` | A list of directories searched before the platform's templates. A template there replaces the platform's of the same name. |

Both are read from your local settings, `oeplatform/securitysettings.py`, and
both are optional: an instance that sets neither looks exactly like the Open
Energy Platform. The default settings file (`securitysettings.py.default`) fills
them from two comma-separated environment variables, `OEP_INSTANCE_STYLESHEETS`
and `OEP_INSTANCE_TEMPLATE_DIRS`, which is the convenient form for a container
(see [below](#in-a-container-image)).

```python
# oeplatform/securitysettings.py
INSTANCE_STYLESHEETS = ["instance/theme.css"]
INSTANCE_TEMPLATE_DIRS = ["/srv/oep-instance/templates"]
```

A path in `INSTANCE_STYLESHEETS` is a static path, as `{% static %}` takes it,
so `collectstatic` must find the file: put it in a directory of
`STATICFILES_DIRS` (by default `assets/`, so `assets/instance/theme.css` is
`instance/theme.css`). While a listed stylesheet cannot be found, `manage.py`
commands such as `collectstatic`, `migrate` and `runserver` stop with the system
check `base.E001`, because with `DEBUG` off every page would fail on it. A
listed template directory that does not exist is a warning (`base.W001`).

## What you can override

**Supported**, which means kept stable across upgrades and announced in the
changelog when one has to change:

- **the design tokens**, in your stylesheet (below);
- **the brand**, three templates under `brand/`:

  | Template                  | What it holds                                                                                                                                                                                                                         |
  | ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
  | `brand/logo.html`         | The logo, as markup. It is called with `size`, the square in px the place is drawn for (45 in the navbar, 32 in the homepage footer), and `alt`, empty where the name stands beside it. The navbar's logo sits on the primary colour. |
  | `brand/name.html`         | The platform's name, one line of plain text (not markup: it is escaped where it is shown): the navbar logo's link text, the homepage footer.                                                                                          |
  | `brand/title_prefix.html` | What every page title starts with, one line of text (`OEP`).                                                                                                                                                                          |

- **the legal pages**, `base/privacy_policy.html` and `base/terms_of_use.html`.
  Every instance has to replace these: they describe the Open Energy Platform's
  operators.

A replacement legal page extends the platform's shell like the original does:

```django
{# /srv/oep-instance/templates/base/privacy_policy.html #}
{% extends "base/base.html" %}
{% block main-content-body %}
  <h1>Privacy policy</h1>
  <p>Example Grid Lab operates this site …</p>
{% endblock %}
```

A brand template is short:

```django
{# /srv/oep-instance/templates/brand/name.html #}
Example Grid Platform
```

```django
{# /srv/oep-instance/templates/brand/logo.html #}
{% load static %}
<img width="{{ size }}" height="{{ size }}" alt="{{ alt }}"
     src="{% static 'instance/logo.svg' %}" />
```

**Everything else** can be overridden the same way, by a template of the same
name or a rule in your stylesheet, but is not supported: templates, class names
and page structure change between releases without notice. Some places are not
covered yet: the sign-in and account pages show the platform's own logo, the
navbar's Sign up and Sign in buttons keep a blue of their own, the pages built
with React (scenario bundles, the ontology browser) do not read the tokens, and
the favicon is a static file (`favicon.ico`), which a file of that name in
`STATICFILES_DIRS` replaces.

Compressed bundles are built ahead of time by `manage.py compress`, so a
`{% compress %}` block in a template you override exists only once `compress`
has run with your template directory configured; otherwise the page fails. Link
stylesheets through `INSTANCE_STYLESHEETS` instead, which needs no compression.

## The design tokens

The platform's colours, radii, shadows and a few sizes are CSS custom properties
at `:root`, and every house component reads them instead of a literal value.
Your stylesheet sets the ones you want to change:

```css
/* assets/instance/theme.css */
:root {
  --bs-primary: #7a1f5d;
  --bs-primary-rgb: 122, 31, 93;
  --bs-body-color: #2b2b2b;
  --bs-body-color-rgb: 43, 43, 43;
  --oep-surface-subtle: #fbf6f9;
  --bs-border-radius: 6px;
}
```

**Set a colour and its `-rgb` twin together.** Bootstrap's utility classes read
the twin (the navbar's background is `bg-primary`, which is
`rgba(var(--bs-primary-rgb), …)`), and CSS cannot derive one from the other. A
primary colour without its twin recolours buttons and links but leaves the
navbar in the platform's blue. The twins are listed below; the ones that matter
most are those of `--bs-primary`, `--bs-secondary` and `--bs-body-color`.

Hover and pressed shades are mixed from the tokens in the browser, so they
follow your colours without being set.

| Token                     | Kind   | Role                                                         |
| ------------------------- | ------ | ------------------------------------------------------------ |
| `--bs-primary`            | colour | primary action, links, brand                                 |
| `--bs-primary-rgb`        | rgb    | the same colour, for Bootstrap's utilities                   |
| `--bs-secondary`          | colour | secondary (outline) actions                                  |
| `--bs-secondary-rgb`      | rgb    | the same colour, for Bootstrap's utilities                   |
| `--bs-body-color`         | colour | text                                                         |
| `--bs-body-color-rgb`     | rgb    | the same colour, for Bootstrap's utilities                   |
| `--oep-text-muted`        | colour | secondary text                                               |
| `--oep-heading-color`     | colour | platform headings (by default the primary colour)            |
| `--bs-border-color`       | colour | borders, dividers                                            |
| `--oep-border-strong`     | colour | field borders                                                |
| `--oep-surface`           | colour | cards, overlays                                              |
| `--oep-surface-subtle`    | colour | light bands, the header band, table heads                    |
| `--oep-surface-strong`    | colour | strong bands (hero, academy, footer; by default the primary) |
| `--oep-surface-hover`     | colour | hover tint (the navbar dropdown's)                           |
| `--oep-on-strong`         | colour | text on strong bands                                         |
| `--oep-on-strong-muted`   | colour | muted text on strong bands                                   |
| `--bs-success`            | colour | status: success, never an action                             |
| `--bs-success-rgb`        | rgb    | the same colour, for Bootstrap's utilities                   |
| `--bs-info`               | colour | status: information, never an action                         |
| `--bs-info-rgb`           | rgb    | the same colour, for Bootstrap's utilities                   |
| `--bs-warning`            | colour | status: warning, never an action                             |
| `--bs-warning-rgb`        | rgb    | the same colour, for Bootstrap's utilities                   |
| `--bs-danger`             | colour | status: error; destructive actions                           |
| `--bs-danger-rgb`         | rgb    | the same colour, for Bootstrap's utilities                   |
| `--bs-border-radius`      | radius | in the page: buttons, fields, cards                          |
| `--bs-border-radius-sm`   | radius | small buttons, badges                                        |
| `--bs-border-radius-lg`   | radius | what floats: dropdowns, dialogs                              |
| `--bs-border-radius-pill` | radius | tags                                                         |
| `--oep-shadow-sm`         | shadow | cards                                                        |
| `--oep-shadow-lg`         | shadow | overlays: dropdowns, dialogs, toasts                         |
| `--oep-shadow-rgb`        | rgb    | the tint of both shadows                                     |
| `--bs-font-sans-serif`    | font   | the font (a system stack, no web font)                       |
| `--bs-body-font-size`     | size   | text                                                         |
| `--oep-font-size-dense`   | size   | tables, badges, sidebars, buttons, fields                    |
| `--oep-heading-weight`    | weight | headings                                                     |
| `--oep-measure`           | width  | reading width for prose                                      |
| `--oep-content-width`     | width  | content column and header band, in steps by screen width     |
| `--oep-transition`        | motion | hover motion                                                 |

`--oep-content-width` changes at the theme's breakpoints; set at `:root` alone,
your value replaces every step. A web font is yours to load: add its
`@font-face` (or an `@import`) to your stylesheet and name it in
`--bs-font-sans-serif`.

Token names are a promise: when one has to be renamed, the old name keeps
working for one release and the changelog says so.

## Check your theme

Open `/styleguide/` on your instance. The component catalogue renders every
house component with your stylesheet applied, and its token table shows the
value each token has on your instance, so a colour you forgot or a twin you did
not set shows at a glance. `/styleguide/?tokens=bootstrap` shows the same page
with Bootstrap 5.2's stock values and **without** your stylesheet, which is the
baseline to compare against. The page is public, not indexed and linked from no
menu. How the catalogue works is in the
[design system](../../dev/frontend/design-system.md) guide.

## In a container image

The production image collects and compresses its static files while it is built,
so your files have to be in the image before that step runs, and the step has to
run again. Build a derived image:

```dockerfile
FROM ghcr.io/openenergyplatform/oeplatform-production:<version>

# Your static files go where collectstatic looks (STATICFILES_DIRS is /app/assets),
# your templates anywhere.
COPY instance/static/ /app/assets/instance/
COPY instance/templates/ /app/instance/templates/

# Read by securitysettings.py.default, at this build and when the container runs.
ENV OEP_INSTANCE_STYLESHEETS=instance/theme.css \
    OEP_INSTANCE_TEMPLATE_DIRS=/app/instance/templates

# The image's own build step, once more, now with your files.
RUN cp /app/oeplatform/securitysettings.py.default /app/oeplatform/securitysettings.py \
    && python manage.py collectstatic --noinput \
    && OEP_DEBUG=False python manage.py compress --force \
    && rm /app/oeplatform/securitysettings.py
```

`compress` runs with `OEP_DEBUG=False` because that is how the container runs:
static file names carry their content hash only with `DEBUG` off, and the
compressed bundles are keyed on those names. If you mount your own
`securitysettings.py` into the container instead of using the default one, set
`INSTANCE_STYLESHEETS` and `INSTANCE_TEMPLATE_DIRS` in it, to the same values
the build used.

## The deep path: rebuild the theme

Custom properties cover what the tokens name. Anything else Bootstrap computes
in Sass (its full shade scales, spacing, breakpoints) needs the theme rebuilt
from its source: change `theming/_variables.scss` and run `npm run build:theme`,
as the
[theming README](https://github.com/OpenEnergyPlatform/oeplatform/tree/develop/theming)
describes. That edits a tracked file, so it is a fork, and every upgrade
conflicts on the compiled stylesheet. Prefer the tokens wherever they reach.
