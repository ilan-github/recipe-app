"""
Test Recipe Api.
"""

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (Recipe, Tag, Ingredient)

from recipe.serializers import (RecipeSerializer, RecipeDetailSerializer)

RECIPES_URL = reverse('recipe:recipe-list')

def detail_url(recipe_id):
    """Create and return a recipe detail URL."""
    return reverse('recipe:recipe-detail', args=[recipe_id])

def create_recipe(user, **params):
    """ Create and return a sample recipe."""
    defaults = {
        'title': "Sample recipe title",
        'time_minutes': 22,
        'price': Decimal('5.55'),
        'description': "Sample recipe description",
        'link': 'http://example.com/recipe.pdf',
    }
    defaults.update(params)

    recipe = Recipe.objects.create(user = user, **defaults)
    return recipe

def create_user(**params):
    """ Create and return a new user"""
    return get_user_model().objects.create_user(**params)

class PublicRecipeAPITests(TestCase):
    """ Test unauthenticated API requests. """

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """ Test auth is required to call API"""
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateRecipeApiTests(TestCase):
    """Test authenticated API requests"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email = 'user@example.com',
            password = 'testpass123',
        )
        self.client.force_authenticate(self.user)

    def test_retrive_recipe(self):
        """ Test auth is retrive a list of recipes"""
        create_recipe(user = self.user)
        create_recipe(user = self.user)
        create_recipe(user = self.user)

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many = True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        """Test list of recipes is limited to authenticated"""
        other_user = create_user(
            email = 'other@example.com',
            password = 'password123',
        )

        create_recipe(user = other_user)
        create_recipe(user = self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user = self.user)
        serializer = RecipeSerializer(recipes, many = True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        """Test get recipe detail"""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.get(url)
        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        """Test creating a recipe"""
        payload = {
            "title": "sample recipe",
            'time_minutes': 30,
            'price': Decimal('4.55'),
        }
        res = self.client.post(RECIPES_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id = res.data['id'])
        for k,v in payload.items():
            self.assertEqual(getattr(recipe, k), v)

        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        """ Test partial update of a recipe """
        original_link = 'https://example.com/recipe.pdf'
        recipe = create_recipe(
            user = self.user,
            title = "Sample recipe title",
            link = original_link,
        )

        payload = {'title': 'New recipe title'}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self):
        """ Test full update of a recipe """
        original_link = 'https://example.com/recipe.pdf'
        recipe = create_recipe(
            user = self.user,
            title = "Sample recipe title",
            link = original_link,
            description = "sample description recipe"
        )
        payload = {'title': 'New recipe title',
                   'link':  'https://example.com/new_recipe.pdf',
                   'description': 'new sample description',
                   'time_minutes': 10,
                   'price': Decimal('2.50')
                   }

        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_update_user_return_error(self):
        """ Test changing the recipe user results in an error"""
        new_user = create_user(email = 'user2@example.com')
        recipe = create_recipe(user = self.user)
        payload = {'user': new_user }
        url = detail_url(recipe.id)
        self.client.patch(url, payload)
        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """ Test delete recipe"""
        recipe = create_recipe(user = self.user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id = recipe.id).exists())

    def test_delete_other_users_recipe_error(self):
        new_user = create_user(email = 'user2@example.com')
        recipe = create_recipe(user = new_user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id = recipe.id).exists())

    def test_create_recipe_with_new_tag(self):
        """Test crating a recipe with a new tag."""
        payload = {
            'title': "Thai Curry",
            'time_minutes': 30,
            'price': Decimal('2.50'),
            'tags': [{'name': 'Thai'}, {'name': 'Dinner'}],
        }

        res = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user = self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name = tag['name'],
                user = self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tag(self):
        """Test creating a recipe with an existing tag"""
        tag_indian = Tag.objects.create(user = self.user, name = 'Indian')
        payload = {
            "title": "Pongal",
            'time_minutes': 60,
            'price': Decimal('4.50'),
            'tags': [{'name': 'Indian'}, {'name': 'Breakfast'}],
        }
        res = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])
        recipes = Recipe.objects.filter(user = self.user)

        self.assertEqual(recipes.count(), 1)
        self.assertEqual(recipe.tags.count(), 2)

        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name = tag['name'],
                user = self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        """Test creating tag when updating a recipe"""
        recipe = create_recipe(user=self.user)
        payload = {
            'tags': [{'name': 'Lunch'}],
        }
        usr = detail_url(recipe.id)
        res = self.client.patch(usr, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user = self.user, name = 'Lunch')
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """Test assigning an existing tag when updating a recipe"""
        # Create the user-specific tags
        tag_breakfast = Tag.objects.create(user=self.user, name='Breakfast')
        tag_lunch = Tag.objects.create(user=self.user, name='Lunch')

        # Create a recipe and associate it with the breakfast tag
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        # Attempt to update the recipe with the 'Lunch' tag
        url = detail_url(recipe.id)
        payload = {'tags': [{'name': 'Lunch'}]}
        res = self.client.patch(url, payload, format='json')

        # Reload the recipe from the database to get the latest state
        recipe.refresh_from_db()

        # Check the response status code
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Check that the 'Lunch' tag is now associated with the recipe
        self.assertTrue(recipe.tags.filter(name='Lunch').exists())

        # Check that the 'Breakfast' tag is no longer associated with the recipe
        self.assertFalse(recipe.tags.filter(name='Breakfast').exists())

    def test_clear_recipe_tags(self):
        """ Test Clearing the recipe tags."""
        tag_breakfast = Tag.objects.create(user=self.user, name = 'Breakfast')
        recipe = create_recipe(user = self.user)
        recipe.tags.add(tag_breakfast)
        payload = {'tags': []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format = 'json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(),0)


    def test_create_recipe_with_new_ingredient(self):
        """Test Creating a recipe with a new ingredient."""
        payload = {
            'title': "Thai Curry",
            'time_minutes': 60,
            'price': Decimal('4.50'),
            'ingredients': [{'name': 'Salt'}, {'name': 'Pepper'}],
        }

        res = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user = self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                name = ingredient['name'],
                user = self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredient(self):
        """Test create a recipe with an existing ingredient"""
        ingredient = Ingredient.objects.create(user = self.user, name = "Salt")
        payload = {
            "title": "Pongal",
            'time_minutes': 60,
            'price': Decimal('4.50'),
            'ingredients': [{'name': 'Salt'}, {'name': 'Papper'}],
        }
        res = self.client.post(RECIPES_URL, payload, format = 'json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user = self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(ingredient, recipe.ingredients.all())
        for ingredient in payload['ingredients']:
            exist = recipe.ingredients.filter(user = self.user, name = ingredient['name']).exists()
            self.assertTrue(exist)

    def test_create_ingredient_on_update(self):
        """Test create an ingredient when updating a recipe"""
        recipe = create_recipe(user = self.user)
        payload = {'ingredients':[ {'name': "Salt"}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format = 'json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipe = Recipe.objects.get(id = recipe.id)
        self.assertEqual(recipe.ingredients.count(), 1)
        new_ingredient = Ingredient.objects.get(user = self.user, name = "Salt")
        self.assertIn(new_ingredient, recipe.ingredients.all() )

    def test_update_recipe_assign_ingredient(self):
            """Test assigning an existing ingredient when updating a recipe"""
            # Create the user-specific ingredients
            ingredient1 = Ingredient.objects.create(user = self.user, name = 'Papper')
            recipe = create_recipe(user = self.user)
            recipe.ingredients.add(ingredient1)

            ingredient2 = Ingredient.objects.create(user = self.user, name = 'Salt')
            payload = {'ingredients': [{'name': 'Salt'}]}
            url = detail_url(recipe.id)
            res = self.client.patch(url, payload, format='json')

            recipe.refresh_from_db()

            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertIn(ingredient2, recipe.ingredients.all() )
            self.assertNotIn(ingredient1, recipe.ingredients.all() )

    def test_clear_ingredients_form_recipe(self):
        """Test clear ingredients form recipe"""
        payload = {'ingredients': [{'name': 'salt'}]}
        ingredient_salt = Ingredient.objects.create(user = self.user, name = 'Salt')
        recipe = create_recipe(user = self.user)
        recipe.ingredients.add(ingredient_salt)

        payload = {'ingredients': []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format = 'json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.ingredients.count(), 0)
