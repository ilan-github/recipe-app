"""
Views for the Recipe Api
"""

from rest_framework import (viewsets, mixins)
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import (Recipe, Tag, Ingredient)
from recipe import serializers

class RecipeViewSet(viewsets.ModelViewSet):
    """View for manage recipe APIs"""
    serializer_class = serializers.RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """ Retrive recipes for authenticated users."""
        return self.queryset.filter(user = self.request.user).order_by('-id')

    def get_serializer_class(self):
        if self.action =="list":
            return serializers.RecipeSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """ Create a new recipe """
        serializer.save(user= self.request.user)

class TagViewSet(mixins.DestroyModelMixin,
                 mixins.UpdateModelMixin,
                 mixins.ListModelMixin,
                 viewsets.GenericViewSet):

    """Manage Tags in the database"""
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """ Retrive tags for authenticated users."""
        return self.queryset.filter(user = self.request.user).order_by('-name')

class IngredientViewSet(mixins.UpdateModelMixin,
                        mixins.ListModelMixin,
                        mixins.DestroyModelMixin,
                        viewsets.GenericViewSet):
    """Manage Ingerient in the db"""
    serializer_class = serializers.IngredientSerializer
    queryset = Ingredient.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter the queryset to authentication"""
        return self.queryset.filter(user = self.request.user).order_by('-name')