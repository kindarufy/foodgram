"""Модели рецептов, тегов, ингредиентов и пользовательских списков."""

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q


class Tag(models.Model):
    """Тег для классификации рецептов."""

    name = models.CharField('название', max_length=32, unique=True)
    slug = models.SlugField('slug', max_length=32, unique=True)

    class Meta:
        """Настройки отображения и сортировки тегов."""

        ordering = ('id',)
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        """Возвращает название тега."""
        return self.name


class Ingredient(models.Model):
    """Ингредиент из справочника с единицей измерения."""

    name = models.CharField('название', max_length=128, db_index=True)
    measurement_unit = models.CharField('единица измерения', max_length=64)

    class Meta:
        """Настройки отображения, сортировки и уникальности ингредиентов."""

        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_ingredient_measurement',
            )
        ]
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        """Возвращает ингредиент с единицей измерения."""
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    """Рецепт пользователя с ингредиентами, тегами и изображением."""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='автор',
    )
    name = models.CharField('название', max_length=256)
    image = models.ImageField('изображение', upload_to='recipes/images/')
    text = models.TextField('описание')
    cooking_time = models.PositiveSmallIntegerField(
        'время приготовления',
        validators=(MinValueValidator(1),),
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='теги',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='ингредиенты',
    )
    created_at = models.DateTimeField('дата публикации', auto_now_add=True)

    class Meta:
        """Настройки отображения, сортировки и индексов рецептов."""

        ordering = ('-created_at', '-id')
        indexes = [
            models.Index(fields=('-created_at',)),
            models.Index(fields=('author',)),
        ]
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        """Возвращает название рецепта."""
        return self.name


class RecipeIngredient(models.Model):
    """Связывает рецепт с ингредиентом и его количеством."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='ингредиент',
    )
    amount = models.PositiveSmallIntegerField(
        'количество',
        validators=(MinValueValidator(1),),
    )

    class Meta:
        """Настройки уникальности ингредиента внутри рецепта."""

        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_recipe_ingredient',
            )
        ]
        verbose_name = 'ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'

    def __str__(self):
        """Возвращает количество ингредиента в рецепте."""
        return f'{self.ingredient} — {self.amount}'


class Favorite(models.Model):
    """Рецепт, добавленный пользователем в избранное."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name='рецепт',
    )
    created_at = models.DateTimeField('дата добавления', auto_now_add=True)

    class Meta:
        """Настройки уникальности избранного рецепта."""

        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_favorite_recipe',
            )
        ]
        verbose_name = 'избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'

    def __str__(self):
        """Возвращает связь пользователя с избранным рецептом."""
        return f'{self.user} — {self.recipe}'


class ShoppingCart(models.Model):
    """Рецепт, добавленный пользователем в список покупок."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_shopping_carts',
        verbose_name='рецепт',
    )
    created_at = models.DateTimeField('дата добавления', auto_now_add=True)

    class Meta:
        """Настройки уникальности рецепта в списке покупок."""

        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_shopping_cart_recipe',
            )
        ]
        verbose_name = 'рецепт в списке покупок'
        verbose_name_plural = 'Рецепты в списках покупок'

    def __str__(self):
        """Возвращает связь пользователя с рецептом в покупках."""
        return f'{self.user} — {self.recipe}'


class Subscription(models.Model):
    """Подписка пользователя на автора рецептов."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='подписчик',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='автор',
    )
    created_at = models.DateTimeField('дата подписки', auto_now_add=True)

    class Meta:
        """Настройки уникальности и запрета подписки на себя."""

        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_user_author_subscription',
            ),
            models.CheckConstraint(
                condition=~Q(user=F('author')),
                name='prevent_self_subscription',
            ),
        ]
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        """Возвращает связь подписчика и автора."""
        return f'{self.user} → {self.author}'
