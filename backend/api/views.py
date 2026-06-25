"""Вьюсеты и представления REST API проекта Foodgram."""

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from recipes_app.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                                ShoppingCart, Subscription, Tag)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import IsAuthorOrReadOnly
from .serializers import (AvatarSerializer, IngredientSerializer,
                          RecipeCreateSerializer, RecipeReadSerializer,
                          RecipeRelationSerializer, RecipeUpdateSerializer,
                          SetPasswordSerializer, TagSerializer,
                          UserCreateSerializer, UserSerializer,
                          UserWithRecipesSerializer)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """Обрабатывает пользователей, аватары, пароли и подписки."""

    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    lookup_value_regex = r'\d+'
    http_method_names = ('get', 'post', 'put', 'delete', 'head', 'options')

    def get_permissions(self):
        """Возвращает права доступа для текущего действия."""
        if self.action in ('list', 'retrieve', 'create'):
            return (AllowAny(),)
        return (IsAuthenticated(),)

    def get_serializer_class(self):
        """Выбирает сериализатор под действие пользователя."""
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ('subscriptions', 'subscribe'):
            return UserWithRecipesSerializer
        if self.action == 'avatar':
            return AvatarSerializer
        if self.action == 'set_password':
            return SetPasswordSerializer
        return UserSerializer

    def create(self, request, *args, **kwargs):
        """Регистрирует нового пользователя."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=('get',), url_path='me')
    def me(self, request):
        """Возвращает профиль текущего пользователя."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=('post',), url_path='set_password')
    def set_password(self, request):
        """Меняет пароль текущего пользователя."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=('put', 'delete'), url_path='me/avatar')
    def avatar(self, request):
        """Загружает или удаляет аватар текущего пользователя."""
        if request.method == 'DELETE':
            if request.user.avatar:
                request.user.avatar.delete(save=False)
            request.user.avatar = None
            request.user.save(update_fields=('avatar',))
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = self.get_serializer(
            request.user,
            data=request.data,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=('get',), url_path='subscriptions')
    def subscriptions(self, request):
        """Возвращает авторов, на которых подписан текущий пользователь."""
        authors = User.objects.filter(subscribers__user=request.user).order_by(
            'subscribers__created_at'
        )
        page = self.paginate_queryset(authors)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=('post', 'delete'), url_path='subscribe')
    def subscribe(self, request, pk=None):
        """Подписывает пользователя на автора или удаляет подписку."""
        author = self.get_object()
        if request.method == 'DELETE':
            deleted_count, _ = Subscription.objects.filter(
                user=request.user,
                author=author,
            ).delete()
            if not deleted_count:
                return Response(
                    {'errors': 'Подписка не найдена.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(status=status.HTTP_204_NO_CONTENT)
        if author == request.user:
            return Response(
                {'errors': 'Нельзя подписаться на самого себя.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        subscription, created = Subscription.objects.get_or_create(
            user=request.user,
            author=author,
        )
        if not created:
            return Response(
                {'errors': 'Подписка уже существует.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = self.get_serializer(subscription.author)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Предоставляет список тегов и отдельный тег."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    lookup_value_regex = r'\d+'
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Предоставляет список ингредиентов с поиском по началу названия."""

    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    lookup_value_regex = r'\d+'
    pagination_class = None

    def get_queryset(self):
        """Возвращает ингредиенты с фильтрацией по параметру name."""
        queryset = Ingredient.objects.all()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset.order_by('name')


class RecipeViewSet(viewsets.ModelViewSet):
    """Обрабатывает рецепты, избранное и список покупок."""

    permission_classes = (IsAuthorOrReadOnly,)
    lookup_value_regex = r'\d+'
    http_method_names = (
        'get',
        'post',
        'patch',
        'delete',
        'head',
        'options',
    )

    def get_queryset(self):
        """Возвращает рецепты с фильтрами из query-параметров."""
        queryset = (
            Recipe.objects.select_related('author')
            .prefetch_related('tags', 'recipe_ingredients__ingredient')
        )
        request = self.request
        author = request.query_params.get('author')
        tags = request.query_params.getlist('tags')
        is_favorited = request.query_params.get('is_favorited')
        is_in_shopping_cart = request.query_params.get('is_in_shopping_cart')
        if author:
            queryset = queryset.filter(author_id=author)
        if tags:
            queryset = queryset.filter(tags__slug__in=tags).distinct()
        if is_favorited == '1':
            if request.user.is_authenticated:
                queryset = queryset.filter(favorited_by__user=request.user)
            else:
                queryset = queryset.none()
        if is_in_shopping_cart == '1':
            if request.user.is_authenticated:
                queryset = queryset.filter(
                    in_shopping_carts__user=request.user,
                )
            else:
                queryset = queryset.none()
        return queryset.order_by('-created_at', '-id')

    def get_permissions(self):
        """Возвращает права доступа для действия рецептов."""
        authenticated_actions = (
            'create',
            'partial_update',
            'destroy',
            'favorite',
            'shopping_cart',
            'download_shopping_cart',
        )
        if self.action in authenticated_actions:
            return (IsAuthenticated(), IsAuthorOrReadOnly())
        return (AllowAny(),)

    def get_serializer_class(self):
        """Выбирает сериализатор рецепта под действие."""
        if self.action == 'create':
            return RecipeCreateSerializer
        if self.action in ('partial_update', 'update'):
            return RecipeUpdateSerializer
        return RecipeReadSerializer

    def perform_create(self, serializer):
        """Сохраняет автора рецепта из текущего пользователя."""
        serializer.save(author=self.request.user)

    def partial_update(self, request, *args, **kwargs):
        """Обновляет рецепт как полный объект через PATCH по спецификации."""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def _change_user_recipe_relation(self, request, pk, model):
        """Добавляет рецепт в пользовательский список или удаляет его."""
        recipe = get_object_or_404(Recipe, pk=pk)
        relation = model.objects.filter(user=request.user, recipe=recipe)
        if request.method == 'POST':
            if relation.exists():
                return Response(
                    {'errors': 'Рецепт уже добавлен.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            model.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeRelationSerializer(
                recipe,
                context=self.get_serializer_context(),
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        deleted_count, _ = relation.delete()
        if not deleted_count:
            return Response(
                {'errors': 'Рецепт не был добавлен.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=('post', 'delete'), url_path='favorite')
    def favorite(self, request, pk=None):
        """Добавляет рецепт в избранное или удаляет его оттуда."""
        return self._change_user_recipe_relation(request, pk, Favorite)

    @action(detail=True, methods=('post', 'delete'), url_path='shopping_cart')
    def shopping_cart(self, request, pk=None):
        """Добавляет рецепт в список покупок или удаляет его оттуда."""
        return self._change_user_recipe_relation(request, pk, ShoppingCart)

    @action(detail=False, methods=('get',), url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        """Возвращает файл со сводным списком покупок."""
        ingredients = RecipeIngredient.objects.filter(
            recipe__in_shopping_carts__user=request.user,
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit',
        ).annotate(total=Sum('amount')).order_by('ingredient__name')
        lines = ['Список покупок Foodgram', '']
        if not ingredients:
            lines.append('Список покупок пуст.')
        for item in ingredients:
            lines.append(
                f"{item['ingredient__name']} "
                f"({item['ingredient__measurement_unit']}) — "
                f"{item['total']}"
            )
        response = HttpResponse('\n'.join(lines), content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping-list.txt"'
        )
        return response

    @action(detail=True, methods=('get',), url_path='get-link')
    def get_link(self, request, pk=None):
        """Возвращает короткую ссылку на рецепт."""
        recipe = self.get_object()
        short_url = request.build_absolute_uri(
            reverse('short-link', kwargs={'pk': recipe.pk})
        )
        return Response({'short-link': short_url})


class ShortLinkRedirectView(APIView):
    """Перенаправляет короткую ссылку рецепта на страницу SPA."""

    permission_classes = (AllowAny,)

    def get(self, request, pk):
        """Проверяет рецепт и перенаправляет на его публичную страницу."""
        get_object_or_404(Recipe, pk=pk)
        return redirect(f'/recipes/{pk}')
