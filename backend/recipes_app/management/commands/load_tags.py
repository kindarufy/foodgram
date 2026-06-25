"""Команда загрузки базовых тегов проекта."""

from django.core.management.base import BaseCommand
from recipes_app.models import Tag


class Command(BaseCommand):
    """Создаёт базовые теги для рецептов."""

    help = 'Создаёт теги Завтрак, Обед и Ужин.'

    TAGS = (
        ('Завтрак', 'breakfast'),
        ('Обед', 'lunch'),
        ('Ужин', 'dinner'),
    )

    def handle(self, *args, **options):
        """Выполняет загрузку базовых тегов."""
        created = 0
        for name, slug in self.TAGS:
            _, was_created = Tag.objects.get_or_create(
                slug=slug,
                defaults={'name': name},
            )
            created += int(was_created)
        self.stdout.write(
            self.style.SUCCESS(f'Создано новых тегов: {created}')
        )
