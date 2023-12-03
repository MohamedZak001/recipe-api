from rest_framework import status
from rest_framework.test import APIClient
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model


CREATE_USER_URL = reverse('user:create')
CREATE_TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


def create_user(**params):
    user = get_user_model().objects.create_user(**params)
    return user


class TestPublicUserApi(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_user(self):
        payload = {
            'email': "teast1@test.com",
            'password': '12345hhh',
            'name': 'test',
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload['email'])
        self.assertTrue(user.check_password(payload['password']))

    def test_user_with_email_exists_error(self):
        payload = {
            'email': "teast1@test.com",
            'password': '12345hhh',
            'name': 'test',
        }
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        payload = {
            "email": "test1@test.com",
            "password": "1234",
            'name': 'test'
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exist = get_user_model().objects.filter(
            email=payload['email'],
        ).exists()
        self.assertFalse(user_exist)

    def test_create_token(self):
        """ test create successful token for any registered user """
        user_info = {
            'email': 'test@test.com',
            'password': 'pass12345',
            'name': 'test',
        }
        create_user(**user_info)
        payload = {
            'email': user_info['email'],
            'password': user_info['password'],
        }
        res = self.client.post(CREATE_TOKEN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('token', res.data)

    def test_create_token_with_invalid_credentials(self):
        """ test unsuccessful creation for token  due to invalid credentials"""
        user_info = {
            'email': 'test@test.com',
            'password': 'pass12345',
            'name': 'test',
        }
        create_user(**user_info)
        payload = {
            'email': user_info['email'],
            'password': 'test12345',
        }
        res = self.client.post(CREATE_TOKEN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', res.data)

    def test_create_token_blank_password(self):
        """test unsuccessful creation for token  due to blank password """
        payload = {
            'email': 'test@test.com',
            'password': '',
        }
        res = self.client.post(CREATE_TOKEN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', res.data)

    def test_retrieve_user_unauthorized(self):
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class TestPrivateUserApi(TestCase):
    def setUp(self):
        user_data = {
            'email': "test1@test.com",
            'password': '12345test',
            'name': 'test'
        }
        self.user = create_user(**user_data)
        self.client = APIClient()
        self.client.force_authenticate(
            user=self.user
        )

    def test_retrieve_user_info(self):
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data.get('email'), self.user.email)
        self.assertEqual(res.data.get('name'), self.user.name)

    def test_method_not_allowed(self):
        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_info(self):
        new_data = {
            'name': 'new_name',
            'password': 'pass123434',
        }
        res = self.client.patch(ME_URL, new_data)
        self.user.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.name, new_data['name'])
        self.assertTrue(self.user.check_password(new_data['password']))
