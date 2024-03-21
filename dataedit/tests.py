from django.test import TestCase
from django.db.migrations.executor import MigrationExecutor
from django.db import connection
from .models import PeerReview, Table, Schema

from login.models import myuser
from metadata.v160.example import OEMETADATA_V160_EXAMPLE

# functionality form migration 0033 / cant be imported?
def populate_oemetadata(apps, schema_editor):
    PeerReview = apps.get_model("dataedit", "PeerReview")
    TableModel = apps.get_model("dataedit", "Table")
    for review in PeerReview.objects.all():
        if not review.oemetadata or review.oemetadata == {}:
            # Logic to find a matching value from TableModel.
            table = TableModel.objects.filter(
                schema=review.schema, name=review.table
            ).first()
            if table:
                review.oemetadata = table.oemetadata
                review.save()


class MigrationTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        test_schema = Schema.objects.create(name="test")

        table = Table.objects.create(
            schema=test_schema,
            name="test_table",
            oemetadata=OEMETADATA_V160_EXAMPLE,
        )

        test_contributor = myuser.objects.create(
            name="test_user_contributor", email="contributor@test.de"
        )
        test_reviewer = myuser.objects.create(
            name="test_user_reviewer", email="reviewer@test.de"
        )

        PeerReview.objects.create(
            table=table.name,  # Make sure this assignment matches your model's expectations
            schema=table.schema.name,  # Adjust based on how `schema` is related in `PeerReview`
            contributor=test_contributor,
            reviewer=test_reviewer,
            oemetadata={},  # Simulate a record that needs migration
        )

    def test_migration(self):
        # Apply the migration
        executor = MigrationExecutor(connection)
        app = "dataedit"  # Your app name
        migration_name = "0033_peerreview_oemetadata"

        executor.migrate([(app, migration_name)])

        # Re-fetch records from the database
        review = PeerReview.objects.first()

        # Check that oemetadata is no longer {]
        self.assertEqual(
            review.oemetadata, OEMETADATA_V160_EXAMPLE
        )  # Or any other condition you expect

    def test_migration_rollback(self):
        # Implement if needed
        pass
