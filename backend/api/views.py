from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from api.permissions import IsAuthenticatedOrAuthorOrReadOnly
from api.serializers import (IngredientsSerializer,
                             TagsSerializer,
                             RecipeCreateSerializer,
                             IngredientsAmountCreateSerializer,
                             IngredientsAmountSerializer,
                             FavoriteRecipeSerializer,
                             ShortRecipeSerializer,
                             IncartRecipeSerializer
)
from foodgram.models import (Ingredients,
                             Tags,
                             IngredientsAmount,
                             Recipe,
                             RecipeIngredients,
                             FavoriteRecipe,
                             IncartRecipe,)



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

    serializer_class = RecipeCreateSerializer
    permission_classes = (IsAuthenticatedOrAuthorOrReadOnly,)
    pagination_class = PageNumberPagination

    def get_queryset(self):
        queryset = Recipe.objects.all()
        query_dict = self.request.query_params.copy()
        limit = query_dict.get('limit')
        author = query_dict.get('author')
        is_favorited = query_dict.get('is_favorited')
        is_in_shopping_cart = query_dict.get('is_in_shopping_cart')
        if 'tags' in query_dict:
            tag_ids = []
            tags = query_dict.pop('tags')
            for tag in tags:
                tag_ids.append(Tags.objects.get(slug=tag).id)
            return Recipe.objects.filter(tags__in=tag_ids)
        if author is not None:
            queryset = Recipe.objects.filter(author=author)
            return queryset
        if limit is not None:
            return queryset[:int(limit)]
        if is_favorited is not None:
            fav_ids = []
            if bool(int(is_favorited)):
                for obj in FavoriteRecipe.objects.filter(user=self.request.user.id):
                    fav_ids.append(obj.recipe.id)
                return Recipe.objects.filter(id__in=fav_ids)
        if is_in_shopping_cart is not None:
            incart_ids = []
            if bool(int(is_in_shopping_cart)):
                for obj in IncartRecipe.objects.filter(user=self.request.user.id):
                    incart_ids.append(obj.recipe.id)
                return Recipe.objects.filter(id__in=incart_ids)
        return queryset

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
        detail=False,
        methods=("GET",),
        permission_classes=(IsAuthenticated,),
    )
    def download_shopping_cart(self, request, *args, **kwargs):
        user = request.user
        queryset = IncartRecipe.objects.filter(user=user.id)
        recipes = []
        ingredients_amount = []
        for obj in queryset:
            recipes.append(obj.recipe.id)
        for recipe in recipes:
            recipe_filter_qs = RecipeIngredients.objects.filter(recipe=recipe)
            for obj in recipe_filter_qs:
                ingredients_amount.append(obj.ingredient.id)
        result = {}
        print(recipes)
        print(ingredients_amount)
        for ingredient_amount in ingredients_amount:
            obj = IngredientsAmount.objects.get(id=ingredient_amount)
            if (obj.ingredient.name, obj.ingredient.measurement_unit) in result:
                old_value = result[obj.ingredient.name, obj.ingredient.measurement_unit]
                result[obj.ingredient.name, obj.ingredient.measurement_unit] = old_value + obj.amount
            else:
                result[obj.ingredient.name, obj.ingredient.measurement_unit] = obj.amount
        print(result)
        str_result = 'Список покупок \n'
        for key, value in result.items():
            str_result += key[0] + ' (' + key[1] + ') — ' + str(value) + '\n'
        print(str_result)
        with open('purchase_list.txt', 'w', encoding='utf-8') as file:
            file.write(str_result,)
            file.close()
        return Response(status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=("GET",),
        permission_classes=(AllowAny,),
        url_path='get-link'
    )
    def get_link(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get('pk')
        get_object_or_404(Recipe, id=recipe_id)
        short_link = request.build_absolute_uri()
        return Response({
            "short-link": short_link
        },
        status=status.HTTP_200_OK)


class IngredientsAmountViewSet(viewsets.ModelViewSet):
    
    queryset = IngredientsAmount.objects.all()
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return IngredientsAmountSerializer
        else:
            return IngredientsAmountCreateSerializer