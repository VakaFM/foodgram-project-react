from django.contrib.auth import get_user_model
from django.db.models import Count, Exists, OuterRef, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.models import (Favorite, Follow, Ingredient, Recipe,
                            RecipeIngredient, ShoppingCart, Tag)
from rest_framework import filters, viewsets
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import SAFE_METHODS, AllowAny, IsAuthenticated
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action

from .filters import FilterRecipe
from .mixins import FavoritMixin, FollowMixin, ListRetriveViewSet
from .pagination import CustomPaginator
from .permissions import IsAdminOrReadOnly
from .serializers import (FavoriteSerializer, FollowSerializer,
                          IngredientSerializer, ModUserSerializer,
                          RecipeSerializer, RecipeSerializerCreate,
                          ShoppingCartSerializer, TagSerializer)

User = get_user_model()


class TagViewSet(ListRetriveViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(ListRetriveViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backend = (filters.SearchFilter,)
    pagination_class = None
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = CustomPaginator
    filter_backends = (DjangoFilterBackend,)
    filterset_class = FilterRecipe

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeSerializer
        return RecipeSerializerCreate

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        methods=['GET', ],
        url_path='download_shopping_cart',
        detail=False,
    )
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            'ingredients__name',
            'ingredients__measurement_unit'
        ).annotate(total_amount=Sum('amount'))
        shopping_list = ['{} ({}) - {}\n'.format(
            ingredient['ingredients__name'],
            ingredient['ingredients__measurement_unit'],
            ingredient['total_amount']
        ) for ingredient in ingredients]
        response = HttpResponse(shopping_list, content_type='text/plain')
        attachment = 'attachment; filename="shopping_cart.txt"'
        response['Content-Disposition'] = attachment
        return response


class ModUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializers = ModUserSerializer
    permission_classes = [AllowAny]
    pagination_class = CustomPaginator

    def get_queryset(self):
        user_id = self.request.user.id
        return self.queryset.all().annotate(
            is_subscribed=Exists(
                Follow.objects.filter(
                    user_id=user_id, author__id=OuterRef('id')
                )
            )
        )


class ShoppingCartViewSet(FavoritMixin):
    model = ShoppingCart
    serializer_class = ShoppingCartSerializer
    queryset = ShoppingCart.objects.all()
    pagination_class = None


class FavoriteViewSet(FavoritMixin):
    model = Favorite
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer
    pagination_class = None


class FollowViewSet(GenericViewSet, ListModelMixin):
    model = Follow
    serializer_class = FollowSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        user_id = self.request.user.id
        return (self.request.user.follower.all()
                .annotate(recipes_count=Count('author__recipes'))
                .annotate(is_subscribed=Exists(Follow.objects.filter(
                    user_id=user_id, author__id=OuterRef('id')))))

    def perform_create(self, serializer):
        author = get_object_or_404(User, id=self.kwargs.get('author_id'))
        serializer.save(user=self.request.user, author=author)


class FollowChangeViewSet(FollowMixin):
    model = Follow
    serializer_class = FollowSerializer
    permission_classes = (IsAuthenticated)

    def get_queryset(self):
        return Follow.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        author = get_object_or_404(User, id=self.kwargs.get('author_id'))
        serializer.save(user=self.request.user, author=author)

    def perform_delete(self, instance):
        author = get_object_or_404(User, id=self.kwargs.get('author_id'))
        user = self.request.user
        instance = get_object_or_404(Follow, user=user, author=author)
        instance.delete()
