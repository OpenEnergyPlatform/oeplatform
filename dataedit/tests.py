from django.test import TestCase
from metadata.v160.example import OEMETADATA_V160_EXAMPLE

from login.models import myuser

from .models import PeerReview, Schema, Table


# replicated functionality form dataedit migration 0033
# avoid setting up full migration test framework
def populate_peerreview_oemetadata():
    for review in PeerReview.objects.all():
        if not review.oemetadata or review.oemetadata == {}:
            # Logic to find a matching value from TableModel.
            table = Table.objects.filter(
                schema__name=review.schema, name=review.table
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
        # executor = MigrationExecutor(connection)
        # app = "dataedit"
        # migration_name = "0033_peerreview_oemetadata"
        # executor.migrate([(app, migration_name)])

        # Make sure at least one PeerReview instance exists for testing
        self.assertTrue(PeerReview.objects.exists(), "PeerReview instance should exist")

        # Re-fetch records from the database
        review = PeerReview.objects.first()
        self.assertEqual(review.oemetadata, {})

        populate_peerreview_oemetadata()

        # Update Re-fetch records from the database
        review = PeerReview.objects.first()

        # Since the 'oemetadata' field is added by the migration, it will exist here
        # Now perform your checks on 'oemetadata'
        self.assertEqual(review.oemetadata, OEMETADATA_V160_EXAMPLE)

    def test_migration_rollback(self):
        # Implement if needed
        pass
