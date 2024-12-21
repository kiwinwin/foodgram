from django.contrib.auth import get_user_model
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from foodgram.models import Subscription

from .pagination import Pagination
from .users_serializers import FollowUserSerializer, TokenSerializer
from .variables import USERS_SERIALIZERS
from .views import RecipeViewSet

User = get_user_model()


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
