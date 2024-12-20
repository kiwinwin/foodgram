from django.contrib.auth import get_user_model
from rest_framework import serializers

from foodgram.models import (FavoriteRecipe, IncartRecipe, Ingredient,
                             IngredientAmount, Recipe, RecipeIngredient,
                             RecipeTag, Tag)

from .circleimport import Base64ImageField
from .users_serializers import CustomUserSerializer
from .variables import (MAX_AMOUNT_VALUE, MAX_COOKING_TIME_VALUE,
                        MIN_AMOUNT_VALUE, MIN_COOKING_TIME_VALUE)

User = get_user_model()


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
        fields = ('ingredient', 'amount')
        model = IngredientAmount

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        ingredient = representation.pop('ingredient')
        representation.update(ingredient)
        return representation


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Serializer for downloading incart recipes."""

    ingredient = IngredientSerializer()

    class Meta:
        fields = ('id', 'ingredient', 'amount')
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
                  'is_favorited', 'is_in_shopping_cart')
        model = Recipe
        read_only_fields = ("id", "ingredients", "tags",
                            "image", "name", "text",
                            "cooking_time", "author",
                            'is_favorited', 'is_in_shopping_cart')

    def get_user(self):
        return CustomUserSerializer.get_user(self)

    def get_is_favorited(self, obj):
        """Getting is_favorited field."""
        user = self.get_user()
        if user is not None:
            user.favoriterecipes.filter(item=obj.id).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        """Getting is_in_shopping_cart field."""
        user = self.get_user()
        if user is not None:
            user.incartrecipes.filter(item=obj.id).exists()
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
            ingredient = current_ingredient['ingredient']
            amount = current_ingredient["amount"]
            ingredient_amount, status = \
                IngredientAmount.objects.get_or_create(
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
            instance, context={'request': request}).data
        return representation

        '''representation["author"] = CustomUserSerializer(
            instance.author, context={"request": request}).data
        representation["is_favorited"] = FavoriteRecipe.objects.filter(
            item=instance.id, user=request.user.id).exists()
        representation["is_in_shopping_cart"] = IncartRecipe.objects.filter(
            item=instance.id, user=request.user.id).exists()
        representation["ingredients"] = []
        representation["tags"] = []
        for db_ingredient in instance.ingredients.all():
            ingredient = IngredientAmountCreateSerializer(db_ingredient).data
            ingredient["name"] = Ingredient.objects.get(
                id=ingredient["id"]).name
            ingredient["measurement_unit"] = Ingredient.objects.get(
                id=ingredient["id"]).measurement_unit
            representation["ingredients"].append(ingredient)
        for db_tag in instance.tags.all():
            tag = TagsSerializer(db_tag).data
            representation["tags"].append(tag)'''

    def validate_ingredients(self, value):
        """Method validating ingredients field."""
        if len(value) == 0:
            raise serializers.ValidationError()
        ids_stack = set()
        for item in value:
            if item['ingredient'].id in ids_stack:
                raise serializers.ValidationError()
            ids_stack.add(item['ingredient'].id)
        return value

    def validate_tags(self, value):
        """Method validating tags field."""
        if len(value) == 0 or len(value) != len(set(value)):
            raise serializers.ValidationError()
        return value


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Serializer for users/subscriptions short recipe."""

    class Meta:
        fields = ("id", "name", "image", "cooking_time")
        model = Recipe
        read_only_fields = ("id", "name", "image", "cooking_time")
