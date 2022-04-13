from django.urls import include, path
from djoser.views import TokenCreateView, TokenDestroyView
from rest_framework.routers import SimpleRouter

from .views import (FavoriteViewSet, FollovChangeViewSet, FollovViewSet,
                    IngredientViewSet, ModUserViewSet, RecipeViewSet,
                    ShoppingCartViewSet, TagViewSet)

router_v1 = SimpleRouter()
router_v1.register('tags', TagViewSet)
router_v1.register('users', ModUserViewSet)
router_v1.register('recipes', RecipeViewSet)
router_v1.register('ingredients', IngredientViewSet)
router_v1.register('users/subscriptions',
                   FollovViewSet,
                   basename='subscriptions')


urlpatterns = [
    path('auth/', include("djoser.urls.authtoken")),
    path('auth/token/login/', TokenCreateView.as_view(), name='login'),
    path('auth/token/logout/', TokenDestroyView.as_view(), name='logout'),
    path('users/', ModUserViewSet.as_view({'get': 'list',
                                           'post': 'create', })),
    path('users/me/',
         ModUserViewSet.as_view({'get': 'me'}),
         name='me'),
    path('recipes/<int:recipe_id>/shopping_cart/',
         ShoppingCartViewSet.as_view({'post': 'create',
                                      'delete': 'destroy',
                                      })),
    path('recipes/<int:recipe_id>/favorite/',
         FavoriteViewSet.as_view({'post': 'create', 'delete': 'destroy'})),
    path('users/<int:author_id>/subscribe/',
         FollovChangeViewSet.as_view({'post': 'create', 'delete': 'destroy'})),
    path('', include(router_v1.urls))
]
