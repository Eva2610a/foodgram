from rest_framework import status
from rest_framework.response import Response


class IsSubscribedMixin:
    """Проверка подписки пользователя на автора."""

    def get_is_subscribed(self, obj):
        request = self.context.get('request')

        if request and hasattr(
            request, 'user'
        ) and request.user.is_authenticated:

            return obj.follower.filter(
                user=request.user
            ).exists()

        return False


class RecipeActionMixin:
    """Добавление или удаления рецепта избранного или корзины."""

    def check_recipe_action(self, request, model, serializer_class):
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            obj, created = model.objects.get_or_create(
                user=user, recipe=recipe)

            if not created:
                return Response(
                    {'detail': 'Такой рецепт уже присутствует'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            data = serializer_class(recipe, context={'request': request}).data
            return Response(data, status=status.HTTP_201_CREATED)

        obj = model.objects.filter(user=user, recipe=recipe).first()

        if not obj:
            return Response(
                {'detail': 'Рецепт не найден.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
