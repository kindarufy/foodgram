"""Административная панель рецептов Foodgram."""

from django.contrib import admin

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Subscription, Tag)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Настраивает отображение тегов в админ-зоне."""

    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Настраивает отображение ингредиентов в админ-зоне."""

    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)


class RecipeIngredientInline(admin.TabularInline):
    """Позволяет редактировать ингредиенты на странице рецепта."""

    model = RecipeIngredient
    extra = 1
    autocomplete_fields = ('ingredient',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Настраивает отображение рецептов в админ-зоне."""

    list_display = (
        'id',
        'name',
        'author',
        'cooking_time',
        'favorite_count',
    )
    search_fields = (
        'name',
        'author__username',
        'author__email',
        'author__first_name',
        'author__last_name',
    )
    list_filter = ('tags', 'author')
    filter_horizontal = ('tags',)
    autocomplete_fields = ('author',)
    inlines = (RecipeIngredientInline,)

    @admin.display(description='В избранном')
    def favorite_count(self, obj):
        """Возвращает число добавлений рецепта в избранное."""
        return obj.favorited_by.count()


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Настраивает отображение избранных рецептов."""

    list_display = ('id', 'user', 'recipe', 'created_at')
    search_fields = ('user__email', 'user__username', 'recipe__name')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Настраивает отображение списков покупок."""

    list_display = ('id', 'user', 'recipe', 'created_at')
    search_fields = ('user__email', 'user__username', 'recipe__name')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Настраивает отображение подписок."""

    list_display = ('id', 'user', 'author', 'created_at')
    search_fields = ('user__email', 'author__email')
