from rest_framework.serializers import ModelSerializer

from apps.models import Post, PostView, PostImage


class PostModelSerializer(ModelSerializer):
    class Meta:
        model = Post
        fields = ('content',)
        read_only_fields = ('id', 'author', 'created_at', 'updated_at',)


class PostViewModelSerializer(ModelSerializer):
    class Meta:
        model = PostView
        fields = ('user',)


class PostImageModelSerializer(ModelSerializer):
    class Meta:
        model = PostImage
        fields = ('id', 'post', 'image')
