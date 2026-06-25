"""Конфигурация приложения рецептов."""

from django.apps import AppConfig


class RecipesConfig(AppConfig):
    """Настраивает приложение рецептов и справочников."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'recipes_app'
    verbose_name = 'Рецепты'
