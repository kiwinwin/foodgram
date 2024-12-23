import base64
import re

from django.contrib.auth import get_user_model, models
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

# линтер ругается на отсутствие строки
from foodgram.models import (FavoriteRecipe, IncartRecipe, Ingredient,
                             IngredientAmount, Recipe, RecipeIngredient,
                             RecipeTag, Subscription, Tag)

from .variables import (MAX_AMOUNT_VALUE, MAX_COOKING_TIME_VALUE,
                        MIN_AMOUNT_VALUE, MIN_COOKING_TIME_VALUE)

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """
    Сlass for users avatar
    and recipe image fields.
    """

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith("data:image"):
            format, imgstr = data.split(";base64,")
            ext = format.split("/")[-1]

            data = ContentFile(base64.b64decode(imgstr), name="image." + ext)

        return super().to_internal_value(data)


class CustomUserSerializer(UserSerializer):
    """Class for users profiles."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):

        fields = ("email", "id", "username", "first_name",
                  "last_name", "avatar", "is_subscribed")
        model = User
        read_only_fields = (
            "email", "id", "username", "first_name",
            "last_name", "avatar", "is_subscribed")

    def get_user(self):
        """Part of getting is_subscribed field."""
        request = self.context.get('request', None)
        user = request.user
        if request is not None and user.__class__ is not models.AnonymousUser:
            return user
        return None

    def get_is_subscribed(self, obj):
        """Getting is_subscribed field."""
        user = self.get_user()
        if user is not None:
            return obj.first_name in user.follows.all().values_list(
                'item__first_name', flat=True)
        return False


class CustomUserCreateSerializer(UserCreateSerializer):
    """Class for creating users."""

    email = serializers.EmailField(
        max_length=254,
        validators=[UniqueValidator(queryset=User.objects.all())],
        required=True,
    )
    username = serializers.CharField(
        max_length=150,
        validators=[UniqueValidator(queryset=User.objects.all())],
        required=True,
    )
    first_name = serializers.CharField(max_length=150, required=True)
    last_name = serializers.CharField(max_length=150, required=True)

    class Meta(UserCreateSerializer.Meta):
        fields = ("id", "email", "username",
                  "first_name", "last_name", "password")
        model = User
        read_only_fields = ("id", "avatar", )

    def validate_username(self, value):
        if not re.match(r"^[\w.@+-]+$", value):
            raise serializers.ValidationError()
        return value


class CustomSetPasswordSerializer(serializers.Serializer):
    """Class for setting/updating users password."""

    new_password = serializers.CharField(style={"input_type": "password"})
    current_password = serializers.CharField(style={"input_type": "password"})


class SetAvatarSerializer(serializers.ModelSerializer):
    """Class for setting/updating users avatar."""

    avatar = Base64ImageField(required=True)

    class Meta:
        fields = ("avatar", )
        model = User

    def validate(self, data):
        if "avatar" not in data:
            raise serializers.ValidationError()
        return data

    def update(self, instance, validated_data):
        instance.avatar = validated_data.get("avatar", instance.avatar)
        instance.save()
        return instance


class FollowCreateSerializer(serializers.ModelSerializer):
    """Class for creating users subscriptions."""

    class Meta:
        fields = ("user", "item")
        model = Subscription

        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=("user", "item"))]

    def validate(self, data):
        if data["user"] == data["item"]:
            raise serializers.ValidationError()
        return data


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Serializer for users/subscriptions short recipe."""

    class Meta:
        fields = ("id", "name", "image", "cooking_time")
        model = Recipe
        read_only_fields = ("id", "name", "image", "cooking_time")


class FollowUserSerializer(CustomUserSerializer):
    """Class for getting users subscriptions."""

    def to_representation(self, instance):
        request = self.context.get("request", None)
        query_dict = request.query_params.copy()
        recipes_limit = query_dict.get("recipes_limit")
        representation = super().to_representation(instance)
        recipes_queryset = Recipe.objects.filter(author=instance.id)
        if recipes_limit is not None:
            recipes_queryset = recipes_queryset[:int(recipes_limit)]
        serializer = ShortRecipeSerializer(recipes_queryset, many=True)
        representation["recipes"] = serializer.data
        representation["recipes_count"] = recipes_queryset.count()
        return representation


class ManyFollowUserSerializer(FollowUserSerializer):
    """Class for getting users subscriptions."""

    def to_representation(self, instance):
        representation = super().to_representation(instance.item)
        return representation


class TokenSerializer(serializers.ModelSerializer):
    """Class for getting users token."""

    password = serializers.CharField(
        required=True,
        style={"input_type": "password"})
    email = serializers.EmailField(
        max_length=254,
        required=True)

    class Meta:
        fields = ("email", "password")
        model = User

    def validate(self, data):
        password = data.get("password")
        email = data.get("email").lower()
        user = get_object_or_404(User, email=email)
        data["user"] = user
        if user.check_password(password):
            return data
        raise serializers.ValidationError()


class TagsSerializer(serializers.ModelSerializer):
    """Serializer for recipes tag."""

    class Meta:
        fields = ("id", "name", "slug",)
        model = Tag


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for ingredient."""

    class Meta:
        fields = ("id", "name", "measurement_unit")
        model = Ingredient


class IngredientAmountCreateSerializer(serializers.ModelSerializer):
    """Serializer for ingredient and its amount."""

    id = serializers.PrimaryKeyRelatedField(
        source="ingredient",
        queryset=Ingredient.objects.all(),
    )
    amount = serializers.IntegerField(
        min_value=MIN_AMOUNT_VALUE,
        max_value=MAX_AMOUNT_VALUE,
        required=True)

    class Meta:
        fields = ("id", "amount",)
        model = IngredientAmount


class IngredientAmountSerializer(serializers.ModelSerializer):

    ingredient = IngredientSerializer()

    class Meta:
        fields = ("ingredient", "amount")
        model = IngredientAmount

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        ingredient = representation.pop("ingredient")
        representation.update(ingredient)
        return representation


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Serializer for downloading incart recipes."""

    ingredient = IngredientSerializer()

    class Meta:
        fields = ("id", "ingredient", "amount")
        model = IngredientAmount


class FavoriteRecipeSerializer(serializers.ModelSerializer):
    """Serializer for users favorite recipes."""

    class Meta:
        fields = ("user", "item")
        model = FavoriteRecipe

        validators = [
            serializers.UniqueTogetherValidator(
                queryset=FavoriteRecipe.objects.all(),
                fields=("user", "item"))]


class IncartRecipeSerializer(serializers.ModelSerializer):
    """Serializer for users recipes in his cart."""

    class Meta:
        fields = ("user", "item")
        model = IncartRecipe

        validators = [
            serializers.UniqueTogetherValidator(
                queryset=IncartRecipe.objects.all(),
                fields=("user", "item"))]


class RecipeReperesentationSerializer(serializers.ModelSerializer):
    """For getting recipes data."""

    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    ingredients = IngredientAmountSerializer(many=True)
    tags = TagsSerializer(many=True)
    author = CustomUserSerializer()

    class Meta:
        fields = ("id", "ingredients", "tags", "image",
                  "name", "text", "cooking_time", "author",
                  "is_favorited", "is_in_shopping_cart")
        model = Recipe
        read_only_fields = ("id", "ingredients", "tags",
                            "image", "name", "text",
                            "cooking_time", "author",
                            "is_favorited", "is_in_shopping_cart")

    def get_user(self):
        request = self.context.get("request", None)
        user = request.user
        if request is not None and user.__class__ is not models.AnonymousUser:
            return user
        return None

    def get_is_favorited(self, obj):
        """Getting is_favorited field."""
        user = self.get_user()
        if user is not None:
            return obj.name in user.favoriterecipes.all().values_list(
                "item__name", flat=True)
        return False

    def get_is_in_shopping_cart(self, obj):
        """Getting is_in_shopping_cart field."""
        user = self.get_user()
        if user is not None:
            return obj.name in user.incartrecipes.all().values_list(
                "item__name", flat=True)
        return False


class RecipeSerializer(serializers.ModelSerializer):
    """
    Serializer for creating,
    updating Recipe object and its data.
    """

    ingredients = IngredientAmountCreateSerializer(
        many=True,
        required=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        required=True,
        many=True)
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    image = Base64ImageField(required=True)
    cooking_time = serializers.IntegerField(
        min_value=MIN_COOKING_TIME_VALUE,
        max_value=MAX_COOKING_TIME_VALUE,
        required=True)

    class Meta:
        fields = ("id", "ingredients", "tags", "image",
                  "name", "text", "cooking_time", "author")
        model = Recipe
        read_only_fields = ("id",)

    def get_ingredient_amount_list(self, ingredients):
        """
        Getting ingredient and amount list
        for making relations in RecipeIngredient table.
        """

        ingredient_amount_list = []
        for current_ingredient in ingredients:
            ingredient = current_ingredient["ingredient"]
            amount = current_ingredient["amount"]
            ingredient_amount, status = IngredientAmount.objects.get_or_create(
                ingredient=ingredient, amount=amount)
            ingredient_amount_list.append(ingredient_amount)
        return ingredient_amount_list

    def create(self, validated_data):
        """Method creating Recipes object."""
        ingredients = validated_data.pop("ingredients")
        tags = validated_data.pop("tags")
        recipe = Recipe.objects.create(**validated_data)
        RecipeTag.objects.bulk_create(
            RecipeTag(tag=tag, recipe=recipe)
            for tag in tags)
        ingredient_amount_list = self.get_ingredient_amount_list(ingredients)
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(recipe=recipe, ingredient=ingredient_amount)
            for ingredient_amount in ingredient_amount_list)
        return recipe

    def update(self, instance, validated_data):
        """Method updateting Recipes object data."""
        ingredients = validated_data.get("ingredients", [])
        tags = validated_data.get("tags", [])
        instance.name = validated_data.get("name", instance.name)
        instance.text = validated_data.get("text", instance.text)
        instance.image = validated_data.get("image", instance.image)
        instance.cooking_time = validated_data.get("cooking_time",
                                                   instance.cooking_time)
        instance.save()
        if tags:
            instance.tags.clear()
            RecipeTag.objects.bulk_create(
                RecipeTag(tag=tag, recipe=instance)
                for tag in tags)
        else:
            self.validate_tags(tags)
        if ingredients:
            instance.ingredients.clear()
            ingredient_amount_list = self.get_ingredient_amount_list(
                ingredients)
            RecipeIngredient.objects.bulk_create(
                RecipeIngredient(recipe=instance, ingredient=ingredient_amount)
                for ingredient_amount in ingredient_amount_list)
        else:
            self.validate_ingredients(ingredients)
        return instance

    def to_representation(self, instance):
        """Method representing Recipes object data."""
        request = self.context.get("request", None)
        representation = RecipeReperesentationSerializer(
            instance, context={"request": request})
        return representation.data

    def validate_ingredients(self, value):
        """Method validating ingredients field."""
        if len(value) == 0:
            raise serializers.ValidationError()
        ids_stack = set()
        for item in value:
            if item["ingredient"].id in ids_stack:
                raise serializers.ValidationError()
            ids_stack.add(item["ingredient"].id)
        return value

    def validate_tags(self, value):
        """Method validating tags field."""
        if len(value) == 0 or len(value) != len(set(value)):
            raise serializers.ValidationError()
        return value
