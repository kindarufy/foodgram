"""Команда создания демонстрационных пользователей и рецептов."""

import base64
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import BaseCommand
from recipes_app.models import Ingredient, Recipe, RecipeIngredient, Tag

User = get_user_model()

IMAGE_BASE64 = (
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD/'
    '//9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAA'
    'ggCByxOyYQAAAABJRU5ErkJggg=='
)


class Command(BaseCommand):
    """Создаёт минимальные тестовые данные для ручной проверки проекта."""

    help = (
        'Создаёт пользователей, теги, ингредиенты '
        'и демонстрационные рецепты.'
    )

    def _image(self, name):
        """Возвращает файл изображения из встроенной base64-строки."""
        return ContentFile(base64.b64decode(IMAGE_BASE64), name=name)

    def _create_user(self, email, username, first_name, last_name, password):
        """Создаёт пользователя, если он ещё не существует."""
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': username,
                'first_name': first_name,
                'last_name': last_name,
            },
        )
        if created:
            user.set_password(password)
            user.save(update_fields=('password',))
        return user

    def _create_recipe(self, author, name, tag_slugs, ingredient_names):
        """Создаёт демонстрационный рецепт автора."""
        if Recipe.objects.filter(author=author, name=name).exists():
            return None
        image_name = f'demo/{author.username}-{Recipe.objects.count() + 1}.png'
        recipe = Recipe.objects.create(
            author=author,
            name=name,
            image=self._image(Path(image_name).name),
            text='Демонстрационный рецепт для проверки проекта Foodgram.',
            cooking_time=15,
        )
        recipe.tags.set(Tag.objects.filter(slug__in=tag_slugs))
        ingredients = Ingredient.objects.filter(name__in=ingredient_names)[:3]
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(recipe=recipe, ingredient=ingredient, amount=100)
            for ingredient in ingredients
        )
        return recipe

    def handle(self, *args, **options):
        """Выполняет создание демонстрационных данных."""
        call_command('load_tags')
        if not Ingredient.objects.exists():
            call_command('load_ingredients')
        users = [
            self._create_user(
                'admin@foodgram.local',
                'admin',
                'Админ',
                'Фудграм',
                'PaSsWord',
            ),
            self._create_user(
                'chef1@foodgram.local',
                'chef-one',
                'Анна',
                'Поварова',
                'PaSsWord123',
            ),
            self._create_user(
                'chef2@foodgram.local',
                'chef-two',
                'Иван',
                'Кулинаров',
                'PaSsWord123',
            ),
        ]
        users[0].is_staff = True
        users[0].is_superuser = True
        users[0].save(update_fields=('is_staff', 'is_superuser'))
        created = 0
        recipes = (
            (
                users[0],
                'Овсяная каша с фруктами',
                ('breakfast',),
                ('овсяные хлопья', 'молоко', 'бананы'),
            ),
            (
                users[1],
                'Овощной суп',
                ('lunch',),
                ('картофель', 'морковь', 'лук репчатый'),
            ),
            (
                users[2],
                'Запечённая рыба',
                ('dinner',),
                ('рыба', 'лимон', 'соль'),
            ),
        )
        for author, name, tag_slugs, ingredient_names in recipes:
            recipe = self._create_recipe(
                author,
                name,
                tag_slugs,
                ingredient_names,
            )
            created += int(bool(recipe))
        self.stdout.write(
            self.style.SUCCESS(f'Создано новых рецептов: {created}')
        )
