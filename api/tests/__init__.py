import json

from django.test import TestCase, Client
from api import actions
# Create your tests here.

from login.models import myuser

from rest_framework.authtoken.models import Token


class APITestCase(TestCase):
    test_schema = 'test'
    test_table = 'population2'

    @classmethod
    def setUpClass(cls):

        actions.perform_sql("DROP SCHEMA IF EXISTS test CASCADE")
        actions.perform_sql("DROP SCHEMA IF EXISTS schema2 CASCADE")
        actions.perform_sql("DROP SCHEMA IF EXISTS schema3 CASCADE")

        actions.perform_sql("CREATE SCHEMA test")
        actions.perform_sql("CREATE SCHEMA schema2")
        actions.perform_sql("CREATE SCHEMA schema3")

        actions.perform_sql("DROP SCHEMA IF EXISTS _test CASCADE")
        actions.perform_sql("DROP SCHEMA IF EXISTS _schema2 CASCADE")
        actions.perform_sql("DROP SCHEMA IF EXISTS _schema3 CASCADE")

        actions.perform_sql("CREATE SCHEMA _test")
        actions.perform_sql("CREATE SCHEMA _schema2")
        actions.perform_sql("CREATE SCHEMA _schema3")

        super(APITestCase, cls).setUpClass()
        cls.user, _ = myuser.objects.get_or_create(name='MrTest', mail_address='mrtest@test.com')
        cls.user.save()
        cls.token = Token.objects.get(user=cls.user)

        cls.other_user, _ = myuser.objects.get_or_create(name='NotMrTest', mail_address='notmrtest@test.com')
        cls.other_user.save()
        cls.other_token = Token.objects.get(user=cls.other_user)

        cls.client = Client()


    def assertDictEqualKeywise(self, d1, d2, excluded=None):
        if not excluded:
            excluded = []

        self.assertEqual(set(d1.keys()).union(excluded), set(d2.keys()).union(excluded), "Key sets do not match")

        for key in d1:
            if key not in excluded:
                value = d1[key]
                covalue = d2[key]
                self.assertEqual(value, covalue,
                                 "Key '{key}' does not match.".format(key=key))