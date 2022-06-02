from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.models import (Favorite, Follow, Ingredient, Recipe,
                            RecipeIngredient, ShoppingCart, Tag)
from rest_framework import filters, viewsets, views, status
# from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import SAFE_METHODS, AllowAny, IsAuthenticated
# from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.response import Response


from .filters import FilterRecipe
from .mixins import FavoritMixin, ListRetriveViewSet
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
    permission_classes = [IsAdminOrReadOnly, ]
    pagination_class = CustomPaginator
    filter_backends = (DjangoFilterBackend,)
    filterset_class = FilterRecipe

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeSerializer
        return RecipeSerializerCreate

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=False, permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__carts__user=request.user).values(
            'ingredient__name',
            'ingredient__measurement_unit').annotate(total=Sum('amount'))
        shopping_list = 'Список покупок:\n\n'
        for number, ingredient in enumerate(ingredients, start=1):
            shopping_list += (
                f'{ingredient["ingredient__name"]}: '
                f'{ingredient["total"]} '
                f'{ingredient["ingredient__measurement_unit"]}\n')

        cart = 'shopping-list.txt'
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = (f'attachment;'
                                           f'filename={cart}')
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


class FollowViewSet(ListAPIView):
    serializer_class = FollowSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = CustomPaginator

    def get_queryset(self):
        user = self.request.user
        return user.follower.all()

    # def get_queryset(self):
    #     user_id = self.request.user.id
    #     return (self.request.user.follower.all()
    #             .annotate(recipes_count=Count('author__recipes'))
    #             .annotate(is_subscribed=Exists(Follow.objects.filter(
    #                 user_id=user_id, author__id=OuterRef('id')))))

    # def perform_create(self, serializer):
    #     author = get_object_or_404(User, id=self.kwargs.get('author_id'))
    #     serializer.save(user=self.request.user, author=author)


class FollowChangeViewSet(views.APIView):
    serializer_class = FollowSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = CustomPaginator

    def post(self, request, pk):
        author = get_object_or_404(User, pk=pk)
        user = self.request.user
        data = {'author': author.id, 'user': user.id}
        serializer = FollowSerializer(
            data=data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, pk):
        author = get_object_or_404(User, pk=pk)
        user = self.request.user
        subscription = get_object_or_404(
            Follow, user=user, author=author
        )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # def get_queryset(self):
    #     author = get_object_or_404(User, id=self.kwargs.get('author_id'))
    #     return Follow.objects.filter(author=author)

    # def post(self, serializer):
    #     author = get_object_or_404(User, id=self.kwargs.get('author_id'))
    #     serializer.save(user=self.request.user, author=author)

    # def destroy(self, request, *args, **kwargs):
    #     author = get_object_or_404(User, id=self.kwargs.get('author_id'))
    #     user = self.request.user
    #     instance = get_object_or_404(Follow, author=author, user=user)
    #     instance.delete()
