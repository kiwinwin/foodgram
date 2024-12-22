from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (CustomUserViewSet, IngredientsViewSet, RecipeViewSet,
                    TagsViewSet, TokenViewSet)

router = DefaultRouter()

router.register(r"tags", TagsViewSet, basename="tags")
router.register(r"ingredients", IngredientsViewSet, basename="ingredients")
router.register(r"recipes", RecipeViewSet, basename="recipes")
router.register(r"users", CustomUserViewSet, basename="users")
router.register(r"auth", TokenViewSet, basename="auth")


urlpatterns = [
    path("", include(router.urls))
]
