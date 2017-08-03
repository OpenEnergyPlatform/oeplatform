import json

from django.test import TestCase, Client

# Create your tests here.

from login.models import myuser

from rest_framework.authtoken.models import Token


class APITestCase(TestCase):
    test_schema = 'schema1'
    test_table = 'population2'

    @classmethod
    def setUpClass(cls):
        super(APITestCase, cls).setUpClass()
        cls.user = myuser.objects.create(name='MrTest')
        cls.user.save()
        cls.token = Token.objects.get(user=cls.user)
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