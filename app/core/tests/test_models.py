"""
Test Models
"""

from django.test import TestCase
from decimal import Decimal
from django.contrib.auth import get_user_model
from core import models


def create_user(**kwargs):
    default = {
        'email': "test@example.com",
        'password': '12345test',
        'name': 'test',
    }
    default.update(kwargs)
    return get_user_model().objects.create_user(**default)


class TestModels(TestCase):
    """
    Test create user with email and password
    """

    def test_create_user_with_email(self):
        email = "test@example.com"
        password = "test12345"
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_normalize_email(self):
        emails_test_cases = [
            ["test1@Example.com", "test1@example.com"],
            ["Test1@example.com", "Test1@example.com"],
            ["TEST1@Example.Com", "TEST1@example.com"],
        ]

        for email, normalized in emails_test_cases:
            user = get_user_model().objects.create_user(
                email=email,
                password="12345test",
            )
            self.assertEqual(user.email, normalized)

    def test_user_without_email_raises_error(self):
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(
                email='',
                password="12345test"
            )

    def test_create_super_user(self):
        user = get_user_model().objects.create_superuser(
            email="test1@example.com",
            password="12345test",
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe(self):
        user = get_user_model().objects.create_user(
            email='test1@test.com',
            name='test',
            password='12345test',
        )
        recipe = models.Recipe.objects.create(
            user=user,
            title='recipe title',
            price=Decimal('5.50'),
            description='the description for the test recipe',
            time_minutes=5,
        )

        self.assertEqual(str(recipe), recipe.title)

    def test_create_tags(self):
        user = create_user()
        tag = models.Tag.objects.create(user=user, name='Tag1')

        self.assertEqual(str(tag), tag.name)
