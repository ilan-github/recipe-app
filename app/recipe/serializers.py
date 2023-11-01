"""
Serializer for recipe API
"""

from rest_framework import serializers

from core.models import Recipe

# from django.contrib.auth import (
#     get_user_model,
#     authenticate,
# )
# from django.utils.translation import gettext as _

class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for the recipe object."""

    class Meta:
        model = Recipe
        fields = ['id', 'title', 'time_minutes', 'price', 'description', 'link']
        read_only_fields = ['id']

