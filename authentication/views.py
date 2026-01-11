import json
import logging
import random
from http import HTTPStatus

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.filters import SearchFilter
from rest_framework.generics import GenericAPIView, UpdateAPIView, RetrieveAPIView, DestroyAPIView, ListAPIView, \
    get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from app.models import Post
from app.serializers import PostModelSerializer
from authentication.error_codes import ErrorCode
from authentication.models import Follow
from authentication.models import User
from authentication.permissions import IsActiveUser
from authentication.serializers import UserModelSerializer, VerifyCodeSerializer, UserUpdateModelSerializer, \
    UserProfileSerializer, FollowModelSerializer, PublicUserSerializer, UserProfileSecondSerializer, \
    UserLanguageSerializer
from authentication.tasks import send_code_email
from core.functions import api_response
from core.utils import RequestLoggingMiddleware
from root.settings import redis

logger = logging.getLogger(__name__)


####################################### AUTH ########################################
@extend_schema(tags=['auth'])
class UserGenericAPIView(GenericAPIView):
    serializer_class = UserModelSerializer
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        ip = RequestLoggingMiddleware.get_client_ip(request)

        logger.info(
            "Registration attempt | ip=%s | email=%s",
            ip,
            request.data.get("email")
        )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_data = serializer.validated_data
        code = str(random.randrange(10 ** 5, 10 ** 6))
        redis_key = f"verify:{code}"
        send_code_email.delay(user_data, code)
        redis.setex(redis_key, 300, json.dumps(user_data))
        return api_response(
            success=True,
            message=_("Verification code sent successfully"),
            data=None,
            status=HTTPStatus.OK
        )


@extend_schema(tags=['auth'])
class VerifyEmailGenericAPIView(GenericAPIView):
    serializer_class = VerifyCodeSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        ip = RequestLoggingMiddleware.get_client_ip(request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data.get("code")
        redis_key = f"verify:{code}"
        raw_data = redis.get(redis_key)

        if not raw_data:
            logger.warning(
                "Email verification failed | ip=%s | code=%s",
                ip,
                code
            )
            return api_response(
                success=False,
                error_code=ErrorCode.VERIFICATION_CODE_EXPIRED,
                message=_("Verification code is invalid or expired."),
                status=status.HTTP_400_BAD_REQUEST
            )

        user_data = json.loads(raw_data)

        with transaction.atomic():
            user = User.objects.create(**user_data)
            redis.delete(redis_key)

        logger.info(
            "Email verified successfully | user_id=%s | ip=%s",
            user.id,
            ip
        )

        return api_response(
            success=True,
            message=_("Email verified successfully"),
            data=UserModelSerializer(user).data,
            status=HTTPStatus.CREATED
        )


@extend_schema(tags=['auth'])
class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        ip = RequestLoggingMiddleware.get_client_ip(request)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.user

        if user.is_deleted:
            user.is_deleted = False
            user.deleted_at = None

        user.last_login = timezone.now()
        user.save(update_fields=['is_deleted', 'deleted_at', 'last_login'])

        logger.info(
            "Login successful | user_id=%s | ip=%s",
            user.id,
            ip
        )

        response_data = {
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
            },
            'tokens': serializer.validated_data,
        }

        return api_response(
            success=True,
            message=_("Login successful"),
            data=response_data
        )


@extend_schema(tags=['auth'])
class CustomTokenRefreshView(TokenRefreshView):
    pass


#################################### USER ###################################
@extend_schema(tags=['user'])
class UserUpdateAPIView(UpdateAPIView):
    serializer_class = UserUpdateModelSerializer
    queryset = User.objects.all()
    permission_classes = [IsActiveUser]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        ip = RequestLoggingMiddleware.get_client_ip(request)

        serializer = self.get_serializer(
            self.get_object(),
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        logger.info(
            "User profile updated | user_id=%s | ip=%s",
            request.user.id,
            ip
        )

        return api_response(
            success=True,
            message=_("User updated successfully"),
            data=serializer.data
        )


@extend_schema(tags=['user'])
class UserDeleteAPIView(DestroyAPIView):
    permission_classes = [IsActiveUser]

    def destroy(self, request, *args, **kwargs):
        ip = RequestLoggingMiddleware.get_client_ip(request)

        user = request.user
        user.is_deleted = True
        user.deleted_at = timezone.now()
        user.save(update_fields=['is_deleted', 'deleted_at'])

        logger.warning(
            "User account deleted | user_id=%s | ip=%s",
            user.id,
            ip
        )

        return api_response(
            success=True,
            message=_("User deleted successfully"),
        )


@extend_schema(tags=['profile'])
class UserDetailAPIView(RetrieveAPIView):
    queryset = User.objects.all()
    lookup_field = 'pk'
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated, IsActiveUser]

    def get_object(self):
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        logger.debug(
            "User profile viewed | user_id=%s",
            request.user.id
        )

        serializer = self.get_serializer(self.get_object())
        return api_response(
            success=True,
            message=_("User profile retrieved successfully"),
            data=serializer.data
        )


@extend_schema(tags=['user'])
class UserListAPIView(ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileSecondSerializer
    filter_backends = [SearchFilter]
    search_fields = ['username', 'first_name', 'last_name']
    permission_classes = [IsAuthenticated, IsActiveUser]

    def list(self, request, *args, **kwargs):
        logger.debug(
            "User list accessed | user_id=%s | query=%s",
            request.user.id,
            request.query_params.dict()
        )

        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return api_response(
            success=True,
            message=_("Users retrieved successfully"),
            data=serializer.data
        )


@extend_schema(tags=['user'])
class UserProfileByUsernameAPIView(RetrieveAPIView):
    queryset = User.objects.all()
    lookup_field = 'username'
    serializer_class = PublicUserSerializer
    permission_classes = [IsAuthenticated, IsActiveUser]

    def get_object(self):
        return get_object_or_404(User, username=self.kwargs['username'])

    def retrieve(self, request, *args, **kwargs):
        logger.debug(
            "Public profile viewed | viewer=%s | target=%s",
            request.user.id,
            self.kwargs['username']
        )

        serializer = self.get_serializer(self.get_object())
        return api_response(
            success=True,
            message=_("User profile retrieved successfully"),
            data=serializer.data
        )


@extend_schema(tags=['user'])
class SuggestedUsersAPIView(ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileSecondSerializer
    permission_classes = [IsAuthenticated, IsActiveUser]

    def get_queryset(self):
        user = self.request.user
        following_ids = Follow.objects.filter(follower=user).values_list('following_id', flat=True)
        return User.objects.exclude(
            Q(id=user.id) | Q(id__in=following_ids)
        ).order_by('-date_joined')[:10]

    def list(self, request, *args, **kwargs):
        logger.debug(
            "Suggested users requested | user_id=%s",
            request.user.id
        )

        serializer = self.get_serializer(self.get_queryset(), many=True)
        return api_response(
            success=True,
            message=_("Suggested users retrieved successfully"),
            data=serializer.data
        )


@extend_schema(tags=['user'])
class UserPostsAPIView(ListAPIView):
    serializer_class = PostModelSerializer
    permission_classes = [IsAuthenticated, IsActiveUser]

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs["username"])
        return Post.objects.filter(user=user).order_by("-created_at")

    def list(self, request, *args, **kwargs):
        logger.debug(
            "User posts viewed | viewer=%s | target=%s",
            request.user.id,
            self.kwargs["username"]
        )

        serializer = self.get_serializer(self.get_queryset(), many=True)
        return api_response(
            success=True,
            message=_("User posts retrieved successfully"),
            data=serializer.data
        )


##################################### FOLLOW ########################################
@extend_schema(tags=['follow/unfollow'])
class FollowUserAPIView(APIView):
    permission_classes = [IsActiveUser]

    def post(self, request, username):
        ip = RequestLoggingMiddleware.get_client_ip(request)

        try:
            user_to_follow = User.objects.get(username=username)
        except User.DoesNotExist:
            logger.warning(
                "Follow failed: user not found | follower=%s | target=%s | ip=%s",
                request.user.id,
                username,
                ip
            )
            return api_response(
                success=False,
                error_code=ErrorCode.USER_NOT_FOUND,
                message=_("User not found"),
                status=status.HTTP_404_NOT_FOUND
            )

        if user_to_follow == request.user:
            logger.warning(
                "Follow failed: self-follow attempt | user_id=%s | ip=%s",
                request.user.id,
                ip
            )
            return api_response(
                success=False,
                error_code=ErrorCode.SELF_FOLLOW,
                message=_('You can not follow yourself'),
                status=status.HTTP_400_BAD_REQUEST
            )

        follow, created = Follow.objects.get_or_create(
            follower=request.user,
            following=user_to_follow
        )

        if not created:
            logger.warning(
                "Follow already exists | follower=%s | following=%s | ip=%s",
                request.user.id,
                user_to_follow.id,
                ip
            )
            return api_response(
                success=False,
                error_code=ErrorCode.ALREADY_FOLLOWED,
                message=_('Follow already created'),
                status=status.HTTP_400_BAD_REQUEST
            )
        logger.info(
            "User followed | follower=%s | following=%s | ip=%s",
            request.user.id,
            user_to_follow.id,
            ip
        )
        return api_response(
            success=True,
            message=_("You are now following %(username)s") % {
                "username": user_to_follow.username
            },
            status=status.HTTP_201_CREATED
        )


@extend_schema(tags=['follow/unfollow'])
class UnfollowUserAPIView(APIView):
    permission_classes = [IsActiveUser]

    def post(self, request, username):
        ip = RequestLoggingMiddleware.get_client_ip(request)

        try:
            user_to_unfollow = User.objects.get(username=username)
        except User.DoesNotExist:
            logger.warning(
                "Unfollow failed: user not found | follower=%s | target=%s | ip=%s",
                request.user.id,
                username,
                ip
            )
            return api_response(
                success=False,
                error_code=ErrorCode.USER_NOT_FOUND,
                message=_("User not found"),
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            follow = Follow.objects.get(follower=request.user, following=user_to_unfollow)
            follow.delete()
            logger.info(
                "User unfollowed | follower=%s | following=%s | ip=%s",
                request.user.id,
                user_to_unfollow.id,
                ip
            )
            return api_response(
                success=True,
                message=_("You have unfollowed %(username)s") % {
                    "username": user_to_unfollow.username
                },
                data=None
            )
        except Follow.DoesNotExist:
            logger.warning(
                "Unfollow failed: relationship not found | follower=%s | target=%s | ip=%s",
                request.user.id,
                username,
                ip
            )
            return api_response(
                success=False,
                error_code=ErrorCode.NOT_FOLLOWING,
                message=_("You are not following this user"),
                status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema(tags=['profile'])
class UserFollowersAPIView(APIView):
    permission_classes = [IsAuthenticated, IsActiveUser]

    def get(self, request, username):
        user = get_object_or_404(User, username=username)
        followers = Follow.objects.filter(following=user)
        serializer = FollowModelSerializer(followers, many=True)

        return api_response(
            success=True,
            message=_("Followers retrieved successfully"),
            data=serializer.data
        )


@extend_schema(tags=['profile'])
class UserFollowingAPIView(APIView):
    permission_classes = [IsAuthenticated, IsActiveUser]

    def get(self, request, username):
        user = get_object_or_404(User, username=username)
        following = Follow.objects.filter(follower=user)
        serializer = FollowModelSerializer(following, many=True)

        return api_response(
            success=True,
            message=_("Following list retrieved successfully"),
            data=serializer.data
        )


##################################### SETTINGS ########################################
@extend_schema(tags=['settings, language'])
class UpdateLanguageAPIView(UpdateAPIView):
    serializer_class = UserLanguageSerializer
    permission_classes = [IsActiveUser]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        ip = RequestLoggingMiddleware.get_client_ip(request)

        serializer = self.get_serializer(
            self.get_object(),
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        logger.info(
            "Language updated | user_id=%s | language=%s | ip=%s",
            request.user.id,
            request.data.get("language"),
            ip
        )

        return api_response(
            success=True,
            message=_("Language updated successfully"),
            data=serializer.data
        )
