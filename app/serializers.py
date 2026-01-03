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
            return obj.likes.filter(user=request.user).exists()
        return False

    def update(self, instance, validated_data):
        old_caption = instance.caption
        new_caption = validated_data.get('caption', old_caption)

        if old_caption != new_caption:
            validated_data['is_edited'] = True

        return super().update(instance, validated_data)


class PostCreateModelSerializer(ModelSerializer):
    class Meta:
        model = Post
        fields = ('id', 'caption', 'user', 'created_at', 'updated_at', 'is_edited')
        read_only_fields = ('id', 'created_at', 'updated_at', 'is_edited')


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
