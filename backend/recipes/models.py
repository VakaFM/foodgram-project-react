from django.db import models

from users.models import User


class Ingredient(models.Model):
    name = models.CharField('Название ингредиента',
                            max_length=200, unique=True)
    measurement_unit = models.CharField('Единица измерения', max_length=200)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField('Название тэга', max_length=200, unique=True)
    color = models.CharField('цвет тэга', max_length=7, unique=True)
    slug = models.SlugField('Слаг тэга')

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    tags = models.ManyToManyField(Tag, verbose_name='Тэг', blank=True)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        verbose_name='автор рецепта')
    name = models.CharField('название рецепта', max_length=200)
    image = models.ImageField(verbose_name='Картинка',
                              upload_to='recipes/images/',
                              blank=True, null=True)
    text = models.TextField(verbose_name='Рецепт')
    ingredients = models.ManyToManyField(Ingredient,
                                         verbose_name='Ингредиенты',
                                         through='RecipeIngredient')
    cooking_time = models.PositiveIntegerField('Время приготовления')

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe,
                               on_delete=models.CASCADE,
                               related_name='recipe_ingredient',
                               verbose_name='Рецепт')
    ingredient = models.ForeignKey(Ingredient,
                                   on_delete=models.CASCADE,
                                   related_name='recipe_ingredient',
                                   verbose_name='Ингредиетн')
    amount = models.PositiveIntegerField('Количество ингредиентов', null=False)

    class Meta:
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='UniqueConstraintRecipeIngridient'),
        ]


class ShoppingCart(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             verbose_name='Покупатель')
    recipes = models.ForeignKey(Recipe,
                                on_delete=models.CASCADE,
                                verbose_name='Рецепт в корзине')

    class Meta:
        verbose_name = 'Корзина'
        constraints = [models.UniqueConstraint(
            fields=['user', 'recipes'], name='UniqueConstraintShoppingCart')]


class Favorite(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             verbose_name='Покупатель')
    recipes = models.ForeignKey(Recipe,
                                on_delete=models.CASCADE,
                                verbose_name='рецепт в избранном')

    class Meta:
        verbose_name = 'Избранное'
        constraints = [models.UniqueConstraint(
            fields=['user', 'recipes'], name='UniqueConstraintFavorite')]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор')

    class Meta:
        ordering = ['-author']
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [models.UniqueConstraint(
            fields=['user', 'author'], name='UniqueConstraintFollow')]
