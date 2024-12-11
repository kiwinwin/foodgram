from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from api.permissions import IsAuthenticatedOrAuthorOrReadOnly
from api.serializers import (IngredientSerializer,
                             TagsSerializer,
                             RecipeSerializer,
                             FavoriteRecipeSerializer,
                             ShortRecipeSerializer,
                             IncartRecipeSerializer)
from foodgram_project.pagination import Pagination
from foodgram.models import (Ingredient,
                             Tag,
                             IngredientAmount,
                             Recipe,
                             RecipeIngredient,
                             FavoriteRecipe,
                             IncartRecipe,)


User = get_user_model()


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    """Class for ingredients ViewSet."""

    serializer_class = IngredientSerializer

    def get_queryset(self):
        queryset = Ingredient.objects.all()
        name = self.request.query_params.get("name")
        if name is not None:
            queryset = queryset.filter(name__startswith=name)
        return queryset


class TagsViewSet(viewsets.ReadOnlyModelViewSet):
    """Class for tags ViewSet."""

    queryset = Tag.objects.all()
    serializer_class = TagsSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    """Class for recipes ViewSet."""

    permission_classes = (IsAuthenticatedOrAuthorOrReadOnly,)
    pagination_class = Pagination
    model = Recipe

    def is_favorite_incart_filter(self, queryset, filterword, filtermodel):
        """Method for filtering queryset."""
        if filterword is not None:
            ids = []
            if bool(int(filterword)):
                for obj in filtermodel.objects.filter(
                    user=self.request.user.id):
                    ids.append(obj.item.id)
                queryset = queryset.filter(id__in=ids)
        return queryset

    def get_queryset(self):
        queryset = Recipe.objects.all()
        query_dict = self.request.query_params.copy()
        author = query_dict.get("author")
        is_favorited = query_dict.get("is_favorited")
        is_in_shopping_cart = query_dict.get("is_in_shopping_cart")
        if author is not None:
            queryset = queryset.filter(author=author)
        queryset = self.is_favorite_incart_filter(
            queryset=queryset, filterword=is_favorited,
            filtermodel=FavoriteRecipe)
        queryset = self.is_favorite_incart_filter(
            queryset=queryset, filterword=is_in_shopping_cart,
            filtermodel=IncartRecipe)
        if "tags" in query_dict:
            tags = query_dict.pop("tags")
            tag_ids = []
            for tag in tags:
                tag_ids.append(Tag.objects.get(slug=tag).id)
            queryset = queryset.filter(tags__in=tag_ids).distinct()
        return queryset

    def get_serializer_class(self):
        serializer = RecipeSerializer
        if self.action == "favorite":
            serializer = FavoriteRecipeSerializer
        if self.action == "shopping_cart":
            serializer = IncartRecipeSerializer
        return serializer

    def partial_update(self, request):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def favorite_incart(self, request, through_model, result_serializer, *args, **kwargs):
        """Method for favorite, incart, subscribe actions."""
        user = request.user
        item_id = self.kwargs.get("pk")
        item = get_object_or_404(self.model, id=item_id)
        if request.method == "POST":
            serializer = self.get_serializer(
                data={
                    "user": user.id,
                    "item": item_id}, )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            serializer = result_serializer(item, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if through_model.objects.filter(user=user.id, item=item_id).exists():
            instance = through_model.objects.filter(user=user.id, item=item_id)
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        raise serializers.ValidationError()

    @action(
        detail=True,
        methods=("POST", "DELETE",),
        permission_classes=(IsAuthenticated,),)
    def favorite(self, request, *args, **kwargs):
        """Method for users favorite recipe."""
        through_model = FavoriteRecipe
        result_serializer = ShortRecipeSerializer
        result = self.favorite_incart(
            request, through_model, result_serializer, *args, **kwargs)
        return result

    @action(
        detail=True,
        methods=("POST", "DELETE",),
        permission_classes=(IsAuthenticated,),)
    def shopping_cart(self, request, *args, **kwargs):
        """Method for users recipes in cart."""
        through_model = IncartRecipe
        result_serializer = ShortRecipeSerializer
        result = self.favorite_incart(
            request, through_model, result_serializer, *args, **kwargs)
        return result

    @action(
        detail=False,
        methods=("GET",),
        permission_classes=(IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        """Method for downloading users
        in cart recipes ingredients."""
        user = request.user
        queryset = IncartRecipe.objects.filter(user=user.id)
        recipes = []
        ingredients_amount = []
        for obj in queryset:
            recipes.append(obj.item.id)
        for recipe in recipes:
            recipe_filter_qs = RecipeIngredient.objects.filter(recipe=recipe)
            for obj in recipe_filter_qs:
                ingredients_amount.append(obj.ingredient.id)
        result = {}
        for ingredient_amount in ingredients_amount:
            obj = IngredientAmount.objects.get(id=ingredient_amount)
            if (obj.ingredient.name,
                obj.ingredient.measurement_unit) in result:
                old_value = result[obj.ingredient.name,
                                   obj.ingredient.measurement_unit]
                result[obj.ingredient.name, obj.ingredient.measurement_unit] =\
                    old_value + obj.amount
            else:
                result[obj.ingredient.name,
                       obj.ingredient.measurement_unit] = obj.amount
        str_result = "Список покупок \n"
        file_name = "shopping_list.txt"
        for key, value in result.items():
            str_result += key[0] + " (" + key[1] + ") — " + str(value) + "\n"
        with open(file_name, "w", encoding="utf-8") as file:
            file.write(str_result,)
        with open(file_name, encoding="utf-8") as file:
            response = HttpResponse(
                file, content_type="text/plain; charset=utf-8"
            )
            response["Content-Disposition"] = \
                f"attachment; filename={file_name}"
            return response

    @action(
        detail=True,
        methods=("GET",),
        permission_classes=(AllowAny,),
        url_path="get-link"
    )
    def get_link(self, request):
        """Method for getting recipes short link."""
        recipe_id = self.kwargs.get("pk")
        get_object_or_404(Recipe, id=recipe_id)
        short_link = request.build_absolute_uri().replace(
            "api/", "").replace("get-link/", "")
        return Response({
            "short-link": short_link},
            status=status.HTTP_200_OK)
