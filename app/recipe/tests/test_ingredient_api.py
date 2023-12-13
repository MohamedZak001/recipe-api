from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from decimal import Decimal

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Ingredient, Recipe
from recipe.serializers import IngredientSerializer


INGREDIENT_URL = reverse('recipe:ingredient-list')


def detail_ingredient_url(id):
    return reverse('recipe:ingredient-detail', args=[id])


def create_user(email='test@example.com', password='12345test'):
    return get_user_model().objects.create_user(email, password)


def create_recipe(user, **kwargs):
    default = {
        'title': 'recipe 1',
        'description': 'the description for test recipe',
        'price': Decimal('50.5'),
        'time_minutes': 5,
        'link': 'http://www.example.com/recipe.pdf',
    }
    default.update(kwargs)
    recipe = Recipe.objects.create(user=user, **default)
    return recipe


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

    def test_filter_tags_by_assigned(self):
        i1 = Ingredient.objects.create(user=self.user, name='ing1')
        i2 = Ingredient.objects.create(user=self.user, name='ing2')
        recipe = create_recipe(self.user)
        recipe.ingredients.add(i1)
        payload = {
            'assigned_only': 1,
        }
        serializer1 = IngredientSerializer(i1)
        serializer2 = IngredientSerializer(i2)
        res = self.client.get(INGREDIENT_URL, payload)

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_filter_tags_by_assigned_distinct(self):
        i1 = Ingredient.objects.create(user=self.user, name='ing1')
        Ingredient.objects.create(user=self.user, name='ing2')
        recipe1 = create_recipe(self.user)
        recipe2 = create_recipe(self.user)
        recipe1.ingredients.add(i1)
        recipe2.ingredients.add(i1)
        payload = {
            'assigned_only': 1,
        }
        serializer1 = IngredientSerializer(i1)
        res = self.client.get(INGREDIENT_URL, payload)
        self.assertEqual(len(res.data), 1)
        self.assertIn(serializer1.data, res.data)