from django.urls import include, path
from rest_framework import routers
from djoser import views as djoser_views

from . import views
from .views import (
    IngredientViewSet, TagViewSet, RecipeViewSet,
    UserViewSet, redirect_to_recipe
)


router = routers.DefaultRouter()
router.register("ingredients", IngredientViewSet, basename="ingredients")
router.register("tags", TagViewSet, basename="tags")
router.register("users", UserViewSet, basename="users")
router.register("recipes", RecipeViewSet, basename="recipes")

name_app = "api"

urlpatterns = [
    path("", include(router.urls)),
    path("", include("djoser.urls")),
    path("auth/", include("djoser.urls.authtoken")),
    path(
        "users/me/avatar/", views.UserAvatarView.as_view(), name="user-avatar"
    ),
    path(
        "users/me/", views.UserSelfView.as_view(), name="user-self"
    ),
    path(
        "users/set_password/",
        djoser_views.UserViewSet.as_view({"post": "set_password"}),
        name="user-set-password"
    ),
    path("s/<str:short_id>/", redirect_to_recipe, name="short-link-redirect"),

]
