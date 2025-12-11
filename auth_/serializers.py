import json

from django.contrib.auth.hashers import make_password
from django.core.validators import validate_email, RegexValidator
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField
from rest_framework.serializers import ModelSerializer, Serializer

from auth_.models import User
from root.settings import redis


class UserModelSerializer(ModelSerializer):
    referral_code = CharField(read_only=True)
    referred_by_code = CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'password', 'avatar', 'bio', 'referral_code',
                  'referred_by_code')
        read_only_fields = ('id', 'date_joined', 'role')

    def validate_email(self, value):
        try:
            validate_email(value)
        except ValidationError:
            raise ValidationError('Email must be valid!')

        if User.objects.filter(email=value).exists():
            raise ValidationError('Email already registered!')

        return value

    username_validation = RegexValidator(
        regex=r'^[a-zA-Z0-9_.-]+$',
        message="Username should contain only letters, numbers and underscores."
    )

    def validate_username(self, value):
        self.username_validation(value)

        reserved = ['admin', 'user', 'root', 'null']

        if len(value) < 3:
            raise ValidationError('Username must be at least 3 characters long.')
        if value.lower() in reserved:
            raise ValidationError('This username is not valid!')
        if User.objects.filter(username=value).exists():
            raise ValidationError('This username is already taken!')

        return value

    def validate_password(self, value):
        if len(value) < 4:
            raise ValidationError('Password must be at least 4 characters!')

        return make_password(value)


class VerifyCodeSerializer(Serializer):
    code = CharField(max_length=6)

    def validate_code(self, value):
        data = redis.get(value)
        if not data:
            raise ValidationError('Invalid code!')
        user_data = json.loads(data)
        self.context['user_data'] = user_data
        return value


class UserUpdateSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'avatar', 'bio',)

    def validate_username(self, value):
        user = self.instance
        if User.objects.exclude(id=user.id).filter(username=value).exists():
            raise ValidationError('Username already registered!')
        return value

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
