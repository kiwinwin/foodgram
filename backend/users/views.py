from api.views import RecipeViewSet
from django.contrib.auth import get_user_model
from foodgram.models import Subscription
from foodgram_project.pagination import Pagination
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.serializers import (CustomSetPasswordSerializer,
                               CustomUserCreateSerializer,
                               CustomUserSerializer, FollowCreateSerializer,
                               FollowUserSerializer, ManyFollowUserSerializer,
                               SetAvatarSerializer)


User = get_user_model()


class CustomUserViewSet(viewsets.ModelViewSet):

    queryset = User.objects.all()
    pagination_class = Pagination
    http_method_names = ["get", "post", "put", "delete"]
    lookup_field = "pk"
    model = User
    imported = RecipeViewSet

    def get_serializer_class(self):
        serializer = CustomUserCreateSerializer
        if self.action == "me" or self.request.method == "GET":
            serializer = CustomUserSerializer
        if self.action == "set_password":
            serializer = CustomSetPasswordSerializer
        if self.action == "avatar":
            serializer = SetAvatarSerializer
        if self.action == "subscribe":
            serializer = FollowCreateSerializer
        if self.action == "subscriptions":
            serializer = ManyFollowUserSerializer
        return serializer

    def subscribing(self, request, through_model,
                    result_serializer, *args, **kwargs):
        return self.imported.favorite_incart(
            self, request, through_model, result_serializer, *args, **kwargs)

    @action(
        detail=False,
        methods=("GET", ),
        permission_classes=(IsAuthenticated,),
    )
    def me(self, request):
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
        through_model = Subscription
        result_serializer = FollowUserSerializer
        result = self.subscribing(request, through_model,
                                  result_serializer, *args, **kwargs)
        return result

    @action(
        detail=False,
        methods=("GET",),
        permission_classes=(IsAuthenticated,),)
    def subscriptions(self, request, *args, **kwargs):
        user = request.user
        queryset = Subscription.objects.filter(user=user.id)
        paginated_queryset = self.paginate_queryset(queryset)
        serializer = self.get_serializer(
            paginated_queryset, context={"request": request}, many=True)
        return self.get_paginated_response(serializer.data)
