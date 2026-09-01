<!--
SPDX-FileCopyrightText: 2026 Open Energy Platform contributors

SPDX-License-Identifier: CC0-1.0
-->

# Account relocation (legacy → social login)

Operator guide for moving users from native (username/password) accounts to
social login (for example RegApp), including ownership transfer, email
verification, terms acceptance, and bulk deactivation of leftover native
accounts.

Detailed feature pages:

- [Social account linking](../social-account-linking/index.md)
- [User agreements](../user-agreements/index.md)
- [Content moderation](../content-moderation/index.md) (deactivation related to violations)

## Recommended rollout order

1. Deploy code (linking, transfer helpers, terms seeding).
2. Run migrations and seed terms: `python manage.py migrate` then
   `python manage.py create_default_terms`.
3. Let users reclaim legacy accounts via social login or the claim form
   (email challenge).
4. Optionally transfer remaining ownership with
   `python manage.py transfer_user_data` for support cases.
5. When ready, deactivate leftover native logins with
   `python manage.py deactivate_native_users` (always `--dry-run` first).

## Self-service: social account linking

The platform does **not** auto-link a social identity to a legacy local account.
It emails a confirmation link to the **legacy mailbox**. Only after that link is
opened is the social identity attached and the legacy user reactivated.

### Same email on social login

1. User authenticates with the social provider.
2. Adapter finds a local user with the same email and no linked provider.
3. `SocialAccountLinkToken` is stored; mail goes to the legacy address.
4. User lands on `/user/social-link/pending/`.
5. Opening `/user/social-link/confirm/<token>/` connects the social account,
   sets `is_active=True`, `is_native=False`, and logs the user in.

### Different email (claim form)

1. User already has a social-backed account.
2. Opens **Claim a legacy account** (`/user/social-link/claim/` or Settings).
3. Enters the legacy email → mail to that address.
4. On confirm: `transfer_user_ownership` moves data, reassigns `SocialAccount`,
   deactivates/renames the temporary account, logs in as the legacy user.

| URL | Purpose |
| --- | --- |
| `/user/social-link/pending/` | “Check your email” |
| `/user/social-link/confirm/<token>/` | Confirm ownership |
| `/user/social-link/claim/` | Enter a legacy email to claim |

| Setting | Purpose |
| ------- | ------- |
| `SOCIALACCOUNT_EMAIL_AUTHENTICATION` | `False` — no silent link |
| `SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT` | `False` |
| `SOCIAL_ACCOUNT_LINK_TOKEN_HOURS` | Token lifetime (default 48) |

Main code: `login/account_linking.py`, `login/adapters.py`,
`login/views_linking.py`, `login/user_transfer.py`.

## Terms and conditions after relocation

Authenticated users must accept active platform terms before using protected
pages. Docker startup seeds a default record if none exists:

```bash
python manage.py create_default_terms
```

Runs automatically from:

- `docker/docker-entrypoint.dev.sh`
- `docker/docker-entrypoint.sh`

Replace placeholder text in Django admin → **Terms and Conditions** before
production. Accept URL: `/terms/accept/`. Public legal text: `/legal/tou/`.

## Admin: transfer ownership between users

Moves tables/permissions, group memberships, scenario bundles, peer reviews,
OEKG modifications, metadata contributors, and cleans source tokens.

Preview:

```bash
python manage.py transfer_user_data \
  --source-name olduser \
  --target-name newuser \
  --deactivate-source \
  --dry-run
```

Apply (example with rename so username/email are freed):

```bash
python manage.py transfer_user_data \
  --source-name olduser \
  --target-name newuser \
  --deactivate-source \
  --rename-source
```

Users can also be selected with `--source-id` / `--target-id` or
`--source-email` / `--target-email`.

Optional skips: `--skip-metadata`, `--skip-peer-reviews`, `--skip-bundles`.

Implementation: `login/user_transfer.py` (shared with the claim flow) and
`login/management/commands/transfer_user_data.py`.

## Admin: deactivate leftover native users

Sets `is_active=False` for **active users with no linked social account**.
Does not delete uploaded data.

```bash
python manage.py deactivate_native_users --dry-run
python manage.py deactivate_native_users
```

See `login/management/commands/deactivate_native_users.py`.

## Manual test checklist

1. Seed terms: `python manage.py create_default_terms`
2. Create legacy user (`is_native=True`, optional `is_active=False`) with email A
3. Social-login with provider email A → pending page + mail → confirm → legacy
   active with social linked
4. New social user with email B → claim A → confirm → data on A, B deactivated
5. `transfer_user_data --dry-run` then a real transfer for a support case
6. `deactivate_native_users --dry-run` before any bulk deactivation
7. Log in as a user who never accepted terms → `/terms/accept/` then normal use
