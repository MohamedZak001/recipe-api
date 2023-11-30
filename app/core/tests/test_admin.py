from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse


class TestUserAdmin(TestCase):

    def setUp(self):
        self.client = Client()
        self.superuser = get_user_model().objects.create_superuser(
            "admin@example.com",
            "test12345",
        )
        self.client.force_login(self.superuser)
        self.user = get_user_model().objects.create_user(
            email="user@example.com",
            password="test12345",
            name="tes1",
        )

    def test_list_users(self):
        """ test the admin page lists the users """
        url = reverse('admin:core_user_changelist')
        res = self.client.get(url)

        self.assertContains(res, self.user.email)
        self.assertContains(res, self.user.name)

    def test_edit_user_page(self):
        """ test the edit users page in admin  """
        url = reverse('admin:core_user_change', args=[self.user.id])
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)

    def test_create_user_page(self):
        url = reverse("admin:core_user_add")
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)
