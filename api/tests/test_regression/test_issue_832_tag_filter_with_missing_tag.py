from django.urls import reverse
from api.tests import APITestCase

class Test_issue_832_tag_filter_with_missing_tag(APITestCase):
    
    def test_issue_832_tag_filter_with_missing_tag(self):
        # index without filter
        res = self.client.post(reverse("index"))
        self.assertEqual(res.status_code, 200)

        # index with tag filter with non existent tag_id
        res = self.client.post(reverse("index") + f'?tags=-1')
        self.assertEqual(res.status_code, 200)

        # index with tag filter with invalid tag_id
        res = self.client.post(reverse("index") + f'?tags=xxx')
        self.assertEqual(res.status_code, 404)


