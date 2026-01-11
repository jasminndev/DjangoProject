from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer

from app.models import Post, PostView, Like, Comment
from authentication.serializers import UserProfileSecondSerializer


class CommentModelSerializer(ModelSerializer):
    user = UserProfileSecondSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ('id', 'post', 'user', 'text', 'created_at')
        read_only_fields = ('id', 'created_at', 'user', 'post')

    def validate_text(self, value):
        if not value or not value.strip():
            raise ValidationError(_('Comment cannot be empty'))
        if len(value) > 500:
            raise ValidationError(_('Comment is too long (maximum 500 characters)'))
        return value


class PostModelSerializer(ModelSerializer):
    user = UserProfileSecondSerializer(read_only=True)
    likes_count = SerializerMethodField()
    comments_count = SerializerMethodField()
    is_liked = SerializerMethodField()

    class Meta:
        model = Post
        fields = (
            'id', 'caption', 'user', 'likes_count', 'comments_count', 'is_liked', 'image', 'created_at',
            'updated_at')
        read_only_fields = ('id', 'user', 'created_at', 'updated_at', 'is_edited')

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_comments_count(self, obj):
        return obj.comments.count()

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Like.objects.filter(user=request.user, post=obj).exists()
        return False

    def update(self, instance, validated_data):
        old_caption = instance.caption
        new_caption = validated_data.get('caption', old_caption)

        if old_caption != new_caption:
            validated_data['is_edited'] = True

        return super().update(instance, validated_data)


class PostCreateModelSerializer(ModelSerializer):
    user = UserProfileSecondSerializer(read_only=True)
    image_url = SerializerMethodField()

    class Meta:
        model = Post
        fields = ('id', 'caption', 'user', 'created_at', 'updated_at', 'is_edited', 'image', 'image_url')
        read_only_fields = ('id', 'created_at', 'updated_at', 'is_edited')
        extra_kwargs = {
            'image': {'write_only': True},
        }

    def validate_image(self, value):
        if not value:
            raise ValidationError(_('Image is required'))

        if value.size > 10 * 1024 * 1024:
            raise ValidationError(_('Image size cannot be exceed 10MB'))

        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
        if hasattr(value, 'content_type') and value.content_type not in allowed_types:
            raise ValidationError(_('Only JPEG, PNG, GIF and WebP images are allowed'))

        return value

    def validate_caption(self, value):
        if value and len(value) > 2200:
            raise ValidationError(_('Caption is too long (maximum 2200 characters)'))
        return value

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None


class PostViewModelSerializer(ModelSerializer):
    class Meta:
        model = PostView
        fields = '__all__'
        read_only_fields = ('id', 'user', 'post')


class LikeModelSerializer(ModelSerializer):
    user = UserProfileSecondSerializer(read_only=True)

    class Meta:
        model = Like
        fields = ('id', 'post', 'user', 'created_at')
        read_only_fields = ('id', 'created_at', 'user', 'post')
