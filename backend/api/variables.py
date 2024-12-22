from .serializers import (CustomSetPasswordSerializer,
                          CustomUserCreateSerializer, CustomUserSerializer,
                          FollowCreateSerializer, ManyFollowUserSerializer,
                          SetAvatarSerializer)

MIN_AMOUNT_VALUE = 1
MAX_AMOUNT_VALUE = 32000
MIN_COOKING_TIME_VALUE = 1
MAX_COOKING_TIME_VALUE = 32000

USERS_SERIALIZERS = {
    'create': CustomUserCreateSerializer,
    'get': CustomUserSerializer,
    'retrieve': CustomUserSerializer,
    'list': CustomUserSerializer,
    'me': CustomUserSerializer,
    'set_password': CustomSetPasswordSerializer,
    'avatar': SetAvatarSerializer,
    'subscribe': FollowCreateSerializer,
    'subscriptions': ManyFollowUserSerializer,
}
