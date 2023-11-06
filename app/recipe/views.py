"""
Views for the Recipe Api
"""
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiTypes)

from rest_framework import (viewsets, mixins, status)
from rest_framework.decorators import action
from rest_framework.response import Response
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

    def _params_to_ints(self, qs):
        """Convert a list  of strings to integers"""
        return [int(str_id) for str_id in qs.split(',')]

    def get_queryset(self):
        """ Retrive recipes for authenticated users."""
        tags = self.request.query_params.get('tags')
        ingredients = self.request.query_params.get('ingredients')

        queryset = self.queryset
        if tags:
            tag_ids = self._params_to_ints(tags)
            queryset = queryset.filter(tags__id__in = tag_ids)

        if ingredients:
            ingredient_ids = self._params_to_ints(ingredients)
            queryset = queryset.filter(ingredients__id__in = ingredient_ids)

        return queryset.filter(
            user = self.request.user,
        ).order_by('-id').distinct()





    def get_serializer_class(self):
        if self.action =="list":
            return serializers.RecipeSerializer
        elif self.action == 'upload_image':
            return serializers.RecipieImageSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """ Create a new recipe """
        serializer.save(user= self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload_image')
    def upload_image(self, request, pk=None):
        """Upload an image to recipe"""
        recipe = self.get_object()
        serializer = self.get_serializer(recipe, data = request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status = status.HTTP_200_OK)

        return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)


class BaseRecipeAttrViewSet(mixins.DestroyModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.ListModelMixin,
                            viewsets.GenericViewSet):
    """ Base Viewset for recipe attributes."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter the queryset to authentication"""
        return self.queryset.filter(user = self.request.user).order_by('-name')

class TagViewSet(BaseRecipeAttrViewSet):

    """Manage Tags in the database"""
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()

class IngredientViewSet(BaseRecipeAttrViewSet):
    """Manage Ingerient in the db"""
    serializer_class = serializers.IngredientSerializer
    queryset = Ingredient.objects.all()
