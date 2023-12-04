from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from decimal import Decimal

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag
from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')

def detail_tag(id):
    return reverse('recipe:tag-detail', args=[id])


def create_user(email='test@example.com', password='12345test'):
    return get_user_model().objects.create_user(email, password)


class TestPublicTagAPi(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_list_tags_for_no_authenticated(self):
        user = create_user()
        tag = Tag.objects.create(user=user, name='tag1')
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class TestPrivateTagApi(TestCase):

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_list_tags_for_authenticated_user(self):
        tag = Tag.objects.create(user=self.user, name='tag1')
        tag2 = Tag.objects.create(user=self.user, name='tag2')

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')
        serialized_tags = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serialized_tags.data)

    def test_only_retrieve_users_tags(self):
        other_user = create_user(email='somemail@example.com')
        Tag.objects.create(user=other_user, name='tag')
        tag = Tag.objects.create(user=self.user, name='tag2')
        serialized_tag = TagSerializer(tag)

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0], serialized_tag.data)

    def test_update_tag(self):
        tag = Tag.objects.create(user=self.user, name='tag1')
        url = detail_tag(tag.id)
        payload = {
            'name': 'new_tag'
        }
        res = self.client.patch(url, payload)
        tag.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(tag.name, payload['name'])

    def test_update_tag_user_unsuccessful(self):
        tag = Tag.objects.create(user=self.user, name='tag1')
        other_user = create_user(email='newuser@example.com')
        url = detail_tag(tag.id)
        payload = {
            'user': other_user
        }
        self.client.patch(url, payload)
        tag.refresh_from_db()

        self.assertEqual(tag.user, self.user)

    def test_delete_tag(self):
        tag = Tag.objects.create(user=self.user, name='tag1')
        url = detail_tag(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tag.objects.filter(id=tag.id).exists())
