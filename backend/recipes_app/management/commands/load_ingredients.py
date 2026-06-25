"""Команда загрузки ингредиентов из JSON или CSV."""

import csv
import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from recipes_app.models import Ingredient


class Command(BaseCommand):
    """Загружает справочник ингредиентов в базу данных."""

    help = 'Загружает ингредиенты из файла JSON или CSV.'

    def add_arguments(self, parser):
        """Добавляет аргументы командной строки."""
        parser.add_argument(
            '--path',
            default=str(settings.BASE_DIR / 'data' / 'ingredients.json'),
            help='Путь к файлу ingredients.json или ingredients.csv.',
        )

    def _read_json(self, path):
        """Читает ингредиенты из JSON-файла."""
        with path.open(encoding='utf-8') as file:
            return json.load(file)

    def _read_csv(self, path):
        """Читает ингредиенты из CSV-файла без заголовков."""
        with path.open(encoding='utf-8') as file:
            reader = csv.reader(file)
            return [
                {'name': row[0], 'measurement_unit': row[1]}
                for row in reader
                if len(row) >= 2
            ]

    def handle(self, *args, **options):
        """Выполняет загрузку ингредиентов."""
        path = Path(options['path'])
        if not path.exists():
            raise CommandError(f'Файл не найден: {path}')
        if path.suffix == '.json':
            data = self._read_json(path)
        else:
            data = self._read_csv(path)
        created = 0
        for item in data:
            _, was_created = Ingredient.objects.get_or_create(
                name=item['name'],
                measurement_unit=item['measurement_unit'],
            )
            created += int(was_created)
        self.stdout.write(
            self.style.SUCCESS(f'Загружено новых ингредиентов: {created}')
        )
