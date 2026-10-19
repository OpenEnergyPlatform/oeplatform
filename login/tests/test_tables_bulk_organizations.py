"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

The bulk bar's Organization actions (#2568, spec #2551, WF-08 decisions
11-15 and 18): sharing a selection with one of the user's Organizations at a
role, and removing an Organization from a selection, as seen through HTTP.
The dashboard reaches the permission service's two bulk writes
(``login.table_roles``) through the table action service, so the preflight,
the ceiling, the row lock and the whole-request refusal are the ones every
bulk action has.

Assertions are on what a preflight leaves out, leaves unchanged and names,
the counts it states, what the database holds afterwards, the status and
which response headers and log lines came back; never on seconds.
"""  # noqa: 501

import re
from unittest import mock

from django.db import connection
from django.test.utils import CaptureQueriesContext

from api.services import table_actions
from login import table_roles
from login.list_views import RECHECKED
from login.models import (
    ADMIN_PERM,
    DELETE_PERM,
    WRITE_PERM,
    GroupPermission,
    Membership,
    UserPermission,
)
from login.tests.helpers import HTMX, make_user
from login.tests.test_tables_bulk_delete_datasets import BulkCase
from modelview.tests.html import element_markup, element_with_id, text

SHARE = table_actions.ORGANIZATION_SHARE
REMOVE = table_actions.ORGANIZATION_REMOVE
PERMISSION_LOG = "oeplatform.table_permissions"


class OrganizationCase(BulkCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.colleague = make_user("BulkOrgColleague")
        cls.other_admin = make_user("BulkOrgOtherAdmin")

    def team(self, name="Team", members=(), member=True):
        """An Organization, the user in it unless ``member`` is False, plus
        ``members``."""
        organization = self.organization(name, member=member)
        for user in members:
            Membership.objects.create(user=user, group=organization)
        return organization

    def grant(self, organization, table, level):
        return GroupPermission.objects.create(
            holder=organization, table=table, level=level
        )

    def grants(self, organization, *names):
        """``organization``'s level on each of ``names`` (None: no grant)."""
        held = dict(
            GroupPermission.objects.filter(
                holder=organization, table__name__in=names
            ).values_list("table__name", "level")
        )
        return {name: held.get(name) for name in names}

    def unchanged(self, check):
        return [table.name for table in check.unchanged]

    def log_lines(self, logs):
        return sorted(record.getMessage() for record in logs.records)


class BulkBarTests(OrganizationCase):
    def test_the_organization_actions_sit_before_delete(self):
        self.draft("t_bar")
        html = self.get().content.decode()
        order = [
            html.index(f'id="bulk-{verb}"')
            for verb in (table_actions.DATASET_REMOVE, SHARE, REMOVE, "delete")
        ]
        self.assertEqual(order, sorted(order))
        for verb in (SHARE, REMOVE):
            with self.subTest(verb=verb):
                button = element_with_id(html, f"bulk-{verb}")
                self.assertIn(f'hx-post="{self.check_path(verb)}"', button)
                self.assertNotEqual(element_with_id(html, f"bulk-menu-{verb}"), "")

    def test_the_ceilings_are_stated(self):
        self.draft("t_c1")
        self.draft("t_c2")
        self.team()
        for action, words in (
            (SHARE, "Sharing with an organization"),
            (REMOVE, "Removing an organization"),
        ):
            with self.subTest(action=action):
                html = self.html(self.joined_preflight(action, "t_c1", "t_c2"))
                self.assertEqual(
                    text(element_markup(html, "table-action-ceiling-rule")),
                    f"{words} takes at most "
                    f"{table_actions.CEILINGS[action]:,} tables at a time.",
                )

    def test_over_the_ceiling_nothing_is_read_or_offered(self):
        names = [f"t_over_{i}" for i in range(3)]
        for name in names:
            self.draft(name)
        self.team()
        with mock.patch.dict(table_actions.CEILINGS, {SHARE: 2}):
            response = self.joined_preflight(SHARE, *names)
        self.assertContains(
            response,
            "Sharing with an organization takes at most 2 tables at a time; "
            "you selected 3.",
        )
        html = self.html(response)
        self.assertEqual(element_with_id(html, "action-organization"), "")
        self.assertEqual(element_with_id(html, "table-action-confirm"), "")


class SharePreflightTests(OrganizationCase):
    def test_it_offers_my_organizations_with_their_member_counts(self):
        self.draft("t_s")
        self.team("Alpha", members=[self.colleague])
        self.team("Beta")
        self.team("Strangers", member=False)
        response = self.joined_preflight(SHARE, "t_s")
        check = response.context["preflight"]
        self.assertEqual([o.name for o in check.organizations], ["Alpha", "Beta"])
        self.assertIsNone(check.organization)
        self.assertFalse(check.confirmable)
        select = element_markup(self.html(response), "action-organization")
        self.assertIn("Alpha (2 members)", text(select))
        self.assertIn("Beta (1 member)", text(select))
        self.assertNotIn("Strangers", select)

    def test_the_roles_offered_stop_at_data_maintainer(self):
        self.draft("t_roles")
        self.team()
        check = self.joined_preflight(SHARE, "t_roles").context["preflight"]
        html = self.html(self.joined_preflight(SHARE, "t_roles"))
        self.assertEqual(check.level, WRITE_PERM)  # the lowest, until chosen
        for level in (WRITE_PERM, DELETE_PERM):
            self.assertNotEqual(element_with_id(html, f"action-level-{level}"), "")
        self.assertEqual(element_with_id(html, f"action-level-{ADMIN_PERM}"), "")

    def test_tables_without_table_admin_are_left_out(self):
        self.draft("t_admin")
        self.draft("t_maintainer", level=DELETE_PERM)
        self.draft("t_strangers", level=None)
        team = self.team()
        check = self.joined_preflight(
            SHARE,
            "t_admin",
            "t_maintainer",
            "t_strangers",
            organization=team.pk,
        ).context["preflight"]
        self.assertEqual(check.names, ["t_admin"])
        self.assertEqual(
            self.left_out(check),
            {
                "Only Table admins can share a table": ["t_maintainer"],
                table_actions.NOT_YOURS: ["t_strangers"],
            },
        )

    def test_a_role_held_already_or_higher_leaves_the_table_unchanged(self):
        """Raise-only: Data maintainer is not lowered to Data editor, an old
        Admin grant is not touched, and both are named, not left out."""
        team = self.team("Team", members=[self.colleague])
        self.grant(team, self.draft("t_maintains"), DELETE_PERM)
        self.grant(team, self.draft("t_old_admin"), ADMIN_PERM)
        self.grant(team, self.draft("t_edits"), WRITE_PERM)
        self.draft("t_none")
        response = self.joined_preflight(
            SHARE,
            "t_maintains",
            "t_old_admin",
            "t_edits",
            "t_none",
            organization=team.pk,
            level=DELETE_PERM,
        )
        check = response.context["preflight"]
        self.assertEqual(check.names, ["t_edits", "t_none"])
        self.assertEqual(self.unchanged(check), ["t_maintains", "t_old_admin"])
        self.assertEqual(check.left_out, [])
        self.assertTrue(check.confirmable)
        html = self.html(response)
        unchanged = text(element_markup(html, "table-action-unchanged"))
        self.assertIn(
            "“Team” holds Data maintainer or more there already (2)", unchanged
        )
        self.assertIn("t_old_admin", unchanged)
        self.assertEqual(
            text(element_markup(html, "table-action-members")),
            "“Team” has 2 members. Each of them gets Data maintainer on these tables.",
        )
        self.assertEqual(
            text(element_markup(html, "table-action-recheck")),
            "2 of 4 tables will be shared with “Team” as Data maintainer.",
        )
        self.assertIn('name="tables" value="t_edits,t_none"', html)

    def test_everything_unchanged_leaves_nothing_to_confirm(self):
        team = self.team()
        self.grant(team, self.draft("t_full"), DELETE_PERM)
        response = self.joined_preflight(
            SHARE, "t_full", organization=team.pk, level=WRITE_PERM
        )
        check = response.context["preflight"]
        self.assertEqual(self.unchanged(check), ["t_full"])
        self.assertFalse(check.confirmable)
        html = self.html(response)
        self.assertEqual(
            text(element_markup(html, "table-action-nothing")),
            "Nothing to share with “Team”.",
        )
        self.assertEqual(element_with_id(html, "table-action-confirm"), "")

    def test_choosing_re_checks_the_whole_selection(self):
        """What the selects send: the form, with the eligible ``tables``
        and the whole ``selection``; a role chosen anew changes what is
        unchanged, and the Table the role gate left out is still named."""
        team = self.team()
        self.grant(team, self.draft("t_r_edits"), WRITE_PERM)
        self.draft("t_r_new")
        self.draft("t_r_theirs", level=WRITE_PERM)
        opened = self.html(self.joined_preflight(SHARE, "t_r_edits", "t_r_new"))
        self.assertIn(
            f'hx-post="{self.check_path(SHARE)}"',
            element_with_id(opened, "table-action-chooser"),
        )
        selection = "t_r_edits,t_r_new,t_r_theirs"
        checks = {}
        for level in (WRITE_PERM, DELETE_PERM):
            response = self.client.post(
                self.check_path(SHARE),
                {
                    "tables": "t_r_edits,t_r_new",
                    "selection": selection,
                    "organization": team.pk,
                    "level": level,
                },
                **HTMX,
            )
            self.assertEqual(response.status_code, 200)
            checks[level] = response.context["preflight"]
        self.assertEqual(checks[WRITE_PERM].names, ["t_r_new"])
        self.assertEqual(self.unchanged(checks[WRITE_PERM]), ["t_r_edits"])
        self.assertEqual(checks[DELETE_PERM].names, ["t_r_edits", "t_r_new"])
        self.assertEqual(self.unchanged(checks[DELETE_PERM]), [])
        for check in checks.values():
            self.assertEqual(
                self.left_out(check),
                {"Only Table admins can share a table": ["t_r_theirs"]},
            )

    def test_an_organization_i_do_not_belong_to_cannot_be_chosen(self):
        self.draft("t_foreign")
        foreign = self.team("Foreign", member=False)
        check = self.joined_preflight(
            SHARE, "t_foreign", organization=foreign.pk
        ).context["preflight"]
        self.assertIsNone(check.organization)
        self.assertFalse(check.confirmable)

    def test_without_an_organization_the_dialog_says_why(self):
        self.draft("t_alone")
        response = self.joined_preflight(SHARE, "t_alone")
        self.assertIn(
            "You are not a member of any organization",
            text(element_markup(self.html(response), "table-action-no-organization")),
        )
        self.assertFalse(response.context["preflight"].confirmable)

    def test_the_preflight_costs_the_same_whatever_the_batch(self):
        team = self.team()

        def queries(count):
            names = [f"t_cost_{count}_{i}" for i in range(count)]
            for i, name in enumerate(names):
                table = self.draft(name)
                if i % 2:
                    self.grant(team, table, DELETE_PERM)
            params = {"organization": team.pk, "level": DELETE_PERM}
            self.joined_preflight(SHARE, *names, **params)  # warms the Site cache
            with CaptureQueriesContext(connection) as captured:
                self.joined_preflight(SHARE, *names, **params)
            return len(captured)

        self.assertEqual(queries(2), queries(20))


class ShareTests(OrganizationCase):
    def test_a_batch_is_shared_in_one_request_one_line_per_table_written(self):
        team = self.team("Team", members=[self.colleague])
        self.grant(team, self.draft("t_raise"), WRITE_PERM)
        self.grant(team, self.draft("t_keep"), ADMIN_PERM)
        self.draft("t_add", title="Added")
        with self.assertLogs(PERMISSION_LOG, "INFO") as logs:
            with self.captureOnCommitCallbacks(execute=True):
                response = self.joined_run(
                    SHARE,
                    "t_raise",
                    "t_keep",
                    "t_add",
                    organization=team.pk,
                    level=DELETE_PERM,
                )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(
            self.grants(team, "t_raise", "t_keep", "t_add"),
            {"t_raise": DELETE_PERM, "t_keep": ADMIN_PERM, "t_add": DELETE_PERM},
        )
        lines = self.log_lines(logs)
        self.assertEqual(len(lines), 2)
        self.assertRegex(
            lines[0],
            rf"^table_permission_write table=t_add holder=org:{team.pk} "
            rf"action=add before=- after={DELETE_PERM} by={self.user.pk} "
            r"via=dashboard$",
        )
        self.assertIn(
            f"table=t_raise holder=org:{team.pk} action=change "
            f"before={WRITE_PERM} after={DELETE_PERM}",
            lines[1],
        )
        detail = self.trigger(response, "tables-changed")
        self.assertTrue(
            detail["message"].startswith(
                "Shared 2 tables with “Team” as Data maintainer."
            ),
            detail["message"],
        )
        self.assertIn("“Added”", detail["tables"])
        self.assertNotIn("gone", detail)

    def test_one_table_is_named_in_the_message_and_keeps_its_focus(self):
        team = self.team()
        table = self.draft("t_one", title="Only one")
        response = self.joined_run(SHARE, "t_one", organization=team.pk, level=4)
        self.assertEqual(response.status_code, 204)
        detail = self.trigger(response, "tables-changed")
        self.assertEqual(
            detail["message"], "Shared “Only one” with “Team” as Data editor."
        )
        self.assertEqual(detail["focus"], f"menu-{table.pk}")

    def test_a_table_without_table_admin_refuses_the_whole_request(self):
        """A stale page still naming it: 403, nothing written, and the
        refusal names it."""
        team = self.team()
        self.draft("t_ok")
        self.draft("t_lowered", level=DELETE_PERM)
        with self.assertNoLogs(PERMISSION_LOG):
            with self.captureOnCommitCallbacks(execute=True):
                response = self.joined_run(
                    SHARE, "t_ok", "t_lowered", organization=team.pk, level=4
                )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            self.grants(team, "t_ok", "t_lowered"), dict.fromkeys(("t_ok", "t_lowered"))
        )
        message = self.trigger(response, "tables-refused")["message"]
        self.assertIn("Only Table admins can share a table", message)
        self.assertIn("t_lowered", message)
        self.assertEqual(response.context["preflight"].names, ["t_ok"])

    def test_a_name_that_is_not_mine_is_refused_403_too(self):
        team = self.team()
        self.draft("t_mine")
        response = self.joined_run(
            SHARE, "t_mine", "t_no_such", organization=team.pk, level=4
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.grants(team, "t_mine"), {"t_mine": None})

    def test_admin_or_a_stranger_organization_is_an_unusable_parameter(self):
        team = self.team()
        foreign = self.team("Foreign", member=False)
        self.draft("t_p")
        for params, field in (
            ({"organization": team.pk, "level": ADMIN_PERM}, "level"),
            ({"organization": team.pk, "level": "x"}, "level"),
            ({"organization": foreign.pk, "level": WRITE_PERM}, "organization"),
            ({"organization": "", "level": WRITE_PERM}, "organization"),
        ):
            with self.subTest(params=params):
                response = self.joined_run(SHARE, "t_p", **params)
                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.context["errors"])
                self.assertNotIn("HX-Trigger", response)
        self.assertEqual(GroupPermission.objects.count(), 0)

    def test_a_failure_part_way_writes_nothing(self):
        team = self.team()
        names = ["t_part_1", "t_part_2", "t_part_3"]
        for name in names:
            self.draft(name)
        real = table_roles._write
        calls = []

        def write(*args):
            calls.append(args)
            if len(calls) == 2:
                raise RuntimeError("the database went away")
            return real(*args)

        with mock.patch.object(table_roles, "_write", write):
            with self.assertRaises(RuntimeError):
                self.joined_run(SHARE, *names, organization=team.pk, level=4)
        self.assertEqual(GroupPermission.objects.count(), 0)

    def test_a_confirmation_checked_against_another_role_runs_nothing(self):
        """Confirmed between choosing another role and its re-check coming
        back: nothing is written, and the dialog shows the role sent."""
        team = self.team()
        self.grant(team, self.draft("t_q_edits"), WRITE_PERM)
        self.draft("t_q_new")
        response = self.client.post(
            self.action_path(SHARE),
            {
                "tables": "t_q_new",
                "selection": "t_q_edits,t_q_new",
                "organization": team.pk,
                "level": DELETE_PERM,
                "previewed": f"{team.pk},{WRITE_PERM}",
            },
            **HTMX,
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("HX-Trigger", response)
        self.assertEqual(response.context["notice"], RECHECKED)
        self.assertEqual(
            self.grants(team, "t_q_edits", "t_q_new"),
            {"t_q_edits": WRITE_PERM, "t_q_new": None},
        )
        check = response.context["preflight"]
        self.assertEqual(check.level, DELETE_PERM)
        self.assertEqual(check.names, ["t_q_edits", "t_q_new"])
        self.assertIn(
            f'name="previewed" value="{team.pk},{DELETE_PERM}"', self.html(response)
        )

    def test_a_confirmation_checked_against_its_own_choice_runs(self):
        team = self.team()
        self.draft("t_same")
        response = self.client.post(
            self.action_path(SHARE),
            {
                "tables": "t_same",
                "selection": "t_same",
                "organization": team.pk,
                "level": WRITE_PERM,
                "previewed": f"{team.pk},{WRITE_PERM}",
            },
            **HTMX,
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.grants(team, "t_same"), {"t_same": WRITE_PERM})


class RemovePreflightTests(OrganizationCase):
    def test_it_offers_the_organizations_holding_a_role_there(self):
        held = self.team("Held", member=False)
        mine = self.team("Mine", members=[self.colleague])
        self.team("Elsewhere")
        a, b = self.draft("t_a"), self.draft("t_b")
        self.grant(held, a, WRITE_PERM)
        self.grant(mine, b, DELETE_PERM)
        check = self.joined_preflight(REMOVE, "t_a", "t_b").context["preflight"]
        self.assertEqual([o.name for o in check.organizations], ["Held", "Mine"])
        self.assertEqual([o.members for o in check.organizations], [0, 2])
        self.assertIsNone(check.organization)
        self.assertFalse(check.confirmable)

    def test_the_only_choice_is_chosen_and_tables_it_is_not_on_left_out(self):
        team = self.team("Team", member=False)
        self.grant(team, self.draft("t_on"), WRITE_PERM)
        self.draft("t_off")
        check = self.joined_preflight(REMOVE, "t_on", "t_off").context["preflight"]
        self.assertEqual(check.organization, team)
        self.assertEqual(check.names, ["t_on"])
        self.assertEqual(
            self.left_out(check), {"“Team” holds no role on it": ["t_off"]}
        )

    def test_an_old_admin_grant_that_is_the_only_admin_is_left_out(self):
        """Its only Admin: left out and named. With a user or another
        Organization holding Admin as well it can go."""
        team = self.team("Team")
        other = self.team("Other", member=False)
        only = self.draft("t_only", level=None)
        self.grant(team, only, ADMIN_PERM)
        with_user = self.draft("t_with_user", level=None)
        self.grant(team, with_user, ADMIN_PERM)
        UserPermission.objects.create(
            holder=self.other_admin, table=with_user, level=ADMIN_PERM
        )
        with_org = self.draft("t_with_org", level=None)
        self.grant(team, with_org, ADMIN_PERM)
        self.grant(other, with_org, ADMIN_PERM)
        check = self.joined_preflight(
            REMOVE, "t_only", "t_with_user", "t_with_org", organization=team.pk
        ).context["preflight"]
        self.assertEqual(check.names, ["t_with_user", "t_with_org"])
        self.assertEqual(
            self.left_out(check),
            {
                "“Team”'s Admin is the only Admin there. Give someone Admin "
                "there first": ["t_only"]
            },
        )

    def test_tables_without_table_admin_are_left_out(self):
        team = self.team("Team", member=False)
        self.grant(team, self.draft("t_admin"), WRITE_PERM)
        self.grant(team, self.draft("t_editor", level=WRITE_PERM), WRITE_PERM)
        check = self.joined_preflight(
            REMOVE, "t_admin", "t_editor", organization=team.pk
        ).context["preflight"]
        self.assertEqual(check.names, ["t_admin"])
        self.assertEqual(
            self.left_out(check),
            {"Only Table admins can remove an organization": ["t_editor"]},
        )

    def test_one_member_is_not_called_each_of_them(self):
        team = self.team("Solo")  # the user is its only member
        self.grant(team, self.draft("t_solo"), WRITE_PERM)
        for action, verb in ((SHARE, "gets Data maintainer on"), (REMOVE, "loses")):
            with self.subTest(action=action):
                html = self.html(
                    self.joined_preflight(
                        action, "t_solo", organization=team.pk, level=DELETE_PERM
                    )
                )
                members = text(element_markup(html, "table-action-members"))
                self.assertTrue(
                    members.startswith(f"“Solo” has 1 member. That member {verb}"),
                    members,
                )

    def test_the_tables_i_would_lose_are_named_with_the_member_count(self):
        """The user is a Table admin on ``t_lose`` only through the old
        Admin grant of the Organization (another user holds direct Admin,
        so the guard does not fire); on ``t_keep`` they hold a role of their
        own as well."""
        team = self.team("Team", members=[self.colleague])
        lose = self.draft("t_lose", title="Lost one", level=None)
        self.grant(team, lose, ADMIN_PERM)
        UserPermission.objects.create(
            holder=self.other_admin, table=lose, level=ADMIN_PERM
        )
        self.grant(team, self.draft("t_keep"), WRITE_PERM)
        response = self.joined_preflight(
            REMOVE, "t_lose", "t_keep", organization=team.pk
        )
        check = response.context["preflight"]
        self.assertEqual(check.names, ["t_lose", "t_keep"])
        self.assertEqual(
            [t.name for t in check.consequences["lose_access"]], ["t_lose"]
        )
        html = self.html(response)
        self.assertIn(
            "Lost one", text(element_markup(html, "table-action-lose-access"))
        )
        self.assertIn(
            'value="t_lose,"', element_with_id(html, "table-action-lose-access-names")
        )
        self.assertEqual(
            text(element_markup(html, "table-action-members")),
            "“Team” has 2 members. Each of them loses the access it gives them "
            "to these tables.",
        )
        self.assertEqual(
            text(element_markup(html, "table-action-recheck")),
            "“Team” will be removed from 2 of 2 tables.",
        )


class LoseAdminTests(OrganizationCase):
    """Losing one's own Admin takes a confirmation, as it does for one
    Table: here the user keeps a direct Data editor grant, so the Table
    stays on the dashboard, but their Admin came through the Organization's
    old Admin grant (another user holds direct Admin, so the guard does not
    fire)."""

    def setUp(self):
        super().setUp()
        self.team_ = self.team("Team")
        table = self.draft("t_demoted", title="Demoted", level=WRITE_PERM)
        self.grant(self.team_, table, ADMIN_PERM)
        UserPermission.objects.create(
            holder=self.other_admin, table=table, level=ADMIN_PERM
        )

    def test_the_dialog_names_it_apart_from_the_tables_i_would_lose(self):
        response = self.joined_preflight(
            REMOVE, "t_demoted", organization=self.team_.pk
        )
        consequences = response.context["preflight"].consequences
        self.assertEqual(consequences["lose_access"], [])
        self.assertEqual([t.name for t in consequences["lose_admin"]], ["t_demoted"])
        html = self.html(response)
        self.assertIn("Demoted", text(element_markup(html, "table-action-lose-admin")))
        self.assertEqual(element_markup(html, "table-action-lose-access"), "")
        self.assertIn(
            'value="t_demoted,"',
            element_with_id(html, "table-action-lose-access-names"),
        )

    def test_unconfirmed_it_is_refused_and_confirmed_it_is_done(self):
        refused = self.joined_run(REMOVE, "t_demoted", organization=self.team_.pk)
        self.assertEqual(refused.status_code, 409)
        self.assertEqual(
            self.grants(self.team_, "t_demoted"), {"t_demoted": ADMIN_PERM}
        )
        done = self.joined_run(
            REMOVE, "t_demoted", organization=self.team_.pk, lose_access="t_demoted"
        )
        self.assertEqual(done.status_code, 204)
        self.assertEqual(self.grants(self.team_, "t_demoted"), {"t_demoted": None})
        detail = self.trigger(done, "tables-changed")
        self.assertNotIn("gone", detail)  # it stays on the dashboard
        self.assertIn("t_demoted", self.names())


class RemoveTests(OrganizationCase):
    def test_a_batch_is_removed_in_one_request_one_line_per_table(self):
        team = self.team("Team", member=False)
        self.grant(team, self.draft("t_x"), WRITE_PERM)
        self.grant(team, self.draft("t_y"), DELETE_PERM)
        with self.assertLogs(PERMISSION_LOG, "INFO") as logs:
            with self.captureOnCommitCallbacks(execute=True):
                response = self.joined_run(REMOVE, "t_x", "t_y", organization=team.pk)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.grants(team, "t_x", "t_y"), {"t_x": None, "t_y": None})
        lines = self.log_lines(logs)
        self.assertEqual(
            [
                re.search(r"action=(\w+) before=(\S+) after=(\S+)", line).groups()
                for line in lines
            ],
            [("remove", str(WRITE_PERM), "-"), ("remove", str(DELETE_PERM), "-")],
        )
        self.assertTrue(all(line.endswith("via=dashboard") for line in lines))
        detail = self.trigger(response, "tables-changed")
        self.assertTrue(detail["message"].startswith("Removed “Team” from 2 tables."))
        self.assertNotIn("gone", detail)

    def test_tables_i_lose_leave_the_dashboard(self):
        team = self.team("Team")
        lose = self.draft("t_gone", title="Gone", level=None)
        self.grant(team, lose, ADMIN_PERM)
        UserPermission.objects.create(
            holder=self.other_admin, table=lose, level=ADMIN_PERM
        )
        self.grant(team, self.draft("t_stays"), WRITE_PERM)
        response = self.joined_run(
            REMOVE, "t_gone", "t_stays", organization=team.pk, lose_access="t_gone"
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(
            self.grants(team, "t_gone", "t_stays"), {"t_gone": None, "t_stays": None}
        )
        detail = self.trigger(response, "tables-changed")
        self.assertEqual(detail["gone"], ["t_gone"])
        self.assertEqual(
            detail["message"],
            "Removed “Team” from 2 tables. You no longer have access to 1 of them.",
        )
        self.assertNotIn("t_gone", self.names())

    def test_losing_a_table_the_dialog_did_not_name_refuses_the_request(self):
        """The dialog named no losses (``lose_access`` empty), but by the
        time it is confirmed the user would lose one: nothing is removed,
        and the dialog comes back naming it."""
        team = self.team("Team")
        lose = self.draft("t_unsaid", level=None)
        self.grant(team, lose, ADMIN_PERM)
        UserPermission.objects.create(
            holder=self.other_admin, table=lose, level=ADMIN_PERM
        )
        with self.assertNoLogs(PERMISSION_LOG):
            with self.captureOnCommitCallbacks(execute=True):
                response = self.joined_run(
                    REMOVE, "t_unsaid", organization=team.pk, lose_access=""
                )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(self.grants(team, "t_unsaid"), {"t_unsaid": ADMIN_PERM})
        message = self.trigger(response, "tables-refused")["message"]
        self.assertIn(table_actions.LOSE_ACCESS_UNSAID, message)
        self.assertIn("t_unsaid", message)
        self.assertEqual(
            [t.name for t in response.context["preflight"].consequences["lose_access"]],
            ["t_unsaid"],
        )

    def test_a_guarded_table_still_sent_refuses_the_whole_request(self):
        team = self.team("Team")
        self.grant(team, self.draft("t_free"), WRITE_PERM)
        only = self.draft("t_guarded", level=None)
        self.grant(team, only, ADMIN_PERM)
        response = self.joined_run(REMOVE, "t_free", "t_guarded", organization=team.pk)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            self.grants(team, "t_free", "t_guarded"),
            {"t_free": WRITE_PERM, "t_guarded": ADMIN_PERM},
        )
        self.assertIn(
            "Give someone Admin there first",
            self.trigger(response, "tables-refused")["message"],
        )

    def test_a_table_without_table_admin_refuses_403(self):
        team = self.team("Team", member=False)
        self.grant(team, self.draft("t_fine"), WRITE_PERM)
        self.grant(team, self.draft("t_editor_only", level=WRITE_PERM), WRITE_PERM)
        response = self.joined_run(
            REMOVE, "t_fine", "t_editor_only", organization=team.pk
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            self.grants(team, "t_fine", "t_editor_only"),
            {"t_fine": WRITE_PERM, "t_editor_only": WRITE_PERM},
        )

    def test_a_confirmation_checked_against_another_organization_runs_nothing(self):
        first = self.team("First", member=False)
        second = self.team("Second", member=False)
        table = self.draft("t_two")
        self.grant(first, table, WRITE_PERM)
        self.grant(second, table, WRITE_PERM)
        response = self.client.post(
            self.action_path(REMOVE),
            {
                "tables": "t_two",
                "selection": "t_two",
                "organization": second.pk,
                "previewed": str(first.pk),
            },
            **HTMX,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["notice"], RECHECKED)
        self.assertEqual(self.grants(first, "t_two"), {"t_two": WRITE_PERM})
        self.assertEqual(self.grants(second, "t_two"), {"t_two": WRITE_PERM})


class ServiceTests(OrganizationCase):
    """The two bulk writes called directly, as an entry point other than
    the dashboard would: their own checks, in the single-Table order."""

    def test_sharing_refuses_a_table_without_table_admin_naming_it(self):
        team = self.team()
        ok, low = self.draft("t_s_ok"), self.draft("t_s_low", level=DELETE_PERM)
        with self.assertRaises(table_roles.NotAllowed) as refused:
            table_roles.share_with_organization(self.user, [ok, low], team, 4)
        self.assertEqual(refused.exception.tables, [low])
        self.assertEqual(GroupPermission.objects.count(), 0)

    def test_sharing_with_a_stranger_organization_is_invalid(self):
        foreign = self.team("Foreign", member=False)
        with self.assertRaises(table_roles.InvalidRequest) as refused:
            table_roles.share_with_organization(
                self.user, [self.draft("t_s_f")], foreign, 4
            )
        self.assertEqual(refused.exception.field, "organization")

    def test_removing_asks_before_taking_tables_off_the_dashboard(self):
        team = self.team()
        lose = self.draft("t_s_lose", level=None)
        self.grant(team, lose, ADMIN_PERM)
        UserPermission.objects.create(
            holder=self.other_admin, table=lose, level=ADMIN_PERM
        )
        with self.assertRaises(table_roles.ConfirmationNeeded) as asked:
            table_roles.remove_organization(self.user, [lose], team)
        self.assertEqual(asked.exception.tables, [lose])
        changes = table_roles.remove_organization(
            self.user, [lose], team, via="api", confirmed=True
        )
        self.assertEqual(
            [(c.action, c.before, c.after) for c in changes],
            [(table_roles.REMOVE, ADMIN_PERM, None)],
        )
        self.assertEqual(self.grants(team, "t_s_lose"), {"t_s_lose": None})

    def test_removing_the_only_admin_is_refused_naming_it(self):
        team = self.team()
        only = self.draft("t_s_only", level=None)
        self.grant(team, only, ADMIN_PERM)
        with self.assertRaises(table_roles.LastAdmin) as refused:
            table_roles.remove_organization(self.user, [only], team, confirmed=True)
        self.assertEqual(refused.exception.tables, [only])
        self.assertEqual(self.grants(team, "t_s_only"), {"t_s_only": ADMIN_PERM})
