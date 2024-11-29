import base64
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from rest_framework import serializers
from users.serializers import CustomUserSerializer
from foodgram.models import (Ingredients,
                             Tags,
                             IngredientsAmount,
                             RecipeIngredients,
                             Recipe,
                             RecipeTags,
                             FavoriteRecipe,
                             IncartRecipe)



User = get_user_model()

class Base64ImageField(serializers.ImageField):


    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='image.' + ext)

        return super().to_internal_value(data)


class TagsSerializer(serializers.ModelSerializer):

    
    class Meta:
        fields = ('id', 'name', 'slug',)
        model = Tags


class IngredientsSerializer(serializers.ModelSerializer):


    class Meta:
        fields = ('id', 'name', 'measurement_unit')
        model = Ingredients


class IngredientsAmountCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredients.objects.all(),
    )

    class Meta:
        fields = ('id', 'amount',)
        model = IngredientsAmount


class IngredientsAmountSerializer(serializers.ModelSerializer):
    
    ingredient = IngredientsSerializer()

    class Meta:
        fields = ('ingredient', 'amount')
        model = IngredientsAmount



class FavoriteRecipeSerializer(serializers.ModelSerializer):
    
    class Meta:
        fields = ('user', 'recipe')
        model = FavoriteRecipe

        validators = [
            serializers.UniqueTogetherValidator(
                queryset=FavoriteRecipe.objects.all(),
                fields=('user', 'recipe'))]


class IncartRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('user', 'recipe')
        model = IncartRecipe

        validators = [
            serializers.UniqueTogetherValidator(
                queryset=IncartRecipe.objects.all(),
                fields=('user', 'recipe'))]


class RecipeSerializer(serializers.ModelSerializer):
    
    tags = TagsSerializer(many=True)
    author = CustomUserSerializer()
    ingredients = IngredientsAmountSerializer(many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()


    class Meta:
        fields = (
            'id', 'tags', 'author'
            'ingredients', 'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time')
        model = Recipe
    
    def get_is_favorited(self, obj):
        request = self.context.get('request', None)
        return FavoriteRecipe.objects.filter(recipe=obj.id, user=request.user.id).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request', None)
        return IncartRecipe.objects.filter(recipe=obj.id, user=request.user.id).exists()


class RecipeIngredientsSerializer(serializers.ModelSerializer):

    ingredient = IngredientsAmountCreateSerializer()

    class Meta:
        fields = ('id', 'ingredient', 'recipe')
        model = RecipeIngredients
        read_only_fields = ('id', 'ingredient', 'recipe')


class RecipeCreateSerializer(serializers.ModelSerializer):

    ingredients = IngredientsAmountCreateSerializer(
        many=True,
        required=True
    )
    
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tags.objects.all(),
        required=True,
        many=True
    )
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    image = Base64ImageField(required=True)
    cooking_time = serializers.IntegerField(min_value=1, required=True)

    class Meta:
        fields = ('id', 'ingredients','tags', 'image', 'name', 'text', 'cooking_time', 'author')
        model = Recipe
        read_only_fields = ('id',)

    
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        for tag in tags:
            RecipeTags.objects.get_or_create(
                recipe=recipe, tag=tag)
        for current_ingredient in ingredients:
            ingredient = current_ingredient['ingredient']
            amount = current_ingredient["amount"]
            ingredient_amount, status = IngredientsAmount.objects.get_or_create(ingredient=ingredient, amount=amount)
            RecipeIngredients.objects.create(recipe=recipe, ingredient=ingredient_amount)
        return recipe
    
    # исправить валидацию отсутствующих полей, эксепшн без конкретики
    def update(self, instance, validated_data):
        try:
            ingredients = validated_data.pop('ingredients')
            tags = validated_data.pop('tags')
        except Exception:
            raise serializers.ValidationError()
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get('cooking_time', instance.cooking_time)
        instance.save()
        for tag in tags:
            RecipeTags.objects.get_or_create(
                recipe=instance, tag=tag)
        for current_ingredient in ingredients:
            ingredient = current_ingredient['ingredient']
            amount = current_ingredient["amount"]
            ingredient_amount, status = IngredientsAmount.objects.get_or_create(ingredient=ingredient, amount=amount)
            RecipeIngredients.objects.update_or_create(recipe=instance, ingredient=ingredient_amount)
        return instance


    def to_representation(self, instance):
        request = self.context.get('request', None)
        representation = super().to_representation(instance)
        representation['author'] = CustomUserSerializer(instance.author).data
        representation['is_favorited'] = FavoriteRecipe.objects.filter(recipe=instance.id, user=request.user.id).exists()
        representation['is_in_shopping_cart'] = IncartRecipe.objects.filter(recipe=instance.id, user=request.user.id).exists()
        representation['ingredients'] = []
        representation['tags'] = []
        for db_ingredient in instance.ingredients.all():
            ingredient = IngredientsAmountCreateSerializer(db_ingredient).data
            ingredient['name'] = Ingredients.objects.get(id=ingredient['id']).name
            ingredient['measurement_unit'] = Ingredients.objects.get(id=ingredient['id']).measurement_unit
            representation['ingredients'].append(ingredient)
        for db_tag in instance.tags.all():
            tag = TagsSerializer(db_tag).data
            representation['tags'].append(tag)
        return representation

    def validate_ingredients(self, value):
        ingredient_ids = []
        for ingredient_amount in value:
            ingredient_ids.append(ingredient_amount['ingredient'].id)
        if len(value) == 0 or len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError()
        return value

    def validate_tags(self, value):
        if len(value) == 0 or len(value) != len(set(value)):
            raise serializers.ValidationError()
        return value


class ShortRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('id', 'name', 'image', 'cooking_time')
        model = Recipe
        read_only_fields = ('id', 'name', 'image', 'cooking_time')