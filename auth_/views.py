import random
from http import HTTPStatus

from celery.utils.time import timezone
from drf_spectacular.utils import extend_schema
from kombu.utils import json
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from auth_.models import User
from auth_.serializers import UserModelSerializer, VerifyCodeSerializer
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
        send_code_email().delay(user, code)
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
