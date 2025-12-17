from rest_framework.fields import ReadOnlyField
from rest_framework.serializers import ModelSerializer

from app.models import Post, PostView, Like, Follow, Comment
from auth_.serializers import UserModelSerializer


class CommentModelSerializer(ModelSerializer):
    user = UserModelSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ('id', 'post', 'user', 'text', 'created_at')
        read_only_fields = ('id', 'created_at', 'user', 'post')


class PostModelSerializer(ModelSerializer):
    user = UserModelSerializer(read_only=True)
    likes_count = ReadOnlyField()
    comments_count = ReadOnlyField()
    is_liked = ReadOnlyField()
    comments = CommentModelSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = (
            'id', 'caption', 'user', 'likes_count', 'comments_count', 'is_liked', 'comments', 'image', 'created_at',
            'updated_at')
        read_only_fields = ('id', 'user', 'created_at', 'updated_at', 'is_edited')

    def update(self, instance, validated_data):
        old_content = instance.contentauthor
        new_content = validated_data.get('content', old_content)

        if old_content != new_content:
            validated_data['is_edited'] = True

        return super().update(instance, validated_data)

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Like.objects.filter(user=request.user, post=obj).exists()
        return False

    # def to_representation(self, instance):
    #     data = super().to_representation(instance)
    #     data['comments'] = CommentModelSerializer(instance.comments.all(), many=True).data
    #     data['likes'] = LikeModelSerializer(instance.likes.all(), many=True).data
    #     return data


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
    user = UserModelSerializer(read_only=True)

    class Meta:
        model = Like
        fields = ('id', 'post', 'user', 'created_at')
        read_only_fields = ('id', 'created_at', 'user')


class FollowModelSerializer(ModelSerializer):
    follower = UserModelSerializer(read_only=True)
    following = UserModelSerializer(read_only=True)

    class Meta:
        model = Follow
        fields = ('id', 'follower', 'following', 'created_at')
        read_only_fields = ('id', 'follower', 'following', 'created_at')
