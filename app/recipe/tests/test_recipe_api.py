from contextlib import AbstractContextManager
from typing import Any
from django.test import TestCase

import os
import tempfile
from PIL import Image

from rest_framework import status
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model
from django.urls import reverse

from recipe.serializers import (
    RecipeSerializer,
    DetailRecipeSerializer,
)
from core.models import Recipe, Tag, Ingredient

from decimal import Decimal

RECIPE_URL = reverse('recipe:recipe-list')


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


def detail_url(pk):
    return reverse('recipe:recipe-detail', kwargs={'pk': pk})


def upload_image_url(id):
    return reverse('recipe:recipe-upload-image', args=[id])


class TestPublicRecipeApi(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_non_authenticated_user_get_recipes(self):
        user = get_user_model().objects.create_user(
            email='test1@test.com',
            name='test',
            password='test12345',
        )
        create_recipe(user)
        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class TestPrivateRecipeApi(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='test1@test.com',
            name='test',
            password='test12345',
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        create_recipe(self.user)
        create_recipe(self.user)
        recipes = Recipe.objects.all().order_by('-id')
        serialized_recipes = RecipeSerializer(recipes, many=True)

        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.data, serialized_recipes.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_retrieve_only_user_recipes(self):
        other_user = get_user_model().objects.create_user(
            email='other@test.com',
            name='second',
            password='test12345',
        )
        create_recipe(other_user)
        create_recipe(self.user)
        create_recipe(self.user)

        recipe = Recipe.objects.filter(user=self.user).order_by('-id')
        serialized_recipe = RecipeSerializer(recipe, many=True)

        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.data, serialized_recipe.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_retrieve_detail_recipe_(self):
        recipe1 = create_recipe(self.user)
        create_recipe(self.user)
        DETAIL_RECIPE_URL = detail_url(recipe1.pk)
        res = self.client.get(DETAIL_RECIPE_URL)
        serialized_recipe = DetailRecipeSerializer(recipe1)

        self.assertEqual(res.data, serialized_recipe.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_recipe(self):
        payload = {
            'title': 'recipe1',
            'price': Decimal('50.0'),
            'time_minutes': 4,
            'description': 'the description for the test recipe',
            'link': 'http://www.example.com/recipe.pdf',
        }
        res = self.client.post(RECIPE_URL, data=payload)
        recipe = Recipe.objects.get(id=res.data.get('id'))

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(recipe.user, self.user)
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)

    def test_partial_update_of_recipe(self):
        link = 'http://www.link.com/recipe.pdf'
        recipe = create_recipe(
            user=self.user,
            link=link,
            title='old_title',
        )
        url = detail_url(recipe.id)
        payload = {
            'title': 'new_title',
        }
        res = self.client.patch(url, data=payload)
        recipe.refresh_from_db()

        self.assertEqual(recipe.link, link)
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_full_update_for_recipe(self):
        recipe = create_recipe(self.user)
        payload = {
            'title': 'new_title',
            'description': 'the new  description for test recipe',
            'price': Decimal('50.5'),
            'time_minutes': 5,
            'link': 'http://www.example.com/new_recipe.pdf',
        }
        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)

    def test_update_recipe_user_unsuccessful(self):
        other_user = get_user_model().objects.create_user(
            email='other@test.com',
            name='second',
            password='test12345',
        )
        recipe = create_recipe(self.user)
        url = detail_url(recipe.id)
        payload = {
            'user': other_user,
        }
        self.client.patch(url, payload)
        recipe.refresh_from_db()

        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        recipe = create_recipe(self.user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_other_users_recipe_unsuccessful(self):
        other_user = get_user_model().objects.create_user(
            email='other@test.com',
            name='second',
            password='test12345',
        )
        recipe = create_recipe(other_user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_new_tags(self):
        payload = {
            'title': 'recipe1',
            'price': Decimal('50.6'),
            'time_minutes': 3,
            'tags': [{'name': 'tag1'}, {'name': 'tag2'}],
        }
        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload['tags']:
            is_exists = recipe.tags.filter(name=tag['name']).exists()
            self.assertTrue(is_exists)

    def test_create_recipe_with_exist_tags(self):
        tag1 = Tag.objects.create(user=self.user, name='tag1')
        payload = {
            'title': 'recipe1',
            'price': Decimal('50.6'),
            'time_minutes': 3,
            'tags': [{'name': 'tag1'}, {'name': 'tag2'}],
        }
        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag1, recipe.tags.all())
        for tag in payload['tags']:
            is_exists = recipe.tags.filter(name=tag['name']).exists()
            self.assertTrue(is_exists)

    def test_update_recipe_with_non_exist_tags(self):
        """ test update tag with non exist tag with that name  """
        tag1 = Tag.objects.create(user=self.user, name='tag1')
        recipe = create_recipe(self.user)
        recipe.tags.add(tag1)
        url = detail_url(recipe.id)
        payload = {
            'tags': [{'name': 'tag2'}],
        }
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag2 = Tag.objects.get(name='tag2', user=self.user)
        self.assertIn(tag2, recipe.tags.all())

    def test_update_recipe_with_exist_tag(self):
        tag1 = Tag.objects.create(user=self.user, name='tag1')
        recipe = create_recipe(self.user)
        recipe.tags.add(tag1)
        tag2 = Tag.objects.create(user=self.user, name='tag2')
        url = detail_url(recipe.id)
        payload = {
            'tags': [{'name': 'tag2'}, ],
        }
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag2, recipe.tags.all())
        self.assertNotIn(tag1, recipe.tags.all())

    def test_clear_all_recipe_tags(self):
        tag = Tag.objects.create(user=self.user, name='tag1')
        recipe = create_recipe(self.user)
        recipe.tags.add(tag)
        url = detail_url(recipe.id)
        payload = {
            'tags': [],
        }
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_recipe_with_new_ingredients(self):
        payload = {
            'title': 'recipe1',
            'price': Decimal('50.6'),
            'time_minutes': 3,
            'ingredients': [{'name': 'ing1'}, {'name': 'ing2'}],
        }
        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        for ingredient in payload['ingredients']:
            is_exists = Ingredient.objects.filter(name=ingredient['name']).exists()
            self.assertTrue(is_exists)

    def test_create_recipe_with_exist_ingredients(self):
        ingredient1 = Ingredient.objects.create(user=self.user, name="ing1")
        payload = {
            'title': 'recipe1',
            'price': Decimal('50.6'),
            'time_minutes': 3,
            'ingredients': [{'name': 'ing1'}, {'name': 'ing2'}],
        }
        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(ingredient1, recipe.ingredients.all())
        for ingredient in payload['ingredients']:
            is_exists = Ingredient.objects.filter(name=ingredient['name']).exists()
            self.assertTrue(is_exists)

    def test_update_recipe_with_non_exist_ingredient(self):
        recipe = create_recipe(self.user)
        ingredient = Ingredient.objects.create(user=self.user, name='ing1')
        recipe.ingredients.add(ingredient)
        payload = {
            "ingredients": [{'name': 'ing2'}],
        }
        URL = detail_url(recipe.id)
        res = self.client.patch(URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient2 = Ingredient.objects.get(name='ing2')
        self.assertIn(ingredient2, recipe.ingredients.all())
        self.assertEqual(recipe.ingredients.count(), 1)

    def test_update_recipe_with_exist_ingredient(self):
        recipe = create_recipe(self.user)
        ingredient1 = Ingredient.objects.create(user=self.user, name='ing1')
        recipe.ingredients.add(ingredient1)
        ingredient2 = Ingredient.objects.create(user=self.user, name='ing2')
        payload = {
            "ingredients": [{'name': 'ing2'}],
        }
        URL = detail_url(recipe.id)
        res = self.client.patch(URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingredient2, recipe.ingredients.all())

    def test_delete_all_ingredients(self):
        recipe = create_recipe(self.user)
        ingredient1 = Ingredient.objects.create(user=self.user, name='ing1')
        recipe.ingredients.add(ingredient1)
        payload = {
            "ingredients": [],
        }
        URL = detail_url(recipe.id)
        res = self.client.patch(URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)


class TestUploadImage(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@example.com",
            "12345pass",
        )
        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image(self):
        url = upload_image_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (10, 10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload = {
                "image": image_file,
            }
            res = self.client.post(url, payload, format='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_update_image_bad_request(self):
        url = upload_image_url(self.recipe.id)
        payload = {
            'image': 'no_image',
        }
        res = self.client.post(url ,payload, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
