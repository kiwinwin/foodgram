import re
import base64
from django.core.files.base import ContentFile
from djoser.serializers import (UserSerializer,
                                UserCreateSerializer,
                                TokenCreateSerializer,
                                TokenSerializer,
                                SetPasswordSerializer,
                                PasswordSerializer,
                                CurrentPasswordSerializer
                                )
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import models
from rest_framework.authtoken.models import Token
from rest_framework.validators import UniqueValidator
from api.shortrecipeserializer import ShortRecipeSerializer
from foodgram.models import Subscription, Recipe

User = get_user_model()

class Base64AvatarField(serializers.ImageField):


    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='image.' + ext)

        return super().to_internal_value(data)

class CustomUserSerializer(UserSerializer):

    is_subscribed = serializers.SerializerMethodField()

    class Meta(UserCreateSerializer.Meta):
        fields = ('email', 'id', "username", 'first_name', 'last_name', 'avatar', 'is_subscribed')
        model = User
        read_only_fields = ('email', 'id', "username", 'first_name', 'last_name', 'avatar', 'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request', None)
        try:
            Subscription.objects.get(user=request.user.id, follows=obj.id)
            return True
        except Exception as error:
            return False


class CustomUserCreateSerializer(UserCreateSerializer):

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
        fields = ('id', 'email', "username", 'first_name', 'last_name', "password")
        model = User
        read_only_fields = ('id', 'avatar', )

    def validate_username(self, value):
        if not re.match(r'^[\w.@+-]+$', value):
            raise serializers.ValidationError()
        return value


class CustomSetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(style={"input_type": "password"})
    current_password = serializers.CharField(style={"input_type": "password"})


class SetAvatarSerializer(serializers.ModelSerializer):

    avatar = Base64AvatarField(required=True)

    class Meta:
        fields = ('avatar', )
        model = User

    # исправить - топорно
    def validate_avatar(self, value):
        if not value:
            raise serializers.ValidationError()
        return value

    def update(self, instance, validated_data):
        if len(validated_data) == 0:
            raise serializers.ValidationError()
        instance.avatar = validated_data.get('avatar', instance.avatar)
        instance.save()
        return instance

class FollowCreateSerializer(serializers.ModelSerializer):
    
    class Meta:
        fields = ('user', 'follows')
        model = Subscription

        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('user', 'follows'))]
    
    def validate(self, data):
        if data["user"] == data["follows"]:
            raise serializers.ValidationError()
        return data
    

class FollowUserSerializer(CustomUserSerializer):
      
    def to_representation(self, instance):
        request = self.context.get('request', None)
        query_dict = request.query_params.copy()
        representation = super().to_representation(instance)
        representation['recipes'] = []
        recipes_queryset = Recipe.objects.filter(author=instance.id)
        if 'recipes_limit' in query_dict:
            recipes_limit = query_dict.get('recipes_limit')
            recipes_queryset = recipes_queryset[:int(recipes_limit)]
        for db_recipe in recipes_queryset:
            recipe = ShortRecipeSerializer(db_recipe).data
            representation['recipes'].append(recipe)
        representation['recipes_count'] = len(representation['recipes'])
        return representation

class ManyFollowUserSerializer(FollowUserSerializer):

    def to_representation(self, instance):
        request = self.context.get('request', None)
        representation = super().to_representation(instance.follows)
        return representation

