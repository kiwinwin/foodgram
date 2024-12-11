from django.contrib.auth import get_user_model
from rest_framework import serializers
from users.serializers import CustomUserSerializer
from foodgram_project.circleimport import Base64ImageField
from foodgram.models import (Ingredient,
                             Tag,
                             IngredientAmount,
                             RecipeIngredient,
                             Recipe,
                             RecipeTag,
                             FavoriteRecipe,
                             IncartRecipe)


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

    class Meta:
        fields = ("id", "amount",)
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


class RecipeSerializer(serializers.ModelSerializer):
    """
    Serializer for creating, updating and representing
    Recipe object and its data.
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
    cooking_time = serializers.IntegerField(min_value=1, required=True)

    class Meta:
        fields = ("id", "ingredients", "tags", "image",
                  "name", "text", "cooking_time", "author")
        model = Recipe
        read_only_fields = ("id",)

    def create(self, validated_data):
        """Method creating Recipes object."""
        ingredients = validated_data.pop("ingredients")
        tags = validated_data.pop("tags")
        recipe = Recipe.objects.create(**validated_data)
        for tag in tags:
            RecipeTag.objects.get_or_create(
                recipe=recipe, tag=tag)
        for current_ingredient in ingredients:
            ingredient = current_ingredient["ingredient"]
            amount = current_ingredient["amount"]
            ingredient_amount, status = IngredientAmount.objects.get_or_create(
                ingredient=ingredient, amount=amount)
            RecipeIngredient.objects.create(
                recipe=recipe, ingredient=ingredient_amount)
        return recipe

    def update(self, instance, validated_data):
        """Method updateting Recipes object data."""
        ingredients = validated_data.get("ingredients", [])
        tags = validated_data.get("tags", [])
        instance.name = validated_data.get("name", instance.name)
        instance.text = validated_data.get("text", instance.text)
        instance.image = validated_data.get("image", instance.image)
        instance.cooking_time = validated_data.get(
            "cooking_time", instance.cooking_time)
        instance.save()
        if tags:
            instance.tags.clear()
            for tag in tags:
                RecipeTag.objects.create(recipe=instance, tag=tag)
        else:
            self.validate_tags(tags)
        if ingredients:
            instance.ingredients.clear()
            for current_ingredient in ingredients:
                ingredient = current_ingredient["ingredient"]
                amount = current_ingredient["amount"]
                ingredient_amount, status = \
                    IngredientAmount.objects.get_or_create(
                        ingredient=ingredient, amount=amount)
                RecipeIngredient.objects.create(
                    recipe=instance, ingredient=ingredient_amount)
        else:
            self.validate_tags(ingredients)
        return instance

    def to_representation(self, instance):
        """Method representing Recipes object data."""
        request = self.context.get("request", None)
        representation = super().to_representation(instance)
        representation["author"] = CustomUserSerializer(
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
            representation["tags"].append(tag)
        return representation

    def validate_ingredients(self, value):
        """Method validating ingredients field."""
        ingredient_ids = []
        for ingredient_amount in value:
            ingredient_ids.append(ingredient_amount["ingredient"].id)
        if len(value) == 0 or len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError()
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
