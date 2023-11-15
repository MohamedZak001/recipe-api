"""
Test Models
"""

from django.test import TestCase
from django.contrib.auth import get_user_model


class TestModels(TestCase):
    """Test create user with email"""

    def test_create_user_with_email(self):
        email = "test@example.com"
        password = "test12345"
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
