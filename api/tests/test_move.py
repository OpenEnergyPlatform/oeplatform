"""test moving tables between draft and published
"""
from oeplatform.settings import DATASET_SCHEMA, TEST_DATASET_SCHEMA

from . import APITestCaseWithTable

# because we are in test mode(if detected properly)
assert TEST_DATASET_SCHEMA == DATASET_SCHEMA


class TestMove(APITestCaseWithTable):
    def _test_move(self):
        self.api_req(
            "post",
            path=f"move/{TEST_DATASET_SCHEMA}/",
            exp_code=201,
        )
