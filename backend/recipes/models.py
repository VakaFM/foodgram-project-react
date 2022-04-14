from django.db import models

from users.models import User


class Ingredient(models.Model):
    name = models.CharField(max_length=200, unique=True)
    measurement_unit = models.CharField(max_length=200)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=200, unique=True)
    color = models.CharField(max_length=7, unique=True)
    slug = models.SlugField()

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Еэги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    tags = models.ManyToManyField(Tag, blank=True)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        verbose_name='автор рецепта')
    name = models.CharField(
        max_length=200,
        verbose_name='название рецепта')
    image = models.ImageField(upload_to='recipes/images/', blank=True)
    text = models.TextField(verbose_name='Рецепт')
    ingredients = models.ManyToManyField(Ingredient,
                                         verbose_name='ingredients',
                                         through='RecipeIngredient')
    cooking_time = models.PositiveIntegerField()

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe,
                               on_delete=models.CASCADE,
                               related_name='recipe_ingredient')
    ingredient = models.ForeignKey(Ingredient,
                                   on_delete=models.CASCADE,
                                   related_name='recipe_ingredient')
    amount = models.PositiveIntegerField(null=False)

    class Meta:
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='UniqueConstraintRecipeIngridient'),
        ]


class ShoppingCart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipes = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Корзина'
        constraints = [models.UniqueConstraint(
            fields=['user', 'recipes'], name='UniqueConstraintShoppingCart')]


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipes = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Избранное'
        constraints = [models.UniqueConstraint(
            fields=['user', 'recipes'], name='UniqueConstraintFavorite')]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following')

    class Meta:
        ordering = ['-author']
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [models.UniqueConstraint(
            fields=['user', 'author'], name='UniqueConstraintFollow')]
