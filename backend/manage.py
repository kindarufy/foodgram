#!/usr/bin/env python
"""Утилита командной строки Django для управления проектом Foodgram."""

import os
import sys


def main():
    """Запускает административные команды Django."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'foodgram.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            'Не удалось импортировать Django. Проверьте виртуальное окружение '
            'и установленные зависимости.'
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
