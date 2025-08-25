from django.core.management.base import BaseCommand

from api.actions import get_schema_names, get_table_names
from dataedit.models import Table

# from dataedit.views import schema_whitelist
# copied from dataedit.views, because it may be removed later
schema_whitelist = [
    "boundaries",
    "climate",
    "demand",
    "economy",
    "emission",
    "environment",
    "grid",
    "model_draft",
    "openstreetmap",
    "policy",
    "reference",
    "scenario",
    "society",
    "supply",
]
schema_sandbox = "sandbox"
schema_datasets = "datasets"
schema_test = "test"


def get_schema_tables_to_migrate() -> dict[str, list[str]]:
    # check schemas in OEDB
    schema_names_oedb = set(get_schema_names({}))
    schema_names_oedb_data = set(schema_whitelist) & schema_names_oedb
    schema_names_oedb_meta = set("_" + s for s in schema_whitelist) & schema_names_oedb
    schema_names_special = (
        {
            "public",
            "openfred",
            "topology",
            "information_schema",
        }
        | {schema_sandbox, schema_datasets, schema_test}
        | {"_" + schema_sandbox, "_" + schema_datasets, "_" + schema_test}
    ) & schema_names_oedb
    schema_names_unexpected = (
        schema_names_oedb
        - schema_names_special
        - schema_names_oedb_data
        - schema_names_oedb_meta
    ) | ((schema_names_oedb_data | schema_names_oedb_meta) & schema_names_special)
    if schema_names_unexpected:
        raise Exception("Unexecpetd schemas: %s", schema_names_unexpected)

    schema_tables_migrate = {}

    # get tables from django
    table_names = set()
    schema_table_names = set()
    for table in Table.objects.all():
        table_name = table.name
        if table_name in table_names:
            raise Exception("duplicate table name: %s", table_name)
        table_names.add(table_name)

        schema_name = table.schema.name
        if schema_name not in schema_names_oedb_data:
            raise Exception("invalid schema name: %s", schema_name)
        schema_table_names.add((schema_name, table_name))

        is_publish = table.is_publish
        if is_publish != (schema_name != "model_draft"):
            print(
                "WARNING: invalid is_publish: %s.%s %s"
                % (schema_name, table_name, is_publish)
            )
            # TODO@jonas: is_publish vs. is in model_draft
            pass  # lots !!

        metadata = table.oemetadata
        topics = (metadata or {}).get("resources", [{}])[0].get("topics", [])
        if schema_name not in topics:
            print(
                "WARNING: schema not in topics: %s.%s %s"
                % (schema_name, table_name, topics)
            )
            # TODO@jonas: topics in metadata or in fields -> should be fields?

    # check tables
    schema_table_names_oedb = set()
    schema_table_names_oedb_meta_possible = set()
    for schema_name in schema_names_oedb_data:
        schema_tables_migrate[schema_name] = []
        for table_name in get_table_names({"schema": schema_name}):
            schema_table_names_oedb.add((schema_name, table_name))
            schema_tables_migrate[schema_name].append(table_name)
            for action in ["delete", "edit", "insert"]:
                meta_table_name = f"_{table_name}_{action}"
                if len(meta_table_name) > 63:
                    print(
                        "Warning: table name too long "
                        f"{meta_table_name} => {meta_table_name[:63]}"
                    )
                    meta_table_name = meta_table_name[:63]
                schema_table_names_oedb_meta_possible.add(
                    (schema_name, meta_table_name)
                )

    # tables in django same as oedb
    unexpected_tables = (schema_table_names_oedb - schema_table_names) | (
        schema_table_names - schema_table_names_oedb
    )
    if unexpected_tables:
        raise Exception(f"Unexpected tables: {unexpected_tables}")

    schema_table_names_oedb_meta = set()
    for schema_name_meta in schema_names_oedb_meta:
        schema_tables_migrate[schema_name_meta] = []
        for table_name in get_table_names({"schema": schema_name_meta}):
            schema_name = schema_name_meta.lstrip("_")
            schema_table_names_oedb_meta.add((schema_name, table_name))
            schema_tables_migrate[schema_name_meta].append(table_name)

    unexpected_tables = (
        schema_table_names_oedb_meta - schema_table_names_oedb_meta_possible
    )
    if unexpected_tables:
        raise Exception(f"Unexpected tables: {unexpected_tables}")

    return schema_tables_migrate


def prepare_oep_tables_to_migrate() -> None:
    """Ensure schema information (is model_draft, schema=>topic) is preserved."""
    # get tables from django
    for table in Table.objects.all():
        schema_name = table.schema.name
        table_name = table.name
        is_published = schema_name != "model_draft"
        if table.is_publish != is_published:
            print(
                "WARNING: invalid is_publish: %s.%s %s"
                % (schema_name, table_name, is_published)
            )
            # TODO@jonas: is_publish vs. is in model_draft
            # table.is_publish = is_published

        metadata = table.oemetadata or {}
        topics = (metadata or {}).get("resources", [{}])[0].get("topics", [])
        if schema_name not in topics:
            print(
                "WARNING: topic not set: %s.%s %s" % (schema_name, table_name, topics)
            )
            # TODO@jonas: topics in metadata:
            # validation (we want control topics), search speed, ...
        # table.save()


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):
        prepare_oep_tables_to_migrate()
        schema_tables_to_migrate = get_schema_tables_to_migrate()

        for schema, tables in schema_tables_to_migrate.items():
            for table in tables:
                sql = (
                    f'ALTER TABLE "{schema}"."{table}" SET SCHEMA "{schema_datasets}";'
                )
                print(sql)

        for schema in schema_tables_to_migrate:
            sql = f'DROP SCHEMA "{schema}";'
            print(sql)
