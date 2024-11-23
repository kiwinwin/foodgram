from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from api.views import (IngredientsViewSet, TagsViewSet, RecipesViewSet,)

router = DefaultRouter()

router.register(r'tags', TagsViewSet, basename='tags')
router.register(r'ingredients', IngredientsViewSet, basename='ingredients')
router.register(r'recipes', RecipesViewSet, basename='recipes')


urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]

'''if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)'''