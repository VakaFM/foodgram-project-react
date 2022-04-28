from django.contrib import admin
from recipes.models import (Favorite, Follow, Ingredient, Recipe,
                            RecipeIngredient, ShoppingCart, Tag)

admin.site.register(Tag)
admin.site.register(Ingredient)
admin.site.register(Recipe)
admin.site.register(ShoppingCart)
admin.site.register(Favorite)
admin.site.register(Follow)
admin.site.register(RecipeIngredient)
