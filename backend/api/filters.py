from django_filters import BooleanFilter, FilterSet, ModelMultipleChoiceFilter

from recipes.models import Recipe, Tag


class FilterRecipe(FilterSet):
    is_favorited = BooleanFilter(method='favorited')
    is_in_shopping_cart = BooleanFilter(method='in_shopping_cart')
    tags = ModelMultipleChoiceFilter(field_name='tags__slug',
                                     to_field_name='slug',
                                     queryset=Tag.objects.all())

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')

    def favorit(self, queryset, name, value):
        user = self.request.user
        if not value:
            return queryset
        return queryset.filter(favorites__user=user)

    def shoping_cart(self, queryset, name, value):
        user = self.request.user
        if not value:
            return queryset
        return queryset.filter(shopping_cart__user=user)
