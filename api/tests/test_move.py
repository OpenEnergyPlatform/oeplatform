"""test moving tables between draft and published
"""
from dataedit.models import Table
from oeplatform.settings import TEST_DATASET_SCHEMA, TEST_DRAFT_SCHEMA

from . import APITestCaseWithTable


class TestMove(APITestCaseWithTable):
    def test_move(self):
        self.assertEqual(
            Table.objects.get(name=self.test_table).schema.name, TEST_DRAFT_SCHEMA
        )

        self.api_req(
            "post",
            path=f"move/{TEST_DATASET_SCHEMA}/",
            exp_code=200,
        )

        self.assertEqual(
            Table.objects.get(name=self.test_table).schema.name, TEST_DATASET_SCHEMA
        )

        # move again would fail
        self.api_req(
            "post",
            path=f"move/{TEST_DATASET_SCHEMA}/",
            exp_code=400,
        )

        # move back, otherwise tear down creates error
        self.api_req(
            "post",
            path=f"move/{self.test_schema}/",
            exp_code=200,
        )

        self.assertEqual(
            Table.objects.get(name=self.test_table).schema.name, TEST_DRAFT_SCHEMA
        )
