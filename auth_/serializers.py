from django.contrib.auth.hashers import make_password
from django.core.validators import validate_email
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer

from auth_.models import User


class UserModelSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'password', 'avatar', 'bio',)
        read_only_fields = ('id', 'date_joined', 'role')

    def validate_email(self, value):
        try:
            validate_email(value)
        except ValidationError:
            raise ValidationError('Email must be valid!')

        if User.objects.filter(email=value).exists():
            raise ValidationError('Email already registered!')

        return value

    def validate_paswword(self, value):
        if len(value) < 4:
            raise ValidationError('Password must be at least 4 characters!')

        return make_password(value)


class UserUpdateSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'avatar', 'bio',)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
