from django.urls import include, path
from rest_framework.routers import DefaultRouter
from users.views import CustomUserViewSet
from views import IngredientsViewSet, RecipeViewSet, TagsViewSet

router = DefaultRouter()

router.register(r"tags", TagsViewSet, basename="tags")
router.register(r"ingredients", IngredientsViewSet, basename="ingredients")
router.register(r"recipes", RecipeViewSet, basename="recipes")
router.register(r"users", CustomUserViewSet, basename="users")


urlpatterns = [
    path("", include(router.urls)),
    path("auth/", include("djoser.urls")),
    path("auth/", include("djoser.urls.authtoken")),
]
