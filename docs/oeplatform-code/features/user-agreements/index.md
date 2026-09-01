<!--
SPDX-FileCopyrightText: 2026 Open Energy Platform contributors

SPDX-License-Identifier: CC0-1.0
-->

# User agreements (terms and conditions)

This page describes how the Open Energy Platform requires authenticated users to
accept the platform terms and conditions before using the site.

If you are migrating legacy accounts to social login, also see
[Account relocation](../account-relocation/Relocation_Readme.md).

The feature is built on
[`django-termsandconditions`](https://github.com/cyface/django-termsandconditions)
and is **enabled by default** once an active terms record exists in the
database.

## Behaviour

| Who | Effect |
| --- | --- |
| Anonymous visitor | No redirect; public pages stay reachable |
| Authenticated user who has not accepted the active terms | Redirected to `/terms/accept/` until they accept |
| Authenticated user who already accepted | Normal access |
| Superusers | Follow the same rules unless excluded via package settings |

Acceptance is stored once per user and terms version
(`UserTermsAndConditions`). Publishing a new active version of the same slug
prompts users again.

### User flow

1. User signs in (native account or social login).
2. On the next protected request, middleware checks for active terms the user
   has not accepted.
3. If any remain, the user is redirected to `/terms/accept/`.
4. After clicking **Accept**, the acceptance is stored and the user continues to
   the original URL.

### Public terms of use page

The static legal text remains available at `/legal/tou/` (Django name
`base:legal-tou`). That page is informational. The mandatory acceptance flow
uses the `termsandconditions` records managed in Django admin.

## Enabling and seeding

The app, middleware, and URL routes are always registered in settings. The
redirect only runs when at least one `TermsAndConditions` row has
`date_active` set.

Docker startup seeds a default active record if none exists:

```bash
python manage.py create_default_terms
```

This runs automatically in:

- `docker/docker-entrypoint.dev.sh` (development)
- `docker/docker-entrypoint.sh` (production image)

The command is idempotent: if an active record for `DEFAULT_TERMS_SLUG`
(`site-terms`) already exists, it skips creation.

Replace the placeholder text in Django admin under **Terms and Conditions**
before going to production.

## Configuration

Relevant settings in `oeplatform/settings.py`:

| Setting | Purpose |
| ------- | ------- |
| `TERMS_BASE_TEMPLATE` | Template shell for the accept page |
| `ACCEPT_TERMS_PATH` | Accept URL (`/terms/accept/`) |
| `DEFAULT_TERMS_SLUG` | Slug used by `create_default_terms` |
| `TERMS_EXCLUDE_URL_PREFIX_LIST` | Path prefixes skipped by the middleware |

Excluded prefixes include `/admin`, `/terms`, `/accounts`, `/static`,
`/captcha`, `/api`, and `/media`, so login, signup, static assets, and the REST
API keep working without an acceptance redirect.

Package docs:
[django-termsandconditions](https://django-termsandconditions.readthedocs.io/).

## Main files

| Path | Role |
| ---- | ---- |
| `oeplatform/settings.py` | App, middleware, terms settings |
| `oeplatform/urls.py` | Mounts `/terms/` |
| `login/templates/termsandconditions/base.html` | OEP-styled base template |
| `login/templates/termsandconditions/tc_accept_terms.html` | Accept page |
| `login/management/commands/create_default_terms.py` | Seeds default active terms |
| `base/templates/base/terms_of_use.html` | Public legal ToU page |
| `requirements.txt` | Pins `django-termsandconditions==2.0.12` |

Apply package migrations after install or upgrade:

```bash
python manage.py migrate
```

## URLs

| URL | Purpose |
| --- | ------- |
| `/terms/accept/` | Accept outstanding terms |
| `/terms/...` | Package views (view, print, etc.) |
| `/legal/tou/` | Public terms of use (static content) |

## Updating terms

1. Open Django admin → **Terms and Conditions**.
2. Create a new version (same or new slug) and set `date_active`.
3. Users who have not accepted that active version are redirected on their next
   visit.

To force a single user to accept again during testing, delete their
`UserTermsAndConditions` rows for that terms record.

## Manual test checklist

1. Ensure default terms exist: `python manage.py create_default_terms`
2. Log in as a normal user who has never accepted
3. Confirm redirect to `/terms/accept/`
4. Accept and confirm you can browse again
5. Log out / log in and confirm you are not prompted again
6. Call an API endpoint with a token and confirm it is not redirected to HTML
   terms pages
