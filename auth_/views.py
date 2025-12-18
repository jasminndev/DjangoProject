import random
from http import HTTPStatus

from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from kombu.utils import json
from rest_framework import status
from rest_framework.generics import GenericAPIView, UpdateAPIView, RetrieveAPIView, DestroyAPIView, ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from app.models import Post
from app.serializers import PostModelSerializer
from auth_.models import Follow
from auth_.models import User
from auth_.serializers import UserModelSerializer, VerifyCodeSerializer, UserUpdateModelSerializer, \
    UserProfileSerializer, FollowModelSerializer
from auth_.tasks import send_code_email
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
        return Response({'message': 'Verification code is sent'}, status=HTTPStatus.OK)


@extend_schema(tags=['auth'])
class VerifyEmailGenericAPIView(GenericAPIView):
    serializer_class = VerifyCodeSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_data = serializer.context.get('user_data')
        user = User.objects.create(**user_data)
        return Response(UserModelSerializer(user).data, status=HTTPStatus.CREATED)


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
    lookup_field = 'pk'

    def get_object(self):
        return self.request.user


@extend_schema(tags=['user'])
class UserDeleteAPIView(DestroyAPIView):
    serializer_class = UserModelSerializer
    lookup_field = 'pk'
    queryset = User.objects.all()

    def get_object(self):
        return self.request.user


@extend_schema(tags=['user'])
class UserDetailAPIView(RetrieveAPIView):
    queryset = User.objects.all()
    lookup_field = 'pk'
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user


@extend_schema(tags=['user'])
class UserListAPIView(ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer


@extend_schema(tags=['user'])
class UserProfileByUsernameAPIView(RetrieveAPIView):
    queryset = User.objects.all()
    lookup_field = 'username'
    serializer_class = UserProfileSerializer


@extend_schema(tags=['user'])
class SuggestedUsersAPIView(ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer

    def get_queryset(self):
        user = self.request.user
        following_ids = Follow.objects.filter(follower=user).values_list('following_id', flat=True)
        return User.objects.exclude(
            Q(id=user.id) | Q(id__in=following_ids)
        ).order_by('-date_joined')[:10]


@extend_schema(tags=['user'])
class UserPostsAPIView(ListAPIView):
    serializer_class = PostModelSerializer

    def get_queryset(self):
        username = self.kwargs.get('username')
        try:
            user = User.objects.get(username=username)
            return Post.objects.filter(user=user).order_by('-created_at')
        except User.DoesNotExist:
            return Post.objects.none()


##################################### FOLLOW #######################################3

@extend_schema(tags=['follow'])
class FollowUserAPIView(APIView):
    def post(self, request, username):
        try:
            user_to_follow = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        if user_to_follow == request.user:
            return Response({'error': 'You can not follow yourself'}, status=status.HTTP_400_BAD_REQUEST)

        follow, created = Follow.objects.get_or_create(
            follower=request.user,
            following=user_to_follow
        )

        if not created:
            return Response({'error': 'Follow already exists'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'message': f'You are now following {user_to_follow.username}'}, status=status.HTTP_201_CREATED)


@extend_schema(tags=['follow'])
class UnfollowUserAPIView(APIView):
    def post(self, request, username):
        try:
            user_to_unfollow = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            follow = Follow.objects.get(follower=request.user, following=user_to_unfollow)
            follow.delete()
            return Response({'message': f"You have unfollowed {user_to_unfollow.username}"}, status=status.HTTP_200_OK)
        except Follow.DoesNotExist:
            return Response({'error': 'You are not following this user'}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=['follow'])
class UserFollowersAPIView(APIView):
    serializer_class = FollowModelSerializer

    def get_queryset(self):
        username = self.kwargs.get('username')
        try:
            user = User.objects.get(username=username)
            return Follow.objects.filter(following=user)
        except User.DoesNotExist:
            return Follow.objects.none()


@extend_schema(tags=['follow'])
class UserFollowingAPIView(APIView):
    serializer_class = FollowModelSerializer

    def get_queryset(self):
        username = self.kwargs.get('username')
        try:
            user = User.objects.get(username=username)
            return Follow.objects.filter(follower=user)
        except User.DoesNotExist:
            return Follow.objects.none()
