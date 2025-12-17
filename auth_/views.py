import random
from http import HTTPStatus

from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from kombu.utils import json
from rest_framework.generics import GenericAPIView, UpdateAPIView, RetrieveAPIView, DestroyAPIView, ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from app.models import Follow
from auth_.models import User
from auth_.serializers import UserModelSerializer, VerifyCodeSerializer, UserUpdateModelSerializer, \
    UserProfileSerializer
from auth_.tasks import send_code_email
from root.settings import redis


#################################### AUTH ###################################
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
