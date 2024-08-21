from django.test import TestCase  # noqa:F401

# Create your tests here.


class OeoxNewUnitTestCase(TestCase):
    def setUp(self):
        self.mock_user_data_struct = {
            "nominator": [
                {
                    "position": 1,
                    "unitName": "test data set",
                    "unitType": "linear",
                    "unitPrefix": "text file format",
                }
            ],
            "denominator": [
                {
                    "position": 1,
                    "unitName": "legal name",
                    "unitType": "linear",
                    "unitPrefix": "",
                }
            ],
            "definition": None,
            "unitLabel": None,
        }

    def test_create_new_oeox_unit(self):
        pass
