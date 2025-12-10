import random
from http import HTTPStatus

from drf_spectacular.utils import extend_schema
from kombu.utils import json
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from auth_.serializers import UserModelSerializer
from auth_.tasks import send_code_email
from root.settings import redis


################################ USER #################################
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
