"""
Test Ingredient Apis.
"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient
from recipe.serializers import IngredientSerializer

INGREDIENT_URL = reverse('recipe:ingredient-list')

def detail_url(ingredient_id):
    """Create and return a ingredient detail URL."""
    return reverse('recipe:ingredient-detail', args=[ingredient_id])

def create_user(email = 'user@example.com', password = 'testpass123'):
    return get_user_model().objects.create_user(email, password)

class PublicIngredientAPITests(TestCase):
    """ Test unauthenticated API requests. """

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """ Test auth is required to call API"""
        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateIngredientAPITests(TestCase):
    """ Test authenticated API requests. """

    def setUp(self):
        self.user = create_user(
            email = 'user@example.com',
            password = 'testpass123',
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrive_ingredients(self):
        """ Test auth is retrive a list of ingredients"""
        Ingredient.objects.create(user = self.user, name = 'Kale')
        Ingredient.objects.create(user = self.user, name = 'Cinamon')

        res = self.client.get(INGREDIENT_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many = True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """ Test list of ingredients is limited to authenticate user"""
        user2 = create_user(email = 'user2@example.com', password = 'passtest1234')
        Ingredient.objects.create(user = user2, name = 'Salt')
        ingredient = Ingredient.objects.create(user = self.user, name = 'Pepper')

        res = self.client.get(INGREDIENT_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)
        self.assertEqual(res.data[0]['id'], ingredient.id)

    def test_update_ingredient(self):
        """Test full update of an ingredient"""
        ingredient = Ingredient.objects.create(user = self.user, name = 'Salt')
        payload = {'name': 'Pepper'}
        url = detail_url(ingredient.id)
        res = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()


        self.assertEqual(ingredient.name, payload['name'])
        self.assertEqual(ingredient.user, self.user)

    def test_delete_ingredient(self):
        ingredient = Ingredient.objects.create(user = self.user, name = "Salt")
        url = detail_url(ingredient.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Ingredient.objects.filter(id = ingredient.id).exists())


    # def test_delete_other_users_tag_error(self):
    #     """Test deleting a nother user tag"""
    #     user2 = create_user(email = 'user2@example.com', password='passtest123')
    #     tag2 = create_tag(user=user2, name = "popotag")
    #     url = detail_url(tag2.id)
    #     res = self.client.delete(url)
    #     self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
    #     self.assertTrue(Tag.objects.filter(id = tag2.id).exists())


