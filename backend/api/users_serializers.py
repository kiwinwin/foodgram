import re

from django.contrib.auth import get_user_model, models
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from foodgram.models import Recipe, Subscription

from .circleimport import Base64ImageField, ShortRecipeSerializer

User = get_user_model()


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
