## What and why

<!--
What does this PR change, and why? Sum up the decisions from the issue or meeting
so that a reader does not have to go back through the whole discussion.
-->

Closes #

## What changed

<!--
The changes, grouped the way a reviewer will read them. Name the files or
modules where the work is, and anything users or API clients will notice.
-->

## How it was tested

<!--
Tests added or changed, which suites you ran locally and their result, and any
manual checks (URL, browser, data used). If something could not be tested, say
so and why.
-->

## Deploy notes

<!--
Anything that has to happen when this is deployed: Django migrations (name
them), alembic migrations for the OEDB, new settings or environment variables,
management commands to run, files to fetch. Write "None" if nothing.
-->

## For reviewers

<!--
Help the reviewer spend their time well. Fill in what applies, delete the rest.
-->

- **Start reading at:**
- **Decisions I'd like checked:**
- **Not sure about:**
- **To try it locally:**
- **Deliberately left out:**

## Checklist

### Author

- [ ] 🐙 Followed the workflow in
      [CONTRIBUTING.md](https://github.com/OpenEnergyPlatform/oeplatform/blob/develop/CONTRIBUTING.md)
- [ ] 📝 Added a line to
      [`versions/changelogs/current.md`](https://github.com/OpenEnergyPlatform/oeplatform/blob/develop/versions/changelogs/current.md)
      under the right heading, ending with the PR number `(#…)`
- [ ] 📙 Updated the
      [documentation](https://openenergyplatform.github.io/oeplatform/), or none
      is needed
- [ ] 🧪 Added or updated tests, and the test suite passes
- [ ] 🔌 Changed an API route or serializer? Regenerated the API reference:
      `python manage.py spectacular --validate --file docs/oeplatform-code/web-api/openapi.yaml`
- [ ] 🤖 Used AI tools? Disclosed any changes you do not fully understand, as
      the
      [AI covenant](https://github.com/rl-institut/super-repo/blob/develop/AI_COVENANT.md)
      asks
- [ ] 👀 Assigned a reviewer

### Reviewer

- [ ] 🐙 Followed the
      [reviewer guidelines](https://github.com/rl-institut/super-repo/blob/production/CONTRIBUTING.md#40--let-someone-else-review-your-pr)
- [ ] 💻 Checked out the branch and ran it
- [ ] 💬 Gave feedback, and some appreciation for the work done
