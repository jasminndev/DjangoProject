from http import HTTPStatus

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework.generics import CreateAPIView, ListAPIView, DestroyAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from app.models import Post, PostImage, PostView, Comment, Like
from app.serializers import PostImageModelSerializer, PostModelSerializer, CommentModelSerializer, LikeModelSerializer


###################################### POST ######################################
@extend_schema(tags=['post'])
class PostCreateAPIView(CreateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostModelSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


@extend_schema(tags=['post'])
class PostListAPIView(ListAPIView):
    queryset = Post.objects.all()
    serializer_class = PostModelSerializer


@extend_schema(tags=['post'])
class PostDestroyAPIView(DestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostModelSerializer
    lookup_field = 'pk'


@extend_schema(tags=['post'])
class PostUpdateAPIView(UpdateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostModelSerializer
    lookup_field = 'pk'


@extend_schema(tags=['post'])
class PostDetailAPIView(RetrieveAPIView):
    queryset = Post.objects.all()
    serializer_class = PostModelSerializer
    lookup_field = 'pk'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        if request.user.is_authenticated:
            PostView.objects.get_or_create(post=instance, user=request.user)

        serializer = self.get_serializer(instance)
        data = serializer.data
        data['views'] = instance.views.count()
        return Response(data)


###################################### POST-IMAGE ######################################
@extend_schema(tags=['post-image'])
class PostImageCreateAPIView(CreateAPIView):
    queryset = PostImage.objects.all()
    serializer_class = PostImageModelSerializer

    def perform_create(self, serializer):
        post_id = self.kwargs.get("post_id")
        post = get_object_or_404(Post, pk=post_id)
        serializer.save(post=post)


@extend_schema(tags=['post-image'])
class PostImageListAPIView(ListAPIView):
    queryset = PostImage.objects.all()
    serializer_class = PostImageModelSerializer


@extend_schema(tags=['post-image'])
class PostImageDestroyAPIView(DestroyAPIView):
    queryset = PostImage.objects.all()
    serializer_class = PostImageModelSerializer
    lookup_field = 'pk'


@extend_schema(tags=['post-image'])
class PostImageUpdateAPIView(UpdateAPIView):
    queryset = PostImage.objects.all()
    serializer_class = PostImageModelSerializer
    lookup_field = 'pk'


###################################### COMMENT ######################################
@extend_schema(tags=['comment'])
class CommentCreateAPIView(CreateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentModelSerializer

    def perform_create(self, serializer):
        post_id = self.kwargs.get('post_id')
        post = get_object_or_404(Post, id=post_id)
        serializer.save(author=self.request.user, post=post)


@extend_schema(tags=['comment'])
class CommentListAPIView(ListAPIView):
    serializer_class = CommentModelSerializer

    def get_queryset(self):
        post_id = self.kwargs.get('post_id')
        return Comment.objects.filter(post_id=post_id)


@extend_schema(tags=['comment'])
class CommentDestroyAPIView(DestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentModelSerializer
    lookup_field = 'pk'


###################################### POST-LIKE ######################################
@extend_schema(tags=['like'])
class LikeCreateAPIView(CreateAPIView):
    queryset = Like.objects.all()
    serializer_class = LikeModelSerializer

    def perform_create(self, serializer):
        post_id = self.kwargs.get('post_id')
        post = get_object_or_404(Post, id=post_id)

        if Like.objects.filter(user=self.request.user, post=post).exists():
            return

        serializer.save(user=self.request.user, post=post)


@extend_schema(tags=['like'])
class LikeListAPIView(ListAPIView):
    serializer_class = LikeModelSerializer

    def get_queryset(self):
        post_id = self.kwargs.get('post_id')
        return Like.objects.filter(post_id=post_id)


@extend_schema(tags=['like'])
class LikeCountAPIView(APIView):
    serializer_class = LikeModelSerializer

    def get(self, request, post_id):
        blog = Post.objects.filter(pk=post_id).first()
        quantity = blog.likes.count()
        return Response({'count': quantity}, status=HTTPStatus.OK)
