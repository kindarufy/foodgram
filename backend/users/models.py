"""Модели пользователей проекта Foodgram."""

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Создаёт пользователей с авторизацией по электронной почте."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Создаёт пользователя с указанными данными и паролем."""
        if not email:
            raise ValueError('Адрес электронной почты обязателен.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Создаёт обычного пользователя."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        """Создаёт администратора проекта."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Суперпользователь должен иметь is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(
                'Суперпользователь должен иметь is_superuser=True.'
            )
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Пользователь Foodgram с уникальным адресом электронной почты."""

    email = models.EmailField(_('email address'), unique=True)
    avatar = models.ImageField(
        'аватар',
        upload_to='users/avatars/',
        blank=True,
        null=True,
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        """Настройки отображения и сортировки пользователей."""

        ordering = ('id',)
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        """Возвращает человекочитаемое имя пользователя."""
        return self.username
