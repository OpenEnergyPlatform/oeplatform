<!--
SPDX-FileCopyrightText: 2026 Open Energy Platform contributors

SPDX-License-Identifier: CC0-1.0
-->

AI generated

# Dataset reporting and user deactivation

This page describes how users report potentially illegal or prohibited dataset
content, how staff review those reports, and how user accounts can be
deactivated.

## Dataset reporting

Logged-in users can report a dataset from the table page. Submitting a report
temporarily blocks the dataset, notifies the uploader and the reporter, and
places the case in a staff moderation queue.

### Who can do what


| Role                                           | Access                                              |
| ---------------------------------------------- | --------------------------------------------------- |
| Logged-in user                                 | Report a dataset                                    |
| Table uploader (admin permission on the table) | Respond to an open report                           |
| Platform admin (`myuser.is_admin`)             | Review queue, restore or delete, warn or deactivate |




### User flow

1. Open a dataset page: `/database/tables/<table>/`
2. Click **Report data/content**
3. Edit the prefilled subject (includes the dataset name and id), choose a
  reason, and describe the issue
4. Submit the form

On submit the platform:

- Creates a `ContentReport` with a unique report ID
- Places a `ModerationHold` on the table (data access is blocked)
- Unpublishes the table if it was published
- Sends email to the moderation inbox, the uploader, and the reporter

The reporter cannot open a second report for the same dataset while one is still
open.

### Report ID

Each report gets a unique ID:

`RP00/{year}/{month}/{day}/{number}`

Example: `RP00/2026/08/18/1`

The number resets each day. The ID is shown in the queue, report pages, and all
related emails.

### Uploader response

The uploader is emailed a link to respond:

`/database/tables/<table>/report/<report_id>/respond/`

Their reply is stored on the report and emailed to the moderation inbox.

### Staff review

Platform admins open `/database/moderation/`.

After review they choose:


| Decision           | Effect                                                                                          |
| ------------------ | ----------------------------------------------------------------------------------------------- |
| No violation       | Clear the hold and restore the previous publish state. Reporter and uploader are notified.      |
| Violation (first)  | Delete the dataset. Create a warning for the uploader. Uploader and reporter are notified.      |
| Violation (repeat) | Delete the dataset. Deactivate the uploader (`is_active=False`) if they already have a warning. |


Account removal for a repeat violation is implemented as **deactivation**, not
hard deletion, so ownership records stay intact.

### Emails

Configure the inbox in `oeplatform/securitysettings.py`:

```python
CONTACT_ADDRESSES = {
    "technical": ["tech@example.org"],
    "other": ["other@example.org"],
    "moderation": ["moderation@example.org"],
}
```

If `moderation` is missing, mail falls back to `other`, then `technical`.


| Event               | Recipients                           |
| ------------------- | ------------------------------------ |
| New report          | Moderation inbox, uploader, reporter |
| Uploader responded  | Moderation inbox                     |
| No violation        | Uploader, reporter                   |
| Violation / warning | Uploader, reporter                   |
| Account deactivated | Uploader, reporter                   |


Templates live under `login/templates/mails/moderation_*.html`.

### Data access while blocked

API data reads and writes return HTTP 403 while a hold is active. Platform
admins can still access the table for review. The dataset page shows a
moderation banner instead of the data view.

### Main files


| Path                                                              | Role                                                       |
| ----------------------------------------------------------------- | ---------------------------------------------------------- |
| `dataedit/models.py`                                              | `ContentReport`, `ModerationHold`, `UserModerationWarning` |
| `dataedit/moderation.py`                                          | Create, hold, resolve, warn, deactivate                    |
| `dataedit/moderation_views.py`                                    | Report form, uploader response, staff queue                |
| `dataedit/moderation_mail.py`                                     | Notification emails                                        |
| `api/helper.py`                                                   | `check_moderation_block` / `check_data_restricted`         |
| `dataedit/migrations/0049_content_moderation.py`                  | Initial models                                             |
| `dataedit/migrations/0050_contentreport_public_id.py`             | Report ID field                                            |
| `dataedit/migrations/0051_contentreport_public_id_format.py`      | `RP00/…` format                                            |
| `dataedit/migrations/0052_contentreport_public_id_drop_hyphen.py` | ID without hyphen                                          |


Apply migrations:

```bash
python manage.py migrate dataedit
```



### URLs


| URL                                             | Purpose           |
| ----------------------------------------------- | ----------------- |
| `/database/tables/<table>/report/`              | Submit a report   |
| `/database/tables/<table>/report/<id>/respond/` | Uploader response |
| `/database/moderation/`                         | Staff queue       |
| `/database/moderation/<id>/`                    | Staff decision    |


---



## Deactivating users

Deactivation sets `myuser.is_active=False`. The user can no longer log in. Data
they uploaded is not deleted by the deactivation commands below.

There are two operational paths.

### Repeat content violation

Handled automatically in staff review (see above). The second confirmed
violation deactivates the table uploader and sends
`mails/moderation_account_deactivated.html`.

### Native login users (management command)

`login/management/commands/deactivate_native_users.py` deactivates **active
users who have no linked social account** (username/password signup, not
OpenID / OAuth).

It does **not** deactivate users who signed in through a social provider
(`SocialAccount` exists).

Preview:

```bash
python manage.py deactivate_native_users --dry-run
```

Apply:

```bash
python manage.py deactivate_native_users
```

The command prints the usernames and emails it will change, then sets
`is_active=False` for those users.

Use `--dry-run` first on production.

### Related command: transfer then deactivate

To move a user's tables, permissions, reviews, and related data to another
account before deactivating them:

```bash
python manage.py transfer_user_data \
  --source-name olduser \
  --target-name newuser \
  --deactivate-source \
  --dry-run
```

`--rename-source` can be used with `--deactivate-source` to free the old
username and email.

See `login/management/commands/transfer_user_data.py`.