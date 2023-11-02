"""
Test Tags Apis.
"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag
from recipe.serializers import TagSerializer

TAG_URL = reverse('recipe:tag-list')

def detail_url(tag_id):
    """Create and return a tag detail URL."""
    return reverse('recipe:tag-detail', args=[tag_id])

def create_user(email = 'user@example.com', password = 'testpass123'):
    return get_user_model().objects.create_user(email, password)

def create_tag(user, **params):
    """Create and return a sample tag"""
    defaults = {
        'name': "sample tag name"
    }
    defaults.update(params)
    tag = Tag.objects.create(user = user, **defaults)
    return tag


class PublicTagAPITests(TestCase):
    """ Test unauthenticated API requests. """

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """ Test auth is required to call API"""
        res = self.client.get(TAG_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateTagAPITests(TestCase):
    """ Test authenticated API requests. """

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email = 'user@example.com',
            password = 'testpass123',
        )
        self.client.force_authenticate(self.user)

    def test_retrive_tags(self):
        """ Test auth is retrive a list of tags"""
        create_tag(user = self.user, name = 'ver')
        create_tag(user = self.user, name = 'ber')

        res = self.client.get(TAG_URL)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many = True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        user2 = create_user(email = 'user2@example.com', password = 'passtest1234')
        create_tag(user = self.user, name = 'ver')
        create_tag(user = user2, name = 'tag_user2')

        res = self.client.get(TAG_URL)
        tags = Tag.objects.filter(user = self.user)
        serializer = TagSerializer(tags, many = True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_update_tag(self):
        """ Test full update of a tag """
        tag = create_tag(
            user = self.user,
            name = "TagName"
        )
        payload = {'name': 'NewTagName'}
        url = detail_url(tag.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload['name'])
        self.assertEqual(tag.user, self.user)

    def test_delete_tag(self):
        """Test deleting a tag"""
        tag = create_tag(user=self.user, name = "popotag")
        url = detail_url(tag.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tag.objects.filter(id = tag.id).exists())

    def test_delete_other_users_tag_error(self):
        """Test deleting a nother user tag"""
        user2 = create_user(email = 'user2@example.com', password='passtest123')
        tag2 = create_tag(user=user2, name = "popotag")
        url = detail_url(tag2.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Tag.objects.filter(id = tag2.id).exists())



