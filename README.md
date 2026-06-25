# Foodgram — продуктовый помощник

Foodgram - SPA-приложение с REST API, где пользователи публикуют рецепты, подписываются на авторов, добавляют рецепты в избранное и формируют список покупок.

## Что реализовано

- Регистрация, вход, выход и смена пароля через токены.
- Профили пользователей, подписки, страница «Мои подписки».
- Загрузка, изменение и удаление аватара пользователя.
- CRUD рецептов: создание, просмотр, редактирование и удаление автором.
- Теги, ингредиенты и поиск ингредиентов по началу названия.
- Фильтрация рецептов по автору, тегам, избранному и списку покупок.
- Избранное и список покупок с защитой от повторного добавления.
- Скачивание сводного списка покупок в `.txt` с суммированием ингредиентов.
- Короткая ссылка рецепта `/s/<id>/` с редиректом на страницу рецепта.
- Админ-зона со всеми моделями, поиском и фильтрами.
- PostgreSQL, Docker Compose, Nginx, Gunicorn, volumes для статики, медиа и БД.
- GitHub Actions для проверки PEP8, сборки Docker-образа и деплоя.

## Технологии

Python 3.12, Django 5.2, Django REST Framework, Djoser, PostgreSQL, Docker, Nginx, Gunicorn, React.

## Основные API-адреса

- `GET /api/recipes/` — список рецептов.
- `POST /api/recipes/` — создать рецепт.
- `GET /api/recipes/{id}/` — рецепт.
- `PATCH /api/recipes/{id}/` — изменить свой рецепт.
- `DELETE /api/recipes/{id}/` — удалить свой рецепт.
- `POST/DELETE /api/recipes/{id}/favorite/` — избранное.
- `POST/DELETE /api/recipes/{id}/shopping_cart/` — список покупок.
- `GET /api/recipes/download_shopping_cart/` — скачать список покупок.
- `GET /api/recipes/{id}/get-link/` — получить короткую ссылку.
- `GET /api/tags/` — теги.
- `GET /api/ingredients/?name=му` — поиск ингредиентов.
- `POST /api/users/` — регистрация.
- `POST /api/auth/token/login/` — получить токен.
- `POST /api/auth/token/logout/` — удалить токен.
- `GET /api/users/me/` — текущий пользователь.
- `PUT/DELETE /api/users/me/avatar/` — аватар.
- `GET /api/users/subscriptions/` — подписки.
- `POST/DELETE /api/users/{id}/subscribe/` — подписаться или отписаться.
