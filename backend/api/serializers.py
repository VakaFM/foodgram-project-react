from django.core.validators import MinValueValidator
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (Favorite, Follow, Ingredient, Recipe,
                            RecipeIngredient, ShoppingCart, Tag)
from rest_framework import serializers
from users.models import User

# from .fields import ImageField


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
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'password', 'is_subscribed')
        read_only_fields = ['id']

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return Follow.objects.filter(user=user, author=obj).exists()


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
    image = Base64ImageField()
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
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Favorite.objects.filter(
            user=request.user, recipes=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user.id
        return ShoppingCart.objects.filter(user=user).exists()


class RecipeSerializerCreate(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = RecipesIngredientsSerializer(source='recipe_ingredient',
                                               many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True)
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(validators=[MinValueValidator(1)])

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'ingredients', 'name',
                  'image', 'cooking_time', 'text', 'author',)
        read_only_fields = ('author',)

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        return Favorite.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        return ShoppingCart.objects.filter(user=user, recipe=obj).exists()

    def validate_ingredient(self, data):
        ingredients = self.initial_data.get('ingredients')
        ingredient_list = []
        for ingredient_item in ingredients:
            ingredient = get_object_or_404(
                Ingredient, id=ingredient_item['id']
            )
            if ingredient in ingredient_list:
                raise serializers.ValidationError(
                    'ингредиент должен быть уникальным'
                )

            ingredient_list.append(ingredient)

        tags = self.initial_data.get('tags')
        if not tags:
            raise serializers.ValidationError(
                'Нужен минимум один тэг для рецепта'
            )
        for tag_id in tags:
            if not Tag.objects.filter(id=tag_id).exists():
                raise serializers.ValidationError(
                    f'тэга с id = {tag_id} не существует'
                )

        return data

    def validate_cooking_time(self, data):
        if data <= 0:
            raise serializers.ValidationError('Время должно быть больше 0')
        return data

    def create(self, validated_data):
        ingredients = validated_data.pop('recipe_ingredient')
        tags = validated_data.pop('tags')
        image = validated_data.pop('image')
        recipe = Recipe.objects.create(image=image, **validated_data)
        recipe.tags.set(tags)
        set_of_ingredients = [RecipeIngredient(
            recipe=recipe, ingredient=get_object_or_404(
                Ingredient, id=item['ingredient']['id']), amount=item[
                    'amount']) for item in ingredients]
        RecipeIngredient.objects.bulk_create(set_of_ingredients)

        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('recipe_ingredient')
        tags = validated_data.pop('tags')
        instance = super().update(instance, validated_data)
        return self.validate_ingredient(ingredients, tags, instance)


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
            raise serializers.ValidationError('Такой рецепт уже добавлен!')
        return data

    class Meta:
        model = Favorite
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
