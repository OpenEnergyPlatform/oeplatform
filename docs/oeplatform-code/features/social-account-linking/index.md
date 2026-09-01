<!--
SPDX-FileCopyrightText: 2026 Open Energy Platform contributors

SPDX-License-Identifier: CC0-1.0
-->

# Social account linking (legacy ownership email)

When a user signs in with a social provider (for example RegApp) and an existing
local “legacy” account may belong to them, the platform does **not** link the
accounts automatically. Instead it sends a confirmation email to the **legacy
account address**. Only after that link is opened is the social identity attached.

For the full operator runbook (transfer commands, bulk deactivation, terms
seeding), see [Account relocation](../account-relocation/Relocation_Readme.md).

## Flows

### Same email on social login

1. User authenticates with the social provider.
2. `SocialAccountAdapter.pre_social_login` finds a local user with the same email
   who does not already have that provider linked.
3. A `SocialAccountLinkToken` is stored (provider, uid, serialized social login).
4. Mail goes to the legacy email with `/user/social-link/confirm/<token>/`.
5. User sees “check your email” (`/user/social-link/pending/`).
6. On confirm: social account is connected to the legacy user, `is_active=True`,
   `is_native=False`, and the user is logged in.

Automatic allauth email authentication is **disabled** so this challenge cannot
be skipped.

### Different email (claim form)

1. User already has a social-backed account (different email).
2. Opens **Claim a legacy account** (`/user/social-link/claim/` or Settings).
3. Enters the legacy email.
4. Mail is sent to that address.
5. On confirm: ownership data is moved with `transfer_user_ownership`, the
   `SocialAccount` is reassigned to the legacy user, the temporary account is
   deactivated/renamed, and the user is logged in as the legacy account.

## Main files

| Path | Role |
| ---- | ---- |
| `login/account_linking.py` | Challenge start/complete helpers |
| `login/adapters.py` | Intercept matching social logins |
| `login/views_linking.py` | Pending, confirm, claim views |
| `login/user_transfer.py` | Shared ownership transfer |
| `login/mail.py` | `send_social_account_link_mail` |
| `login/models.py` | `SocialAccountLinkToken` |

## Settings

| Setting | Purpose |
| ------- | ------- |
| `SOCIALACCOUNT_EMAIL_AUTHENTICATION` | `False` — no silent link |
| `SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT` | `False` |
| `SOCIAL_ACCOUNT_LINK_TOKEN_HOURS` | Token lifetime (default 48) |

## URLs

| URL | Purpose |
| --- | ------- |
| `/user/social-link/pending/` | “Check your email” page |
| `/user/social-link/confirm/<token>/` | Confirm ownership |
| `/user/social-link/claim/` | Enter a legacy email to claim |

## Manual test checklist

1. Create a legacy user (`is_native=True`, optional `is_active=False`) with email A.
2. Social-login with a provider that returns email A → expect pending page + mail.
3. Open the confirm link → logged in as legacy, social account attached, active.
4. Create a social user with email B, claim email A → mail to A → confirm merges
   data onto A and deactivates B.
