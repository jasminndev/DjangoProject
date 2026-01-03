import random
from http import HTTPStatus

from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from kombu.utils import json
from rest_framework import status
from rest_framework.filters import SearchFilter
from rest_framework.generics import GenericAPIView, UpdateAPIView, RetrieveAPIView, DestroyAPIView, ListAPIView, \
    get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from app.models import Post
from app.serializers import PostModelSerializer
from authentication.models import Follow
from authentication.models import User
from authentication.serializers import UserModelSerializer, VerifyCodeSerializer, UserUpdateModelSerializer, \
    UserProfileSerializer, FollowModelSerializer, PublicUserSerializer, UserProfileSecondSerializer
from authentication.tasks import send_code_email
from core.functions import api_response
from root.settings import redis


####################################### AUTH ########################################
@extend_schema(tags=['auth'])
class UserGenericAPIView(GenericAPIView):
    serializer_class = UserModelSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        code = str(random.randrange(10 ** 5, 10 ** 6))
        send_code_email.delay(user, code)
        redis.set(code, json.dumps(user))
        return api_response(
            success=True,
            message="Verification code sent successfully",
            data=None,
            status=HTTPStatus.OK
        )


@extend_schema(tags=['auth'])
class VerifyEmailGenericAPIView(GenericAPIView):
    serializer_class = VerifyCodeSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_data = serializer.context.get('user_data')
        user = User.objects.create(**user_data)
        return api_response(
            success=True,
            message="Email verified successfully",
            data=UserModelSerializer(user).data,
            status=HTTPStatus.CREATED
        )


@extend_schema(tags=['auth'])
class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == HTTPStatus.OK:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.user
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
        return response


@extend_schema(tags=['auth'])
class CustomTokenRefreshView(TokenRefreshView):
    pass


#################################### USER ###################################
@extend_schema(tags=['user'])
class UserUpdateAPIView(UpdateAPIView):
    serializer_class = UserUpdateModelSerializer
    queryset = User.objects.all()

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            self.get_object(),
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return api_response(
            success=True,
            message="User updated successfully",
            data=serializer.data
        )


@extend_schema(tags=['user'])
class UserDeleteAPIView(DestroyAPIView):
    serializer_class = UserModelSerializer
    lookup_field = 'pk'
    queryset = User.objects.all()

    def get_object(self):
        return self.request.user

    def destroy(self, request, *args, **kwargs):
        self.get_object().delete()
        return api_response(
            success=True,
            message="User deleted successfully",
            data=None
        )


@extend_schema(tags=['user'])
class UserDetailAPIView(RetrieveAPIView):
    queryset = User.objects.all()
    lookup_field = 'pk'
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return api_response(
            success=True,
            message="User profile retrieved successfully",
            data=serializer.data
        )


@extend_schema(tags=['user'])
class UserListAPIView(ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileSecondSerializer
    filter_backends = [SearchFilter]
    search_fields = ['username', 'first_name', 'last_name']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return api_response(
            success=True,
            message="Users retrieved successfully",
            data=serializer.data
        )


@extend_schema(tags=['user'])
class UserProfileByUsernameAPIView(RetrieveAPIView):
    queryset = User.objects.all()
    lookup_field = 'username'
    serializer_class = PublicUserSerializer

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return api_response(
            success=True,
            message="User profile retrieved successfully",
            data=serializer.data
        )


@extend_schema(tags=['user'])
class SuggestedUsersAPIView(ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileSecondSerializer

    def get_queryset(self):
        user = self.request.user
        following_ids = Follow.objects.filter(follower=user).values_list('following_id', flat=True)
        return User.objects.exclude(
            Q(id=user.id) | Q(id__in=following_ids)
        ).order_by('-date_joined')[:10]

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return api_response(
            success=True,
            message="Suggested users retrieved successfully",
            data=serializer.data
        )


@extend_schema(tags=['user'])
class UserPostsAPIView(ListAPIView):
    serializer_class = PostModelSerializer

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs["username"])
        return Post.objects.filter(user=user).order_by("-created_at")

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return api_response(
            success=True,
            message="User posts retrieved successfully",
            data=serializer.data
        )


##################################### FOLLOW ########################################

@extend_schema(tags=['follow'])
class FollowUserAPIView(APIView):
    def post(self, request, username):
        try:
            user_to_follow = User.objects.get(username=username)
        except User.DoesNotExist:
            return api_response(
                success=False,
                message="User not found",
                status=status.HTTP_404_NOT_FOUND
            )

        if user_to_follow == request.user:
            return api_response(
                success=False,
                message='You can not follow yourself',
                status=status.HTTP_400_BAD_REQUEST
            )

        follow, created = Follow.objects.get_or_create(
            follower=request.user,
            following=user_to_follow
        )

        if not created:
            return api_response(
                success=False,
                message='Follow already created',
                status=status.HTTP_400_BAD_REQUEST
            )
        return api_response(
            success=True,
            message=f'You are now following {user_to_follow.username}',
            status=status.HTTP_201_CREATED
        )


@extend_schema(tags=['follow'])
class UnfollowUserAPIView(APIView):
    def post(self, request, username):
        try:
            user_to_unfollow = User.objects.get(username=username)
        except User.DoesNotExist:
            return api_response(
                success=False,
                message="User not found",
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            follow = Follow.objects.get(follower=request.user, following=user_to_unfollow)
            follow.delete()
            return api_response(
                success=True,
                message=f"You have unfollowed {user_to_unfollow.username}",
                data=None
            )
        except Follow.DoesNotExist:
            return api_response(
                success=False,
                message="You are not following this user",
                status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema(tags=['follow'])
class UserFollowersAPIView(APIView):
    def get(self, request, username):
        user = get_object_or_404(User, username=username)
        followers = Follow.objects.filter(following=user)
        serializer = FollowModelSerializer(followers, many=True)

        return api_response(
            success=True,
            message="Followers retrieved successfully",
            data=serializer.data
        )


@extend_schema(tags=['follow'])
class UserFollowingAPIView(APIView):
    def get(self, request, username):
        user = get_object_or_404(User, username=username)
        following = Follow.objects.filter(follower=user)
        serializer = FollowModelSerializer(following, many=True)

        return api_response(
            success=True,
            message="Following list retrieved successfully",
            data=serializer.data
        )
