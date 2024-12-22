from collections import Counter

from django.contrib.auth import get_user_model, models
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from foodgram.models import (FavoriteRecipe, IncartRecipe, Ingredient,
                             IngredientAmount, Recipe, RecipeIngredient,
                             Subscription, Tag)

from .pagination import Pagination
from .permissions import IsAuthenticatedOrAuthorOrReadOnly
from .serializers import (FavoriteRecipeSerializer, FollowUserSerializer,
                          IncartRecipeSerializer, IngredientSerializer,
                          RecipeSerializer, ShoppingCartSerializer,
                          ShortRecipeSerializer, TagsSerializer,
                          TokenSerializer)
from .variables import USERS_SERIALIZERS

User = get_user_model()


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    """Class for ingredients ViewSet."""

    serializer_class = IngredientSerializer

    def get_queryset(self):
        queryset = Ingredient.objects.all()
        name = self.request.query_params.get("name").lower()
        if name is not None:
            queryset = queryset.filter(name__icontains=name)
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

    def get_queryset(self):
        queryset = Recipe.objects.all()
        user = self.request.user
        query_dict = self.request.query_params.copy()
        author = query_dict.get("author")
        is_favorited = query_dict.get("is_favorited")
        is_in_shopping_cart = query_dict.get("is_in_shopping_cart")
        if author is not None:
            queryset = queryset.filter(author=author)
        if user.__class__ is not models.AnonymousUser:
            if is_favorited is not None and bool(int(is_favorited)):
                queryset = queryset.filter(
                    id__in=user.favoriterecipes.all().values("item__id"))
            if (is_in_shopping_cart is not None
                    and bool(int(is_in_shopping_cart))):
                queryset = queryset.filter(
                    id__in=user.incartrecipes.all().values("item__id"))
        if "tags" in query_dict:
            tags = query_dict.pop("tags")
            queryset = queryset.filter(tags__slug__in=tags).distinct()
        return queryset

    def get_serializer_class(self):
        serializer = RecipeSerializer
        if self.action == "favorite":
            serializer = FavoriteRecipeSerializer
        if self.action == "shopping_cart":
            serializer = IncartRecipeSerializer
        return serializer

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def favorite_incart(self, request, through_model,
                        result_serializer, *args, **kwargs):
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
        return self.favorite_incart(
            request, through_model, result_serializer, *args, **kwargs)

    @action(
        detail=True,
        methods=("POST", "DELETE",),
        permission_classes=(IsAuthenticated,),)
    def shopping_cart(self, request, *args, **kwargs):
        """Method for users recipes in cart."""
        through_model = IncartRecipe
        result_serializer = ShortRecipeSerializer
        return self.favorite_incart(
            request, through_model, result_serializer, *args, **kwargs)

    @action(
        detail=False,
        methods=("GET",),
        permission_classes=(IsAuthenticated,),
    )
    def download_shopping_cart(self, request, *args, **kwargs):
        """Method for downloading users
        in cart recipes ingredients."""
        user = request.user
        queryset = user.incartrecipes.all()
        recipe_qs = queryset.values("item_id")
        ingredients_recipe = RecipeIngredient.objects.filter(
            recipe__in=recipe_qs).values_list(
                "ingredient_id", flat=True).order_by(
                    "ingredient__ingredient")
        amount_coeff = dict(Counter(ingredients_recipe))
        ingredient_amount = IngredientAmount.objects.filter(
            id__in=ingredients_recipe).order_by("ingredient__name")
        serializer = ShoppingCartSerializer(
            ingredient_amount,
            many=True)
        ids_stack = set()
        result = {}
        for item in serializer.data:
            amount = item["amount"] * amount_coeff[item["id"]]
            name, measure = (item["ingredient"]["name"],
                             item["ingredient"]["measurement_unit"])
            if item["ingredient"]["id"] in ids_stack:
                old_amount = result[name, measure]
                result[name, measure] = amount + old_amount
            else:
                result[name, measure] = amount
            ids_stack.add(item["ingredient"]["id"])
        str_result = "Список покупок \n"
        for key, value in result.items():
            str_result += f"{key[0]} ({key[1]}) — {value} \n"
        file_name = "shopping_list.txt"
        with open(file_name, "w", encoding="utf-8") as file:
            file.write(str_result,)
        with open(file_name, encoding="utf-8") as file:
            response = HttpResponse(
                file, content_type="text/plain; charset=utf-8"
            )
            response["Content-Disposition"] = (f"attachment;"
                                               f"filename={file_name}")
            return response

    @action(
        detail=True,
        methods=("GET",),
        permission_classes=(AllowAny,),
        url_path="get-link"
    )
    def get_link(self, request, *args, **kwargs):
        """Method for getting recipes short link."""
        recipe_id = self.kwargs.get("pk")
        get_object_or_404(Recipe, id=recipe_id)
        short_link = request.build_absolute_uri().replace(
            "api/", "").replace("get-link/", "")
        return Response({
            "short-link": short_link},
            status=status.HTTP_200_OK)


class CustomUserViewSet(viewsets.ModelViewSet):
    """ViewSet for User model."""

    queryset = User.objects.all()
    pagination_class = Pagination
    http_method_names = ["get", "post", "put", "delete"]
    lookup_field = "pk"
    model = User
    imported = RecipeViewSet

    def get_serializer_class(self):
        return USERS_SERIALIZERS[self.action]

    def subscribing(self, request, through_model,
                    result_serializer, *args, **kwargs):
        """Importing favorite_incart method."""
        return self.imported.favorite_incart(
            self, request, through_model, result_serializer, *args, **kwargs)

    @action(
        detail=False,
        methods=("GET", ),
        permission_classes=(IsAuthenticated,),
    )
    def me(self, request):
        """Getting users own profile."""
        user = request.user
        serializer = self.get_serializer(
            user, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=("PUT", "DELETE"),
        permission_classes=(IsAuthenticated,),
        url_path="me/avatar"
    )
    def avatar(self, request, *args, **kwargs):
        """Setting new users avatar."""
        instance = request.user
        if request.method == "PUT":
            serializer = self.get_serializer(
                instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        instance.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=("POST", ),
        permission_classes=(IsAuthenticated,),
    )
    def set_password(self, request, *args, **kwargs):
        """Setting new users password."""
        user = request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if user.check_password(serializer.data["current_password"]):
            request.user.set_password(serializer.data["new_password"])
            request.user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=("POST", "DELETE"),
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, *args, **kwargs):
        """Making and destroying users subscriptions."""
        through_model = Subscription
        result_serializer = FollowUserSerializer
        return self.subscribing(
            request, through_model,
            result_serializer, *args, **kwargs)

    @action(
        detail=False,
        methods=("GET",),
        permission_classes=(IsAuthenticated,),)
    def subscriptions(self, request, *args, **kwargs):
        """Method for getting users subscriptions list."""
        user = request.user
        queryset = user.follows.all()
        paginated_queryset = self.paginate_queryset(queryset)
        serializer = self.get_serializer(
            paginated_queryset, context={"request": request}, many=True)
        return self.get_paginated_response(serializer.data)


class TokenViewSet(viewsets.ModelViewSet):
    """ViewSet for getting and destroying users Token."""

    queryset = User.objects.all()
    serializer_class = TokenSerializer

    @action(
        detail=False,
        methods=("POST", ),
        permission_classes=(AllowAny,),
        url_path="token/login"
    )
    def login(self, request, *args, **kwargs):
        """Method for getting users token."""
        serializer = self.serializer_class(
            data=request.data,)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data.get("user")
        token, status = Token.objects.get_or_create(user=user)
        return Response(
            {
                "auth_token": token.key,
            },)

    @action(
        detail=False,
        methods=("POST", ),
        permission_classes=(IsAuthenticated,),
        url_path="token/logout")
    def logout(self, request, *args, **kwargs):
        """Method for destroying users token."""
        user = request.user
        token = Token.objects.get(user=user)
        token.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
