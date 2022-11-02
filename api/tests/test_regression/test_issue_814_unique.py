"""
inserting the string "1000" in a varchar column
that has unique constraint  leads to an error.
"""
from api.tests import APITestCase


class Test_issue_814_unique(APITestCase):
    def test_issue_814_unique(self):
        self.create_table(
            structure={
                "columns": [
                    {"name": "id", "data_type": "bigseriaL", "is_nullable": True},
                    {
                        "name": "textfield",
                        "data_type": "varchar(128)",
                        "is_nullable": False,
                    },
                ],
                "constraints": [
                    {"constraint_type": "UNIQUE", "columns": ["textfield"]}
                ],
            },
            data=[{"textfield": "1000"}],
        )
