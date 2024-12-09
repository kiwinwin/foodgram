from rest_framework import serializers
from foodgram.models import Recipe


class ShortRecipeSerializer(serializers.ModelSerializer):
    """
    Serializer for taking short recipe data.
    Circle import.
    """

    class Meta:
        fields = ("id", "name", "image", "cooking_time")
        model = Recipe
        read_only_fields = ("id", "name", "image", "cooking_time")