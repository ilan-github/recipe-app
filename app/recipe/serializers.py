"""
Serializer for recipe API
"""

from rest_framework import serializers

from core.models import Recipe, Tag, Ingredient

class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for the Ingredient object."""

    class Meta:
        model = Ingredient
        fields = ['id', 'name']
        read_only_fields = ['id']

class TagSerializer(serializers.ModelSerializer):
    """Serializer for the tag object."""

    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']
class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for the recipe object."""
    tags = TagSerializer(many = True, required = False)
    ingredients = IngredientSerializer(many = True, required = False)

    def _get_or_create_tags(self, tags, recipe):
        """Handle getting or creating tas if needed"""
        # get the authenticated user
        auth_user = self.context['request'].user

        # adding the tags into the recipe:
        for tag in tags:
            tag_obj = Tag.objects.create(user=auth_user, **tag)
            recipe.tags.add(tag_obj)
        return recipe

    def _get_co_create_ingredients(self, ingredients, recipe):
        """Handle getting or creating ingredients if needed"""
        # get the authenticated user
        auth_user = self.context['request'].user
        for ingredient in ingredients:
            ingredient_obj = Ingredient.objects.get_or_create(
                        user = auth_user,
                        **ingredient
                        )
            recipe.ingredients.add(ingredient_obj)
        return recipe

    class Meta:
        model = Recipe
        fields = [
            'id', 'title', 'time_minutes', 'price', 'link',
            'tags', 'ingredients'
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        """Create a recipe"""
        # here we assign the tag fileds (if exist) to tag var,
        # (if not exist the tag var will be [])
        # than we pop the 'tags' out of the validated data.
        tags = validated_data.pop('tags', [])
        ingredients = validated_data.pop('ingredients', [])

        # create a recipe without the 'tags' and 'ingredients'
        recipe = Recipe.objects.create(**validated_data)

        self._get_or_create_tags(tags=tags, recipe=recipe)
        self._get_co_create_ingredients(ingredients=ingredients, recipe=recipe)

        return recipe

    def update(self, instance, validated_data):
        """Update Recipe"""
        tags = validated_data.pop('tags', None)
        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class RecipeDetailSerializer(RecipeSerializer):
    """Serializer for recipe detail view """
    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['description']



