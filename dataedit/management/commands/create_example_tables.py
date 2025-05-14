# myapp/management/commands/setup_tables.py

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from api.services.permissions import assign_table_holder
from api.services.table_creation import TableCreationOrchestrator

User = get_user_model()

# Define your table specs here:
# Note: these can keep `"type"` for readability; we remap it below.
TABLE_DEFS = [
    {
        "schema": "model_draft",
        "table": "my_first_table",
        "columns": [
            {
                "name": "id",
                "type": "integer",
                "options": {"primary_key": True, "nullable": False},
            },
            {
                "name": "value",
                "type": "text",
                "options": {"nullable": True, "default": ""},
            },
        ],
        "constraints": [
            # e.g. { "constraint_type": "unique", "columns": ["value"], "name": "uq_value" } # noqa
        ],
    },
    # … more specs …
]


class Command(BaseCommand):
    help = "Seed DataEdit tables + actual DB tables as in the Tables API"

    def handle(self, *args, **opts):
        # 1) Ensure your dev user exists
        user, _ = User.objects.get_or_create(
            name="test", defaults={"email": "test@mail.com", "is_staff": True}
        )

        orchestrator = TableCreationOrchestrator()

        for spec in TABLE_DEFS:
            schema_name = spec["schema"]
            table_name = spec["table"]
            raw_columns = spec["columns"]
            raw_constraints = spec.get("constraints", [])

            # 2) Normalize each raw column into the shape table_create wants
            column_defs = []
            for col in raw_columns:
                opts = col.get("options", {})
                col_def = {
                    "name": col["name"],
                    "data_type": col["type"],  # <— required key
                    # boolean flags:
                    "primary_key": opts.get("primary_key", False),
                    "nullable": opts.get("nullable", True),
                }
                # optional defaults:
                if "default" in opts:
                    col_def["default"] = opts["default"]

                column_defs.append(col_def)

            # 3) Pass constraints through (they already match actions.table_create)
            constraint_defs = raw_constraints

            try:
                # 4) Create physical table → Django metadata
                orchestrator.create_table(
                    schema_name=schema_name,
                    table_name=table_name,
                    column_defs=column_defs,
                    constraint_defs=constraint_defs,
                )

                # 5) Grant ADMIN to your test user
                assign_table_holder(user, schema_name, table_name)

                self.stdout.write(
                    self.style.SUCCESS(f"✔ Created table {schema_name}.{table_name}")
                )

            except Exception as e:
                self.style.ERROR(f"✘ Failed to create {schema_name}.{table_name}: {e}")
