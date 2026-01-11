import json
import logging
import re

from django.contrib.auth.hashers import make_password
from django.core.validators import validate_email, RegexValidator
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, ReadOnlyField, SerializerMethodField
from rest_framework.serializers import ModelSerializer, Serializer

from authentication.models import User, Follow
from root.settings import redis

logger = logging.getLogger(__name__)


class UserModelSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'username', 'email', 'password', 'bio',)
        read_only_fields = ('id', 'date_joined', 'is_deleted')

    def validate_email(self, value):
        try:
            validate_email(value)
        except ValidationError:
            raise ValidationError(_('Email must be valid!'))

        if User.objects.filter(email=value).exists():
            logger.warning("Registration failed: email already registered | email=%s", value)
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
            logger.warning("Username too short | username=%s", value)
            raise ValidationError(_('Username must be at least 3 characters long.'))
        if value.lower() in reserved:
            logger.warning("Reserved username attempt | username=%s", value)
            raise ValidationError(_('This username is not valid!'))
        if User.objects.filter(username=value).exists():
            logger.warning("Username already taken | username=%s", value)
            raise ValidationError(_('This username is already taken!'))

        return value

    def validate_password(self, value):
        VALIDATOR = re.compile(
            r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>])[A-Za-z\d!@#$%^&*(),.?":{}|<>]{8,64}$'
        )
        if not VALIDATOR.match(value):
            logger.warning("Weak password rejected during registration")
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
            logger.warning("Invalid or expired verification code used | code=%s", value)
            raise ValidationError(_('Invalid or expired code!'))

        user_data = json.loads(data)
        self.context['user_data'] = user_data
        return value


class UserUpdateModelSerializer(ModelSerializer):
    avatar_url = SerializerMethodField()

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'avatar', 'bio', 'avatar_url')
        extra_kwargs = {
            'avatar': {'write_only': True, 'required': False},
        }

    username_validation = RegexValidator(
        regex=r'^[a-zA-Z0-9_.]+$',
        message=_("Username should contain only letters, numbers and underscores.")
    )

    def validate_username(self, value):
        self.username_validation(value)

        reserved = ['admin', 'user', 'root', 'null']

        if len(value) < 3:
            logger.warning("Username too short during update | username=%s", value)
            raise ValidationError(_('Username must be at least 3 characters long.'))

        if value.lower() in reserved:
            logger.warning("Reserved username update attempt | username=%s", value)
            raise ValidationError(_('This username is not valid!'))

        user = self.instance
        if User.objects.exclude(id=user.id).filter(username=value).exists():
            logger.warning(
                "Username conflict during update | user_id=%s | username=%s",
                user.id,
                value
            )
            raise ValidationError(_('This username is already taken!'))

        return value

    def update(self, instance, validated_data):
        if 'avatar' in validated_data and instance.avatar:
            instance.avatar.delete(save=False)
        return super().update(instance, validated_data)

    def get_avatar_url(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None


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
