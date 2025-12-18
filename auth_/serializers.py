import json

from django.contrib.auth.hashers import make_password
from django.core.validators import validate_email, RegexValidator
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, ReadOnlyField, SerializerMethodField
from rest_framework.serializers import ModelSerializer, Serializer

from auth_.models import User, Follow
from root.settings import redis


class UserModelSerializer(ModelSerializer):
    followers_count = ReadOnlyField()
    following_count = ReadOnlyField()
    posts_count = ReadOnlyField()
    is_following = SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'username', 'email', 'password', 'avatar', 'bio', 'followers_count',
                  'following_count', 'posts_count', 'is_following')
        read_only_fields = ('id', 'date_joined')

    def validate_email(self, value):
        try:
            validate_email(value)
        except ValidationError:
            raise ValidationError('Email must be valid!')

        if User.objects.filter(email=value).exists():
            raise ValidationError('Email already registered!')

        return value

    username_validation = RegexValidator(
        regex=r'^[a-zA-Z0-9_.]+$',
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

    def get_is_following(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated():
            return Follow.objects.filter(
                follower=request.user,
                following=obj
            ).exists()
        return False


class UserProfileSerializer(ModelSerializer):
    followers_count = ReadOnlyField()
    following_count = ReadOnlyField()
    posts_count = ReadOnlyField()
    is_following = SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'username', 'email', 'password', 'avatar', 'bio', 'followers_count',
                  'following_count', 'posts_count', 'is_following')
        read_only_fields = ('id', 'date_joined')

    def get_is_following(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated():
            return Follow.objects.filter(
                follower=request.user,
                following=obj
            ).exists()
        return False


class VerifyCodeSerializer(Serializer):
    code = CharField(
        max_length=6,
        validators=[RegexValidator(r'^\d{6}$', 'Code must be 6 digits.')]
    )

    def validate_code(self, value):
        data = redis.get(value)
        if not data:
            raise ValidationError('Invalid code!')
        user_data = json.loads(data)
        self.context['user_data'] = user_data
        return value


class UserUpdateModelSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'avatar', 'bio',)

    username_validation = RegexValidator(
        regex=r'^[a-zA-Z0-9_.]+$',
        message="Username should contain only letters, numbers and underscores."
    )

    def validate_username(self, value):
        self.username_validation(value)

        reserved = ['admin', 'user', 'root', 'null']

        if len(value) < 3:
            raise ValidationError('Username must be at least 3 characters long.')
        if value.lower() in reserved:
            raise ValidationError('This username is not valid!')

        user = self.instance
        if User.objects.exclude(id=user.id).filter(username=value).exists():
            raise ValidationError('This username is already taken!')

        return value

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class FollowModelSerializer(ModelSerializer):
    follower = UserModelSerializer(read_only=True)
    following = UserModelSerializer(read_only=True)

    class Meta:
        model = Follow
        fields = ('id', 'follower', 'following', 'created_at')
        read_only_fields = ('id', 'follower', 'following', 'created_at')
