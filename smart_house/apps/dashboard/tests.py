from django.test import TestCase
from django.urls import reverse


class DashboardViewsTests(TestCase):
    def test_dashboard_page_works_without_devices(self):
        response = self.client.get(reverse("dashboard:status"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No active switch devices found")
