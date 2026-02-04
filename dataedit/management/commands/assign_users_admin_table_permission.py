"""
SPDX-License-Identifier: AGPL-3.0-or-later
"""

from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from dataedit.models import Table
from login.models import myuser
from login.utils import assign_table_holder


class Command(BaseCommand):
    help = "Patch table owners by assigning a user as permission"
    "holder (via assign_table_holder)."

    def add_arguments(self, parser):
        user_group = parser.add_mutually_exclusive_group(required=True)
        user_group.add_argument("--user-id", type=int, help="User id (myuser.pk)")
        user_group.add_argument("--username", type=str, help="Username (myuser.name)")
        user_group.add_argument("--email", type=str, help="Email (myuser.email)")

        parser.add_argument(
            "--from-file",
            type=str,
            default=None,
            help="Read table names from file (one per line; blank lines"
            "and #comments ignored).",
        )
        parser.add_argument(
            "table_names",
            nargs="*",
            help="Table names (edut_00) or schema-qualified (data.edut_00).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Don't write changes; only show what would happen.",
        )

    def _resolve_user(self, options) -> myuser:
        if options["user_id"] is not None:
            return myuser.objects.get(pk=options["user_id"])
        if options["username"]:
            return myuser.objects.get(name=options["username"])
        if options["email"]:
            return myuser.objects.get(email=options["email"])
        raise CommandError("No user selector provided (should be unreachable).")

    def _load_names(self, options) -> list[str]:
        names = list(options["table_names"] or [])

        if options["from_file"]:
            p = Path(options["from_file"])
            if not p.exists():
                raise CommandError(f"--from-file path does not exist: {p}")
            for line in p.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                names.append(line)

        if not names:
            raise CommandError(
                "No table names provided. Use positional names or --from-file."
            )
        return names

    @staticmethod
    def _normalize_table_name(raw: str) -> str:
        raw = raw.strip()
        # Accept `data.<name>` (schema is always data in your setup)
        if raw.startswith("data."):
            return raw.split(".", 1)[1]
        return raw

    def handle(self, *args, **options):
        try:
            user = self._resolve_user(options)
        except myuser.DoesNotExist as e:
            raise CommandError(f"User not found: {e}") from e

        dry_run = options["dry_run"]
        raw_names = self._load_names(options)
        table_names = [self._normalize_table_name(n) for n in raw_names]

        missing = []
        changed = 0

        with transaction.atomic():
            for name in table_names:
                table = Table.objects.filter(name=name).first()
                if not table:
                    missing.append(name)
                    self.stdout.write(self.style.ERROR(f"missing: {name}"))
                    continue

                if dry_run:
                    self.stdout.write(
                        self.style.WARNING(
                            f"[DRY] would assign holder {user} to {name}"
                        )
                    )
                    continue

                # This should create/update the proper UserPermission row(s)
                # exactly like normal table creation does.
                assign_table_holder(user=user, table=table)

                changed += 1
                self.stdout.write(self.style.SUCCESS(f"assigned: {user} -> {name}"))

            if dry_run:
                transaction.set_rollback(True)

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. assigned={changed}, missing={len(missing)}, dry_run={dry_run}"
            )
        )
