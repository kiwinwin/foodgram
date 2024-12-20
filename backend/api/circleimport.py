import base64

from django.core.files.base import ContentFile
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
