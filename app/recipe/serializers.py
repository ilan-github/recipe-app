"""
Serializer for recipe API
"""

from rest_framework import serializers

from core.models import Recipe, Tag

# from django.contrib.auth import (
#     get_user_model,
#     authenticate,
# )
# from django.utils.translation import gettext as _
class TagSerializer(serializers.ModelSerializer):
    """Serializer for the tag object."""

    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']
class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for the recipe object."""
    tags = TagSerializer(many = True, required = False)
    class Meta:
        model = Recipe
        fields = ['id', 'title', 'time_minutes', 'price', 'link', 'tags']
        read_only_fields = ['id']

    def create(self, validated_data):
        """Create a recipe"""
        # here we assign the tag fileds (if exist) to tag var,
        # (if not exist the tag var will be [])
        # than we pop the 'tag' out of the validated data.
        tags = validated_data.pop('tag', [])

        # create a recipe without the 'tag'
        recipe = Recipe.objects.create(**validated_data)

        # get the authenticated user
        auth_user = self.context['request'].user

        # adding the tags into the recipe:
        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(
                user = auth_user,
                **tag,
            )
            recipe.tags.add(tag_obj)

        return recipe


class RecipeDetailSerializer(RecipeSerializer):
    """Serializer for recipe detail view """
    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['description']



