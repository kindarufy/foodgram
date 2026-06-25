"""Конфигурация приложения API."""

from django.apps import AppConfig


class ApiConfig(AppConfig):
    """Настраивает приложение REST API."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    verbose_name = 'API'
