import csv
from io import StringIO

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny,
                                        IsAuthenticated,
                                        IsAuthenticatedOrReadOnly
                                        )
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from api.filters import IngredientFilter, RecipeFilter
from api.pagination import CustomPagination
from api.permissions import IsAuthorOrReadOnly
from api.mixins import RecipeActionMixin
from recipes.models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
    Follow,
    Tag
)
from .serializer import (
    AvatarSerializer,
    FavoriteShoppingCartSerializer,
    IngredientSerializer,
    RecipeSerializer,
    TagSerializer,
    UserRegistrationSerializer,
    UserSerializer,
    UserSubscriptionSerializer,
    PasswordSetSerializer
)

User = get_user_model()


def redirect_to_recipe(request, short_code):
    """Перенаправление на полный URL рецепта по короткому коду."""
    recipe = get_object_or_404(Recipe, short_code=short_code)
    return redirect(f'/recipes/{recipe.id}')


class UserViewSet(ModelViewSet):
    """Управление пользователями."""

    permission_classes = (AllowAny,)
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegistrationSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=['get'],
            permission_classes=(IsAuthenticated,))
    def me(self, request):
        serializer = UserSerializer(request.user,
                                    context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def set_password(self, request):
        serializer = PasswordSetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if user.check_password(serializer.data.get('current_password')):
            user.set_password(serializer.data.get('new_password'))
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'errors': 'Указан неверный пароль'},
                        status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, pk=None):
        target_user = self.get_object()
        current_user = request.user

        if request.method == 'DELETE':
            subscription = target_user.follower.filter(
                user=current_user
            ).first()

            if not subscription:
                return Response(
                    {'detail': 'Подписка не найдена.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        if target_user.follower.filter(
                user=current_user).exists():
            return Response(
                {'detail': 'Вы уже подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        Follow.objects.create(user=current_user, author=target_user)

        context = self.get_serializer_context()
        context['recipes_limit'] = request.query_params.get('recipes_limit')

        user_data = UserSubscriptionSerializer(
            target_user, context=context).data
        return Response(user_data, status=status.HTTP_201_CREATED)

    @action(
        detail=False,
        methods=['get'],
        url_path='subscriptions',
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        user = request.user
        author_ids = user.follow.values_list('author', flat=True)

        authors = User.objects.filter(id__in=author_ids)

        context = self.get_serializer_context()
        context['recipes_limit'] = request.query_params.get('recipes_limit')

        page = self.paginate_queryset(authors)
        if page is not None:
            serializer = UserSubscriptionSerializer(
                page, many=True, context=context
            )
            return self.get_paginated_response(serializer.data)

        serializer = UserSubscriptionSerializer(
            authors, many=True, context=context
        )
        return Response(serializer.data)


class UserSelfView(APIView):
    """получения данных аутентифицированного текущего пользователя."""

    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class UserAvatarView(APIView):
    """Работа с аватаром."""

    permission_classes = [IsAuthenticated]

    def put(self, request, *args, **kwargs):
        user = request.user
        serializer = AvatarSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            'avatar': request.build_absolute_uri(user.avatar.url)
        }, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        user = request.user
        user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(ModelViewSet):
    """Работы с тегами."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny, )
    http_method_names = ['get']
    pagination_class = None


class RecipeViewSet(ModelViewSet, RecipeActionMixin):
    """Управление рецептами."""

    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly, ]
    pagination_class = CustomPagination
    http_method_names = ['get', 'post', 'patch', 'delete']
    filter_backends = (DjangoFilterBackend, )
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        return self.check_recipe_action(
            request, Favorite, FavoriteShoppingCartSerializer
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        return self.check_recipe_action(
            request, ShoppingCart, FavoriteShoppingCartSerializer
        )

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link'
    )
    def get_link(self, request, pk=None):
        """Возвращает короткую ссылку на рецепт."""
        recipe = self.get_object()
        link = request.build_absolute_uri(f'/api/r/{recipe.short_code}')
        return Response({'short-link': link})

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        user = request.user
        ingredients = (
            IngredientInRecipe.objects
            .filter(recipe__in_shopping_cart__user=user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
            .order_by('ingredient__name')
        )

        output = StringIO()
        output.write('\ufeff')

        writer = csv.writer(output)
        writer.writerow(['Ингредиенты', 'Количество'])

        for ingredient in ingredients:
            name = ingredient['ingredient__name']
            unit = ingredient['ingredient__measurement_unit']
            total_amount = ingredient['total_amount']
            writer.writerow([f'{name} ({unit})', total_amount])

        response = HttpResponse(
            output.getvalue(), content_type='text/csv; charset=utf-8'
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.csv"'
        )
        return response

    @staticmethod
    def ingredients_to_txt(ingredients):
        """Объединение ингредиентов в список для загрузки"""

        shopping_list = ''
        for ingredient in ingredients:
            shopping_list += (
                f"{ingredient['ingredient__name']}  - "
                f"{ingredient['sum']}"
                f"({ingredient['ingredient__measurement_unit']})\n"
            )
        return shopping_list


class IngredientViewSet(ModelViewSet):
    """Управление ингредиентами."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    http_method_names = ['get']
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend, )
    pagination_class = None
    filterset_class = IngredientFilter
    search_fields = ('^name', )
