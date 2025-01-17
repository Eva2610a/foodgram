import base64
from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from api.mixins import IsSubscribedMixin
from recipes.models import (Ingredient,
                            IngredientInRecipe,
                            Recipe,
                            Tag
                            )
from users.models import User
from constant import MAXLEN, MESSAGE, MES_MAX


class Base64ImageField(serializers.ImageField):
    """Кастомное поле для кодирования изображения в base64."""

    def to_internal_value(self, data):
        """Преобразование картинки."""
        if isinstance(data, str) and data.startswith("data:image"):
            format, imgstr = data.split(";base64,")
            ext = format.split("/")[-1]
            data = ContentFile(base64.b64decode(imgstr), name="photo." + ext)

        return super().to_internal_value(data)


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Регистрация новых пользователей."""

    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    first_name = serializers.CharField(MAXLEN, required=True)
    last_name = serializers.CharField(MAXLEN, required=True)

    class Meta:
        model = User
        fields = (
            "email", "id", "username", "first_name", "last_name", "password"
        )
        extra_kwargs = {
            "password": {"write_only": True}
        }

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer, IsSubscribedMixin):
    """Представление информации о пользователях."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email", "id", "username", "first_name",
            "last_name", "is_subscribed", "avatar"
        )


class PasswordSetSerializer(serializers.Serializer):
    new_password = serializers.CharField(style={"input_type": "password"},
                                         required=True)
    current_password = serializers.CharField(style={"input_type": "password"},
                                             required=True)


class RecipeShortSerializer(serializers.ModelSerializer):
    """Краткое представления рецептов."""
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class UserSubscriptionSerializer(
        serializers.ModelSerializer, IsSubscribedMixin):
    """
    Сериализатор для отображения информации
    о подписках пользователя на других авторов.
    """

    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email", "id", "username", "first_name", "last_name",
            "is_subscribed", "recipes", "recipes_count", "avatar"
        )

    def get_recipes(self, obj):

        recipes_limit = self.context.get("recipes_limit")

        if recipes_limit is not None:
            try:
                recipes_limit = int(recipes_limit)
            except ValueError:
                raise serializers.ValidationError(
                    "recipes_limit должен быть числом.")

        recipes = obj.recipes
        if recipes_limit:
            recipes = recipes[:recipes_limit]

        return RecipeShortSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с тегами."""

    class Meta:
        model = Tag
        fields = ("id", "name", "slug")


class AvatarSerializer(serializers.ModelSerializer):
    """Обработка аватара пользователя."""

    avatar = Base64ImageField(max_length=None, use_url=True)

    class Meta:
        model = User
        fields = ["avatar"]

    def validate(self, data):

        if "avatar" not in data:
            raise serializers.ValidationError(
                {"avatar": "Это поле обязательно для заполнения."}
            )
        return data


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Работа с ингредиентами, использующимися в рецептах."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source="ingredient.id"
    )
    name = serializers.CharField(source="ingredient.name", read_only=True)
    measurement_unit = serializers.CharField(
        source="ingredient.measurement_unit", read_only=True
    )
    amount = serializers.IntegerField(max_value=MES_MAX, min_value=MESSAGE)

    class Meta:
        model = IngredientInRecipe
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeSerializer(serializers.ModelSerializer):
    """Основной сериализатор для рецептов."""

    cooking_time = serializers.IntegerField(
        max_value=MES_MAX, min_value=MESSAGE
    )
    image = Base64ImageField(max_length=None, use_url=True)
    ingredients = IngredientInRecipeSerializer(
        source="ingredient_list", many=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "cooking_time",
            "image",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "text",
            "name"
        )
        read_only_fields = ("author",)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["tags"] = TagSerializer(
            instance.tags.all(), many=True).data
        representation["author"] = UserSerializer(
            instance.author, context=self.context
        ).data

        return representation

    def validate(self, data):
        request = self.context.get("request")

        if request and request.method == "PATCH":

            if "tags" not in data:
                raise serializers.ValidationError({
                    "tags": "Поле tags обязательно."
                })
            if "ingredient_list" not in data:
                raise serializers.ValidationError({
                    "ingredients": "Поле ingredients обязательно."
                })

        return data

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError("Поле не должно быть пустым.")

        ingredient_ids = [ingredient["ingredient"]["id"]
                          for ingredient in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                "Список ингредиентов содержит дубликаты.")

        return ingredients

    def validate_tags(self, tags):
        if not tags:
            raise serializers.ValidationError("Поле не должно быть пустым.")

        tag_ids = [tag.id for tag in tags]
        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError(
                "Список тегов содержит дубликаты.")

        return tags

    def _process_ingredients(self, recipe, ingredients_data):

        recipe.ingredients.clear()

        ingredient_instances = [
            IngredientInRecipe(
                recipe=recipe,
                ingredient=ingredient_data["ingredient"]["id"],
                amount=ingredient_data["amount"]
            )
            for ingredient_data in ingredients_data
        ]
        IngredientInRecipe.objects.bulk_create(ingredient_instances)

    def create(self, validated_data):
        tags = validated_data.pop("tags")
        ingredients_data = validated_data.pop("ingredient_list")

        recipe = Recipe.objects.create(**validated_data)
        self._process_ingredients(recipe, ingredients_data)
        recipe.tags.set(tags)

        return recipe

    def update(self, instance, validated_data):
        tags_data = validated_data.pop("tags", None)
        ingredients_data = validated_data.pop("ingredient_list", None)

        instance = super().update(instance, validated_data)

        if tags_data is not None:
            instance.tags.set(tags_data)

        if ingredients_data is not None:
            self._process_ingredients(instance, ingredients_data)

        return instance

    def get_is_favorited(self, obj):
        user = self.context["request"].user
        if user.is_authenticated:
            return user.favorites.filter(recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context["request"].user
        if user.is_authenticated:
            return user.shopping_user.filter(recipe=obj).exists()
        return False


class FavoriteShoppingCartSerializer(serializers.ModelSerializer):
    """Избранные рецепты и корзина."""

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")
