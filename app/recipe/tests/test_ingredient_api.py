from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Ingredient
from recipe.serializers import IngredientSerializer


INGREDIENT_URL = reverse('recipe:ingredient-list')


def detail_ingredient_url(id):
    return reverse('recipe:ingredient-detail', args=[id])


def create_user(email='test@example.com', password='12345test'):
    return get_user_model().objects.create_user(email, password)


class TestPublicIngredientApi(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_list_ingredients_for_non_auth_user(self):
        user = create_user()
        Ingredient.objects.create(name="ing1", user=user)
        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class TestPrivateIngredientApi(TestCase):
    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_list_ingredients_for_authenticated_user(self):
        Ingredient.objects.create(name="ing1", user=self.user)
        Ingredient.objects.create(name="ing2", user=self.user)
        res = self.client.get(INGREDIENT_URL)
        ingredients = Ingredient.objects.filter(user=self.user).order_by(
            '-name',
        )
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_list_ingredients_limited_to_user(self):
        other_user = create_user(email="newmail@yahoo.com")
        Ingredient.objects.create(name="ing1", user=other_user)
        ingredient = Ingredient.objects.create(name="ing2", user=self.user)
        res = self.client.get(INGREDIENT_URL)
        Ingredient.objects.filter(user=self.user).order_by('-name')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data[0]['name'], ingredient.name)
        self.assertEqual(res.data[0]['id'], ingredient.id)

    def test_update_ingredient(self):
        ingredient = Ingredient.objects.create(name='ing1', user=self.user)
        URL = detail_ingredient_url(ingredient.id)
        payload = {
            'name': 'new_one'
        }
        res = self.client.patch(URL, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload['name'])

    def test_delete_ingredient(self):
        ingredient = Ingredient.objects.create(name='ing1', user=self.user)
        URL = detail_ingredient_url(ingredient.id)
        res = self.client.delete(URL)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Ingredient.objects.filter(id=ingredient.id).exists())
