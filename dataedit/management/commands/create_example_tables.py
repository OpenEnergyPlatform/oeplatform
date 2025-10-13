import json
from csv import DictReader
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from sqlalchemy import MetaData
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from api.actions import (
    _get_engine,
    set_table_metadata,
    try_convert_metadata_to_v2,
    try_parse_metadata,
    try_validate_metadata,
)
from api.services.permissions import assign_table_holder
from api.services.table_creation import TableCreationOrchestrator
from dataedit.views import get_tag_keywords_synchronized_metadata

User = get_user_model()


TABLE_DEFS = [
    {
        "schema": "dataset",
        "table": "example_wind_farm_capacity",
        "columns": [
            {
                "name": "id",
                "type": "bigserial",
                "options": {"primary_key": True, "nullable": False},
            },
            {
                "name": "technology",
                "type": "text",
                "options": {"nullable": True},
            },
            {
                "name": "type",
                "type": "text",
                "options": {"nullable": True},
            },
            {
                "name": "year",
                "type": "integer",
                "options": {"nullable": True},
            },
            {
                "name": "date",
                "type": "date",
                "options": {"nullable": True},
            },
            {
                "name": "value",
                "type": "numeric",
                "options": {"nullable": True},
            },
            {
                "name": "comment",
                "type": "text",
                "options": {"nullable": True},
            },
            {
                "name": "geometry",
                "type": "geometry",
                "options": {"nullable": True},
            },
        ],
        "constraints": [],
    }
]

CSV_FILE = "dataedit/management/data/example_wind_farm_capacity.csv"


class Command(BaseCommand):
    help = "Seed DataEdit tables + actual DB tables as in the Tables API"

    def handle(self, *args, **opts):
        # 1) Ensure your dev user exists
        user, _ = User.objects.get_or_create(
            name="test", defaults={"email": "test@mail.com", "is_staff": True}
        )

        print("Hello  world")
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
                self.stderr.write(
                    self.style.ERROR(
                        f"✘ Failed to create {schema_name}.{table_name}: {e}"
                    )
                )

            try:
                # Seed the table with data from CSV
                self._seed_data(schema_name, table_name, CSV_FILE)

            except Exception as e:
                self.stderr.write(
                    self.style.ERROR(
                        f"✘ Failed to seed {schema_name}.{table_name} with data: {e}"
                    )
                )

            try:
                # Set metadata for the table
                metadata_file = "dataedit/management/data/datapackage.json"
                self._set_metadata(schema_name, table_name, metadata_file)
            except Exception as e:
                self.stderr.write(
                    self.style.ERROR(
                        f"✘ Failed to set metadata for {schema_name}.{table_name}: {e}"
                    )
                )

    def _seed_data(self, schema, table_name, csv_file):
        engine = _get_engine()
        Session = sessionmaker(bind=engine)
        session = Session()
        metadata = MetaData(schema=schema)
        metadata.reflect(bind=engine, schema=schema)

        full_table_name = f"{schema}.{table_name}"
        table = metadata.tables.get(full_table_name)

        print(table)

        if table is None:
            self.stderr.write(
                self.style.ERROR(
                    f"Table '{full_table_name}' not found in reflected metadata."
                )
            )
            return

        with open(csv_file, newline="", encoding="utf-8") as f:
            reader = DictReader(f)
            rows = []

            for row in reader:
                cleaned = {k: (v if v != "" else None) for k, v in row.items()}
                rows.append(cleaned)

            if not rows:
                self.stdout.write(
                    self.style.WARNING(f"No rows to insert into {full_table_name}.")
                )
                return

            self.stdout.write(
                f"Preparing to insert {len(rows)} rows into {full_table_name}"
            )
            self.stdout.write(f"First row: {rows[0]}" if rows else "No rows parsed.")

            try:
                stmt = pg_insert(table).values(rows)
                stmt = stmt.on_conflict_do_nothing(index_elements=["id"])
                session.execute(stmt)
                session.commit()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✔ Inserted {len(rows)} rows into {full_table_name}"
                    )
                )
            except SQLAlchemyError as e:
                session.rollback()
                self.stderr.write(self.style.ERROR(f"SQLAlchemy insert error: {e}"))
            except Exception as e:
                session.rollback()
                self.stderr.write(self.style.ERROR(f"General insert error: {e}"))
            finally:
                session.close()

    def _set_metadata(self, schema, table_name, metadata_file):
        metadata_path = Path(metadata_file)
        metadata: dict = {}

        if not metadata_path.exists():
            self.stderr.write(
                self.style.ERROR(f"Metadata file '{metadata_file}' not found.")
            )
            return

        with open(metadata_path, encoding="utf-8") as f:
            raw_metadata = json.load(f)

        metadata, error = try_parse_metadata(raw_metadata)
        if error:
            raise Exception(f"Metadata parse error: {error}")

        metadata = try_convert_metadata_to_v2(metadata)
        metadata, error = try_validate_metadata(metadata)
        if error:
            raise Exception(f"Metadata validation error: {error}")

        # Sync keywords with tag system
        keywords = metadata["resources"][0].get("keywords", []) or []
        synced = get_tag_keywords_synchronized_metadata(
            table=table_name, schema=schema, keywords_new=keywords
        )
        metadata["resources"][0]["keywords"] = synced["resources"][0]["keywords"]

        # Save to Django's oemetadata JSONB field and comment
        set_table_metadata(table=table_name, schema=schema, metadata=metadata)

        self.stdout.write(
            self.style.SUCCESS(
                f"✔ Metadata saved and tags synced for {schema}.{table_name}"
            )
        )
