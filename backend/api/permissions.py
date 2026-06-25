"""Права доступа API проекта Foodgram."""

from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Разрешает изменение объекта только его автору."""

    def has_permission(self, request, view):
        """Проверяет доступ к действию вьюсета."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Проверяет права на конкретный объект."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user
