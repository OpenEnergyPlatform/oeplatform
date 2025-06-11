# SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr>
# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI>
# SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
# SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr>
# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI>
#
# SPDX-License-Identifier: MIT

from django.test import TestCase
from oemetadata.v2.v20.example import OEMETADATA_V20_EXAMPLE

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
            oemetadata=OEMETADATA_V20_EXAMPLE,
        )

        test_contributor = myuser.objects.create(
            name="test_user_contributor", email="contributor@test.de"
        )
        test_reviewer = myuser.objects.create(
            name="test_user_reviewer", email="reviewer@test.de"
        )

        PeerReview.objects.create(
            # Make sure this assignment matches your model's expectations
            table=table.name,
            # Adjust based on how `schema` is related in `PeerReview`
            schema=table.schema.name,
            contributor=test_contributor,
            reviewer=test_reviewer,
            # Simulate a record that needs migration
            oemetadata={},
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
        self.assertEqual(review.oemetadata, OEMETADATA_V20_EXAMPLE)

    def test_migration_rollback(self):
        # Implement if needed
        pass
