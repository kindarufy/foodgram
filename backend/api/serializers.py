"""Сериализаторы REST API проекта Foodgram."""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from recipes_app.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                                ShoppingCart, Subscription, Tag)
from rest_framework import serializers

from .fields import Base64ImageField

User = get_user_model()


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализует регистрацию пользователя."""

    password = serializers.CharField(write_only=True)

    class Meta:
        """Определяет поля регистрации пользователя."""

        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )
        read_only_fields = ('id',)

    def validate_username(self, value):
        """Проверяет, что имя пользователя допустимо."""
        if value.lower() == 'me':
            raise serializers.ValidationError(
                'Имя пользователя "me" использовать нельзя.'
            )
        return value

    def validate_password(self, value):
        """Проверяет пароль стандартными валидаторами Django."""
        try:
            validate_password(value)
        except DjangoValidationError as error:
            raise serializers.ValidationError(list(error.messages))
        return value

    def create(self, validated_data):
        """Создаёт пользователя с хешированным паролем."""
        password = validated_data.pop('password')
        return User.objects.create_user(password=password, **validated_data)

    def to_representation(self, instance):
        """Возвращает ответ без пароля после регистрации."""
        return UserCreateResponseSerializer(
            instance,
            context=self.context,
        ).data


class UserCreateResponseSerializer(serializers.ModelSerializer):
    """Сериализует пользователя в ответе после регистрации."""

    class Meta:
        """Определяет поля ответа после регистрации."""

        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name')
        read_only_fields = fields


class UserSerializer(serializers.ModelSerializer):
    """Сериализует профиль пользователя."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(read_only=True)

    class Meta:
        """Определяет поля профиля пользователя."""

        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )
        read_only_fields = fields

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь на автора."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return Subscription.objects.filter(
            user=request.user,
            author=obj,
        ).exists()


class AvatarSerializer(serializers.Serializer):
    """Сериализует загрузку и ответ с аватаром пользователя."""

    avatar = Base64ImageField()

    def update(self, instance, validated_data):
        """Обновляет аватар пользователя."""
        if instance.avatar:
            instance.avatar.delete(save=False)
        instance.avatar = validated_data['avatar']
        instance.save(update_fields=('avatar',))
        return instance

    def create(self, validated_data):
        """Не создаёт отдельные объекты для аватара."""
        raise NotImplementedError(
            'Аватар обновляется у существующего пользователя.'
        )

    def to_representation(self, instance):
        """Возвращает ссылку на сохранённый аватар."""
        field = Base64ImageField(read_only=True, context=self.context)
        return {'avatar': field.to_representation(instance.avatar)}


class SetPasswordSerializer(serializers.Serializer):
    """Сериализует смену пароля текущего пользователя."""

    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_current_password(self, value):
        """Проверяет текущий пароль пользователя."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Текущий пароль указан неверно.')
        return value

    def validate_new_password(self, value):
        """Проверяет новый пароль стандартными валидаторами Django."""
        try:
            validate_password(value, self.context['request'].user)
        except DjangoValidationError as error:
            raise serializers.ValidationError(list(error.messages))
        return value

    def save(self, **kwargs):
        """Сохраняет новый пароль пользователя."""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save(update_fields=('password',))
        return user


class TagSerializer(serializers.ModelSerializer):
    """Сериализует тег рецепта."""

    class Meta:
        """Определяет поля тега."""

        model = Tag
        fields = ('id', 'name', 'slug')
        read_only_fields = fields


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализует ингредиент из справочника."""

    class Meta:
        """Определяет поля ингредиента."""

        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = fields


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализует ингредиент внутри рецепта."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        """Определяет поля ингредиента в рецепте."""

        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = fields


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """Сериализует краткую информацию о рецепте."""

    image = Base64ImageField(read_only=True)

    class Meta:
        """Определяет поля краткого рецепта."""

        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields


class UserWithRecipesSerializer(UserSerializer):
    """Сериализует автора вместе с его рецептами для подписок."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        """Определяет поля автора с рецептами."""

        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes_count(self, obj):
        """Возвращает общее количество рецептов автора."""
        return obj.recipes.count()

    def get_recipes(self, obj):
        """Возвращает рецепты автора с учётом параметра recipes_limit."""
        request = self.context.get('request')
        recipes = obj.recipes.all()
        limit = request.query_params.get('recipes_limit') if request else None
        if limit:
            try:
                recipes = recipes[:int(limit)]
            except ValueError:
                recipes = recipes.none()
        return RecipeMinifiedSerializer(
            recipes,
            many=True,
            context=self.context,
        ).data


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализует полную информацию о рецепте."""

    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(
        source='recipe_ingredients',
        many=True,
        read_only=True,
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField(read_only=True)

    class Meta:
        """Определяет поля полного рецепта."""

        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )
        read_only_fields = fields

    def _has_user_relation(self, obj, model):
        """Проверяет наличие связи рецепта с текущим пользователем."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return model.objects.filter(user=request.user, recipe=obj).exists()

    def get_is_favorited(self, obj):
        """Проверяет, находится ли рецепт в избранном."""
        return self._has_user_relation(obj, Favorite)

    def get_is_in_shopping_cart(self, obj):
        """Проверяет, находится ли рецепт в списке покупок."""
        return self._has_user_relation(obj, ShoppingCart)


class IngredientAmountSerializer(serializers.Serializer):
    """Сериализует ингредиент и количество для записи рецепта."""

    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)


class RecipeWriteBaseSerializer(serializers.ModelSerializer):
    """Базовый сериализатор создания и изменения рецепта."""

    ingredients = IngredientAmountSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
    )

    class Meta:
        """Определяет поля записи рецепта."""

        model = Recipe
        fields = (
            'id',
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )
        read_only_fields = ('id',)

    def validate_ingredients(self, value):
        """Проверяет ингредиенты рецепта на корректность."""
        if not value:
            raise serializers.ValidationError(
                'Нужно выбрать хотя бы один ингредиент.'
            )
        ingredient_ids = [item['id'] for item in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться.'
            )
        existing_ids = set(
            Ingredient.objects.filter(id__in=ingredient_ids)
            .values_list('id', flat=True)
        )
        missing_ids = set(ingredient_ids) - existing_ids
        if missing_ids:
            raise serializers.ValidationError(
                'Указан несуществующий ингредиент.'
            )
        return value

    def validate_tags(self, value):
        """Проверяет теги рецепта на пустоту и повторы."""
        if not value:
            raise serializers.ValidationError(
                'Нужно выбрать хотя бы один тег.'
            )
        tag_ids = [tag.id for tag in value]
        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError('Теги не должны повторяться.')
        return value

    def validate_name(self, value):
        """Проверяет, что название рецепта не пустое."""
        if not value.strip():
            raise serializers.ValidationError('Название не может быть пустым.')
        return value

    def validate_text(self, value):
        """Проверяет, что описание рецепта не пустое."""
        if not value.strip():
            raise serializers.ValidationError('Описание не может быть пустым.')
        return value

    def _save_ingredients(self, recipe, ingredients_data):
        """Сохраняет ингредиенты рецепта без дублирования кода."""
        ingredients = Ingredient.objects.in_bulk(
            [item['id'] for item in ingredients_data]
        )
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredients[item['id']],
                amount=item['amount'],
            )
            for item in ingredients_data
        )

    @transaction.atomic
    def create(self, validated_data):
        """Создаёт рецепт, теги и ингредиенты."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self._save_ingredients(recipe, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        """Обновляет рецепт, теги и ингредиенты."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        instance.tags.set(tags)
        instance.recipe_ingredients.all().delete()
        self._save_ingredients(instance, ingredients)
        return instance

    def to_representation(self, instance):
        """Возвращает рецепт в полном формате после записи."""
        return RecipeReadSerializer(instance, context=self.context).data


class RecipeCreateSerializer(RecipeWriteBaseSerializer):
    """Сериализует создание рецепта."""

    image = Base64ImageField()


class RecipeUpdateSerializer(RecipeWriteBaseSerializer):
    """Сериализует изменение рецепта без обязательной замены изображения."""

    image = Base64ImageField(required=False)


class RecipeRelationSerializer(RecipeMinifiedSerializer):
    """Сериализует рецепт после добавления в список пользователя."""

    class Meta(RecipeMinifiedSerializer.Meta):
        """Определяет поля краткого ответа для списков пользователя."""

        fields = RecipeMinifiedSerializer.Meta.fields
