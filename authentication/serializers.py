import json
import re

from django.contrib.auth.hashers import make_password
from django.core.validators import validate_email, RegexValidator
from django.utils.translation import gettext as _
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, ReadOnlyField, SerializerMethodField
from rest_framework.serializers import ModelSerializer, Serializer

from authentication.models import User, Follow
from root.settings import redis


class UserModelSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'username', 'email', 'password', 'avatar', 'bio',)
        read_only_fields = ('id', 'date_joined', 'is_deleted')

    def validate_email(self, value):
        try:
            validate_email(value)
        except ValidationError:
            raise ValidationError(_('Email must be valid!'))

        if User.objects.filter(email=value).exists():
            raise ValidationError(_('Email already registered!'))

        return value

    username_validation = RegexValidator(
        regex=r'^[a-zA-Z0-9_.]+$',
        message=_("Username should contain only letters, numbers and underscores.")
    )

    def validate_username(self, value):
        self.username_validation(value)

        reserved = ['admin', 'root', 'null']

        if len(value) < 3:
            raise ValidationError(_('Username must be at least 3 characters long.'))
        if value.lower() in reserved:
            raise ValidationError(_('This username is not valid!'))
        if User.objects.filter(username=value).exists():
            raise ValidationError(_('This username is already taken!'))

        return value

    def validate_password(self, value):
        VALIDATOR = re.compile(
            r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>])[A-Za-z\d!@#$%^&*(),.?":{}|<>]{8,64}$'
        )
        if not VALIDATOR.match(value):
            raise ValidationError(
                _("Password must be 8–64 characters long and include at least "
                  "one uppercase letter, one lowercase letter, one number, "
                  "and one special character.")
            )

        return make_password(value)


class UserProfileSerializer(ModelSerializer):
    followers_count = ReadOnlyField()
    following_count = ReadOnlyField()
    posts_count = ReadOnlyField()
    is_following = SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'username', 'avatar', 'bio', 'followers_count',
                  'following_count', 'posts_count', 'is_following')
        read_only_fields = ('id', 'date_joined')

    def get_is_following(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Follow.objects.filter(
                follower=request.user,
                following=obj
            ).exists()
        return False


class UserProfileSecondSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'avatar',)
        read_only_fields = ('id', 'username', 'avatar',)


class VerifyCodeSerializer(Serializer):
    code = CharField(
        max_length=6,
        validators=[RegexValidator(r'^\d{6}$', _('Code must be 6 digits.'))]
    )

    def validate_code(self, value):
        redis_key = f"verify:{value}"
        data = redis.get(redis_key)
        if not data:
            raise ValidationError(_('Invalid or expired code!'))
        user_data = json.loads(data)
        self.context['user_data'] = user_data
        return value


class UserUpdateModelSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'avatar', 'bio',)

    username_validation = RegexValidator(
        regex=r'^[a-zA-Z0-9_.]+$',
        message=_("Username should contain only letters, numbers and underscores.")
    )

    def validate_username(self, value):
        self.username_validation(value)

        reserved = ['admin', 'user', 'root', 'null']

        if len(value) < 3:
            raise ValidationError(_('Username must be at least 3 characters long.'))
        if value.lower() in reserved:
            raise ValidationError(_('This username is not valid!'))

        user = self.instance
        if User.objects.exclude(id=user.id).filter(username=value).exists():
            raise ValidationError(_('This username is already taken!'))

        return value

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class FollowModelSerializer(ModelSerializer):
    follower = UserProfileSecondSerializer(read_only=True)
    following = UserProfileSecondSerializer(read_only=True)

    class Meta:
        model = Follow
        fields = ('id', 'follower', 'following', 'created_at')
        read_only_fields = ('id', 'follower', 'following', 'created_at')


class PublicUserSerializer(ModelSerializer):
    followers_count = ReadOnlyField()
    following_count = ReadOnlyField()
    posts_count = ReadOnlyField()
    is_following = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'username',
            'first_name',
            'last_name',
            'avatar',
            'bio',
            'followers_count',
            'following_count',
            'posts_count',
            'is_following',
        )

    def get_is_following(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Follow.objects.filter(
                follower=request.user,
                following=obj
            ).exists()
        return False


class UserLanguageSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ('language',)
