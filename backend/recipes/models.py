from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

User = get_user_model()


class Tag(models.Model):
    """Модель тега."""

    name = models.CharField(
        max_length=35,
        unique=True,
        verbose_name="Название тега"
    )
    slug = models.SlugField(
        max_length=150,
        unique=True,
        verbose_name="Уникальный слаг"
    )

    class Meta:
        """Класс мета."""

        verbose_name = "Тег"
        verbose_name_plural = "Теги"
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'slug'),
                name='unique_tags',
            ),
        )

    def __str__(self):
        """Метод строкового представления модели."""
        return self.name


class Ingredient(models.Model):
    """Модель описания ингридиента."""

    name = models.CharField(
        max_length=150,
        db_index=True,
        verbose_name="Название ингредиента"
    )
    measurement_unit = models.CharField(
        max_length=150,
        verbose_name="Ед. измерения"
    )

    class Meta:
        """Класс мета."""

        ordering = ('name',)
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"

    def __str__(self):
        """Метод строкового представления модели."""
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    """Модель описания рецепта."""

    author = models.ForeignKey(
        User,
        related_name="recipes",
        on_delete=models.CASCADE,
        verbose_name="Автор рецепта"
    )
    name = models.CharField(
        max_length=150,
        verbose_name="Название рецепта"
    )
    image = models.ImageField(
        verbose_name="Фотография рецепта",
        upload_to='recipes/',
        blank=True
    )
    text = models.TextField(
        verbose_name="Описание рецепта"
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through="IngredientInRecipe",
        related_name="recipes",
        verbose_name="Ингредиенты"
    )
    tags = models.ManyToManyField(
        Tag,
        related_name="recipes",
        verbose_name="Теги"
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления',
        validators=[
            MinValueValidator(1, message='Минимальное значение 1!'),
        ]
    )
    created = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Дата публикации рецепта'
    )

    class Meta:
        """Класс мета."""

        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-created',)

    def __str__(self):
        """Метод строкового представления модели."""
        return self.name


class IngredientInRecipe(models.Model):
    """Кол-во ингредиентов в отдельных рецептах."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="ingredient_list",
        verbose_name="Рецепт"
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name="Ингредиент",
        related_name="in_recipe"
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name="Количество",
        validators=[
            MinValueValidator(1, message="Минимальное кол-во 1.")
        ]
    )

    class Meta:
        """Класс мета."""

        verbose_name = "Ингредиенты в рецепте"
        verbose_name_plural = "Ингредиенты в рецептах"
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name="unique_ingredients_in_the_recipe"
            )
        ]

    def __str__(self):
        """Метод строкового представления модели."""
        return f'{self.ingredient} {self.recipe}'


class TagInRecipe(models.Model):
    """Теги рецептов."""

    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        verbose_name="Теги"
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт"
    )

    class Meta:
        """Класс мета."""

        verbose_name = "Тег рецепта"
        verbose_name_plural = "Теги рецепта"
        constraints = [
            models.UniqueConstraint(fields=['tag', 'recipe'],
                                    name='unique_tagrecipe')
        ]

    def __str__(self):
        """Метод строкового представления модели."""
        return f'{self.tag} {self.recipe}'


class ShoppingCart(models.Model):
    """Корзина покупок."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="shopping_user",
        verbose_name="Пользователь"
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="shopping_recipe",
        verbose_name="Рецепт"
    )

    class Meta:
        """Класс мета."""

        verbose_name = "Список покупок"
        verbose_name_plural = "Списки покупок"
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_shoppingcart'
            )
        ]

    def __str__(self):
        """Метод строкового представления модели."""
        return f'{self.user} {self.recipe}'


class Follow(models.Model):
    """Подписки на автора."""

    author = models.ForeignKey(
        User,
        related_name="follow",
        on_delete=models.CASCADE,
        verbose_name="Автор рецепта",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="follower",
        verbose_name="Подписчик"
    )

    class Meta:
        """Класс мета."""

        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'], name='unique_follow'
            )
        ]

    def __str__(self):
        """Метод строкового представления модели."""
        return f'{self.user} {self.author}'


class Favorite(models.Model):
    """Избранное."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="Пользователь"
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="Рецепт"
    )

    class Meta:
        """Класс мета."""

        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_favorite'
            )
        ]

    def __str__(self):
        """Метод строкового представления модели."""
        return f'{self.user} {self.recipe}'
