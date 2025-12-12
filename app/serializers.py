from rest_framework.serializers import ModelSerializer

from app.models import Post, PostView, PostImage, Comment, Like


class PostModelSerializer(ModelSerializer):
    class Meta:
        model = Post
        fields = '__all__'
        read_only_fields = ('id', 'author', 'created_at', 'updated_at',)

    def update(self, instance, validated_data):
        old_content = instance.content
        new_content = validated_data.get('content', old_content)

        if new_content != old_content:
            validated_data['is_edited'] = True


class PostImageModelSerializer(ModelSerializer):
    class Meta:
        model = PostImage
        fields = ('post', 'image',)
        read_only_fields = ('id',)


class PostViewModelSerializer(ModelSerializer):
    class Meta:
        model = PostView
        fields = '__all__'
        read_only_fields = ('id', 'user')


class CommentModelSerializer(ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'author', 'post')


class LikeModelSerializer(ModelSerializer):
    class Meta:
        model = Like
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'user', 'post')
