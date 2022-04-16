from django.core.validators import MinValueValidator
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers

from recipes.models import (Favorite, Follow, Ingredient, Recipe,
                            RecipeIngredient, ShoppingCart, Tag)
from users.models import User
from .fields import ImageField


class ModUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name', 'is_subscribed')
        read_only_fields = ['id']

    def get_is_subscribed(self, author):
        user = self.context.get('request').user
        return not user.is_anonymous and Follow.objects.filter(
            user=user,
            author=author.id
        ).exists()


class ModUserCreateSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'password')
        read_only_fields = ['id']


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'slug', 'color', 'name',)


class RecipesIngredientsSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.StringRelatedField(
        source='ingredient.measurement_unit',
        read_only=True)
    amount = serializers.FloatField(validators=[MinValueValidator(0.001)])

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = ModUserSerializer(read_only=True)
    ingredients = RecipesIngredientsSerializer(source='recipe_ingredient',
                                               many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author',
                  'ingredients', 'name',
                  'text', 'image',
                  'cooking_time',
                  'is_favorited',
                  'is_in_shopping_cart',)

    def get_is_favorited(self, obj):
        if not self.context['request'].user.is_authenticated:
            return False
        recipes_user = self.context['request'].user.fav_recipes
        return recipes_user.filter(recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user.id
        return ShoppingCart.objects.filter(user=user).exists()


class RecipeSerializerCreate(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = RecipesIngredientsSerializer(source='recipe_ingredient',
                                               many=True)
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects, many=True)
    image = ImageField()
    cooking_time = serializers.IntegerField(validators=[MinValueValidator(1)])

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author',
                  'ingredients', 'name',
                  'image', 'cooking_time', 'text')

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        return Favorite.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        return ShoppingCart.objects.filter(user=user, recipe=obj).exists()

    def tags_ingredients(self, tags_data, ingredients_data, recipe):
        recipe.tags.clear()
        recipe.ingredients.clear()
        recipe.tags.set(tags_data)
        for ingredient_el in ingredients_data:
            ingredient_id = ingredient_el['ingredients'].get('id')
            ingredient = get_object_or_404(Ingredient, id=ingredient_id)
            RecipeIngredient.objects.update_or_create(
                recipe=recipe,
                ingredients=ingredient,
                amount=ingredient_el['amount']
            )
        return recipe

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError('Добавьте ингредиенты')
        ingredients_list = []
        for ingredient in ingredients:
            ingredient_obj = ingredient.get('id')
            if ingredient.get('amount') <= 0:
                raise serializers.ValidationError(
                    'Добавьте ингредиенты')
            if ingredient_obj.id in ingredients_list:
                raise serializers.ValidationError(
                    'Ингредиенты не должны повторяться')
            ingredients_list.append(ingredient_obj.id)
        return ingredients

    def validate_cooking_time(self, data):
        if data <= 0:
            raise serializers.ValidationError('Время должно быть больше 0')
        return data

    def create(self, validated_data):
        ingredients = validated_data.pop('recipe_ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(author=self.author, **validated_data)
        return self.tags_ingredients(ingredients, tags, recipe)

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('recipe_ingredients')
        tags = validated_data.pop('tags')
        instance = super().update(instance, validated_data)
        return self.tags_ingredients(ingredients, tags, instance)


class FollowSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(read_only=True)
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    recipes_count = serializers.IntegerField(read_only=True)
    is_subscribed = serializers.BooleanField(read_only=True)
    recipes = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Follow
        fields = ('__all__')

    def validate(self, data):
        request = self.context.get('request')
        if request.method == 'DELETE':
            return data
        author_id = request.parser_context.get('kwargs').get('author_id')
        author = get_object_or_404(User, id=author_id)
        user = self.context['request'].user
        if author == user:
            raise serializers.ValidationError(
                'Глупо подписываться на себя)')
        if Follow.objects.filter(author=author, user=user).exists():
            raise serializers.ValidationError(
                'Такая подписка уже есть')
        return data


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit',)


class FavoriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='recipe.id', read_only=True)
    name = serializers.CharField(source='recipe.name', read_only=True)
    cooking_time = serializers.CharField(source='recipe.cooking_time',
                                         read_only=True)
    image = serializers.CharField(source='recipe.image', read_only=True)

    def validated(self, data):
        request = self.context.get('request')
        if request.method == 'DELETE':
            return data
        recipe_id = request.parser_context.get('kwargs').get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        user = self.context['request'].user
        if Favorite.objects.filter(recipe=recipe, user=user).exists():
            raise serializers.ValidationError('Такой рецепт уже добавлен')
        return data

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time',)


class ShoppingCartSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='recipe.id', read_only=True)
    name = serializers.CharField(source='recipe.name', read_only=True)
    cooking_time = serializers.CharField(source='recipe.cooking_time',
                                         read_only=True)
    image = serializers.CharField(source='recipe.image', read_only=True)

    def validated(self, data):
        request = self.context.get('request')
        if request.method == 'DELETE':
            return data

        recipe_id = request.parser_context.get('kwargs').get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        user = self.context['request'].user
        if ShoppingCart.objects.filter(recipe=recipe, user=user).exists():
            raise serializers.ValidationError('Такой рецепт уже добавлен')
        return data

    class Meta:
        model = ShoppingCart
        fields = ('id', 'name', 'image', 'cooking_time',)