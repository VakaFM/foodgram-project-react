from django.db import models

# from django.contrib.auth import get_user_model
from users.models import User

# User = get_user_model


class Ingredient(models.Model):
    name = models.CharField(max_length=200, unique=True)
    measurement_unit = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=200, unique=True)
    color = models.CharField(max_length=7, unique=True)
    slug = models.SlugField()

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


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe,
                               on_delete=models.CASCADE,
                               related_name='recipe_ingredient')
    ingredient = models.ForeignKey(Ingredient,
                                   on_delete=models.CASCADE,
                                   related_name='recipe_ingredient')
    amount = models.PositiveIntegerField(null=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='UniqueConstraintRecipeIngridient'),
        ]


class ShoppingCart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipes = models.ForeignKey(Recipe, on_delete=models.CASCADE)


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipes = models.ForeignKey(Recipe, on_delete=models.CASCADE)


class Follov(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following')
