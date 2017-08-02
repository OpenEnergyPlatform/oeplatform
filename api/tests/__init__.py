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