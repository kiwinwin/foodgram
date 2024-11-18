from django.contrib.auth import get_user_model
from django.db.models import Q
#from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, filters, mixins, status, serializers
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from foodgram.models import (Ingredients,
                             Tags,
                             IngredientsAmount,
                             Recipe,
                             RecipeTags,
                             FavoriteRecipe,
                             IncartRecipe,
                             Subscription)
from api.serializers import (IngredientsSerializer,
                             TagsSerializer,
                             RecipeCreateSerializer,
                             
                             IngredientsAmountCreateSerializer,
                             IngredientsAmountSerializer,
                             FavoriteRecipeSerializer,
                             ShortRecipeSerializer,
                             IncartRecipeSerializer
)
from api.permissions import IsAuthenticatedOrAuthorOrReadOnly

User = get_user_model()


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    
    serializer_class = IngredientsSerializer

    def get_queryset(self):
        queryset = Ingredients.objects.all()
        name = self.request.query_params.get('name')
        if name is not None:
            queryset = queryset.filter(name__startswith=name)
        return queryset


class TagsViewSet(viewsets.ReadOnlyModelViewSet):
    
    queryset = Tags.objects.all()
    serializer_class = TagsSerializer


class RecipesViewSet(viewsets.ModelViewSet):

    #pagination_class = LimitOffsetPagination
    serializer_class = RecipeCreateSerializer
    permission_classes = (IsAuthenticatedOrAuthorOrReadOnly,)
    pagination_class = PageNumberPagination
    #queryset = Recipe.objects.all()

    def get_queryset(self):
        queryset = Recipe.objects.all()
        query_dict = self.request.query_params.copy()
        author = query_dict.get('author')
        if author is not None:
            queryset = Recipe.objects.filter(author=author)
            return queryset
        return queryset
        '''tags=query_dict.pop('tags')
        print(tags)
        print(len(tags))
        if tags is not None:
            #tags_queryset = Recipe.objects.filter(tags__slug=tags[0])
            for tag in tags:
                tags_queryset = Recipe.objects.filter(tags__slug=tag)
                tags_queryset = tags_queryset.union
            queryset = tags_queryset
            print(queryset)
            return queryset
            #print(recipe_tags_queryset)'''
        


    '''def get_queryset(self):
        queryset = Recipe.objects.all()
        query_dict = self.request.query_params.copy()
        print(query_dict)
        author = query_dict.get('author')
        tags = query_dict.pop('tags')
        print(author)
        print(tags)
        print(query_dict)
        if author is not None:
            author_queryset = Recipe.objects.filter(author=author)
            queryset = author_queryset
        if tags is not None:
            tags_queryset = Recipe.objects.filter(tags__slug=tags[0])
            for tag in tags:
                tags_queryset.union(Recipe.objects.filter(tags__slug=tag))
            queryset = tags_queryset
        if (author and tags) is not None:
            queryset = tags_queryset.union(author_queryset)
        return queryset'''

    ''' tags = query_dict.pop('tags')
        tags_queryset = Recipe.objects.filter(tags__slug=tags[0])
        for tag in tags:
            tags_queryset.union(Recipe.objects.filter(tags__slug=tag))
        print(query_dict)
        print(tags)
        return tags_queryset'''
    @action(
        detail=True,
        methods=("POST", "DELETE",),
        permission_classes=(IsAuthenticated,),
    )
    def favorite(self, request, *args, **kwargs):
        user = request.user
        recipe_id = self.kwargs.get('pk')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        if request.method == "POST":
            serializer = FavoriteRecipeSerializer(data={
                "user": user.id,
                "recipe": recipe_id}, )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            serializer = ShortRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if FavoriteRecipe.objects.filter(
            user=user.id, recipe=recipe_id).exists():
            instance = FavoriteRecipe.objects.filter(user=user.id, recipe=recipe_id)
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        raise serializers.ValidationError()
    
    @action(
        detail=True,
        methods=("POST", "DELETE",),
        permission_classes=(IsAuthenticated,),
    )
    def shopping_cart(self, request, *args, **kwargs):
        user = request.user
        recipe_id = self.kwargs.get('pk')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        if request.method == "POST":
            serializer = IncartRecipeSerializer(data={
                "user": user.id,
                "recipe": recipe_id}, )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            serializer = ShortRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if IncartRecipe.objects.filter(
            user=user.id, recipe=recipe_id).exists():
            instance = IncartRecipe.objects.filter(user=user.id, recipe=recipe_id)
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        raise serializers.ValidationError()

    @action(
        detail=True,
        methods=("GET",),
        permission_classes=(AllowAny,),
        url_path='get-link'
    )
    def get_link(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get('pk')
        get_object_or_404(Recipe, id=recipe_id)
        shor_link = request.build_absolute_uri()
        return Response({
            "short-link": shor_link
        },
        status=status.HTTP_200_OK)


class IngredientsAmountViewSet(viewsets.ModelViewSet):
    
    queryset = IngredientsAmount.objects.all()
    #serializer_class = IngredientsAmountCreateSerializer
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return IngredientsAmountSerializer
        else:
            return IngredientsAmountCreateSerializer