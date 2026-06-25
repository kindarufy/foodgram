"""Пользовательские поля сериализаторов API."""

import base64
import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    """Декодирует изображение из строки base64 и сохраняет как файл."""

    def to_internal_value(self, data):
        """Преобразует base64-строку в объект файла изображения."""
        if not data:
            raise serializers.ValidationError(
                'Необходимо передать изображение.'
            )
        if isinstance(data, str) and data.startswith('data:image'):
            try:
                format_part, image_string = data.split(';base64,')
                extension = format_part.split('/')[-1]
                file_name = f'{uuid.uuid4()}.{extension}'
                data = ContentFile(base64.b64decode(image_string), file_name)
            except (TypeError, ValueError, base64.binascii.Error):
                raise serializers.ValidationError(
                    'Изображение должно быть корректной base64-строкой.'
                )
        return super().to_internal_value(data)

    def to_representation(self, value):
        """Возвращает абсолютную ссылку на изображение."""
        if not value:
            return None
        request = self.context.get('request')
        url = value.url
        if request is None:
            return url
        return request.build_absolute_uri(url)
