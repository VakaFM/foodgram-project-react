from django.shortcuts import get_object_or_404
from recipes.models import Recipe
from rest_framework import status
from rest_framework.mixins import (CreateModelMixin, DestroyModelMixin,
                                   ListModelMixin, RetrieveModelMixin)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet


class ListRetriveViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    pass


class FollowMixin(CreateModelMixin, DestroyModelMixin, GenericViewSet):
    pass


class FavoritMixin(FollowMixin):
    permission_classes = (IsAuthenticated,)
    lookup_field = 'recipe_id'

    def perform_create(self, serializer):
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('recipe_id'))
        serializer.save(user=self.request.user, recipes=recipe)

    def destroy(self, request, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('recipe_id'))
        user = self.request.user
        instance = get_object_or_404(self.model, recipes=recipe, user=user)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('recipe_id'))
        return self.model.objects.filter(recipes=recipe)
