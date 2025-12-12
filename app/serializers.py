from rest_framework.serializers import ModelSerializer

from app.models import Post, PostView, PostImage, Comment, Like


class PostModelSerializer(ModelSerializer):
    class Meta:
        model = Post
        fields = '__all__'
        read_only_fields = ('id', 'author', 'created_at', 'updated_at', 'is_edited')

    def update(self, instance, validated_data):
        old_content = instance.content
        new_content = validated_data.get('content', old_content)

        if old_content != new_content:
            validated_data['is_edited'] = True

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['comments'] = CommentModelSerializer(instance.comments.all(), many=True).data
        data['images'] = PostImageModelSerializer(instance.images.all(), many=True).data
        data['likes'] = LikeModelSerializer(instance.likes.all(), many=True).data
        return data


class PostImageModelSerializer(ModelSerializer):
    class Meta:
        model = PostImage
        fields = '__all__'
        read_only_fields = ('id', 'post')


class PostViewModelSerializer(ModelSerializer):
    class Meta:
        model = PostView
        fields = '__all__'
        read_only_fields = ('id', 'user', 'post')


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
