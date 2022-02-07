import re
from django.urls import reverse
from api.tests import APITestCase

class Test_879(APITestCase):
    test_table = "test_issue_879_csv_export"
    
    test_data = [
        {"id": 1, "textfield": "text1", "numfield": 1},
        {"id": 2, "textfield": "text2", "numfield": -0.5},
    ]
    excepted_response = '''"id","textfield","numfield"\n1,"text1",1\n2,"text2",-0.5'''
    
    def test_879(self):        
        # create table with test data using the API
        self.create_table(
            structure={"columns": [
                {"name": "id", "data_type": "bigint", "is_nullable": False},
                {"name": "textfield", "data_type": "varchar(128)", "is_nullable": False},
                {"name": "numfield", "data_type": "float", "is_nullable": False}
            ]}, 
            data=self.test_data
        )
    
        import logging
        url = reverse("api_rows", kwargs={"schema": self.test_schema, "table": self.test_table})
        url = url + '?form=csv'

        logging.error(url)

        stream = self.client.get(url).streaming_content
        byte_data = b''.join(stream)
        str_data = byte_data.decode()
        
        # compare without whitespace
        str_data = re.sub('\s*', '', str_data)

        self.assertEqual(str_data, re.sub('\s*', '', self.excepted_response))


# python manage.py test api.tests.test_regression.test_issue_879_csv_export