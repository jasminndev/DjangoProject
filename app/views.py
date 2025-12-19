from datetime import timedelta

from celery.utils.time import timezone
from django.db.models import Count, Q, F
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import CreateAPIView, ListAPIView, DestroyAPIView, RetrieveAPIView, UpdateAPIView, \
    get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from app.models import Post, PostView, Comment, Like
from app.permissions import IsOwnerOrReadOnly, IsOwnerOrAdmin
from app.serializers import PostModelSerializer, CommentModelSerializer, LikeModelSerializer
from auth_.models import Follow


###################################### POST ######################################
@extend_schema(tags=['post'])
class PostCreateAPIView(CreateAPIView):
    serializer_class = PostModelSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@extend_schema(tags=['post'])
class PostListAPIView(ListAPIView):
    queryset = Post.objects.all().order_by('-created_at')
    serializer_class = PostModelSerializer


@extend_schema(tags=['post'])
class PostDeleteAPIView(DestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostModelSerializer
    permission_classes = [IsOwnerOrReadOnly]
    lookup_field = 'pk'


@extend_schema(tags=['post'])
class PostUpdateAPIView(UpdateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostModelSerializer
    permission_classes = [IsOwnerOrReadOnly]
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


@extend_schema(tags=['post-feed'])
class PostFeedAPIView(ListAPIView):
    serializer_class = PostModelSerializer

    def get_queryset(self):
        user = self.request.user
        following_ids = Follow.objects.filter(follower=user).values_list('following_id', flat=True)
        return Post.objects.filter(
            Q(user=user) | Q(user_id__in=following_ids)
        ).order_by('-created_at')


@extend_schema(tags=['post-feed'])
class TopPostsAPIView(ListAPIView):
    serializer_class = PostModelSerializer

    def get_queryset(self):
        days_ago = 7
        time_threshold = timezone.now() - timedelta(days=days_ago)

        posts = Post.objects.filter(
            created_at__gte=time_threshold
        ).annotate(
            likes_count_db=Count('likes', distinct=True),
            comments_count_db=Count('comments', distinct=True),
            engagement_score=F('likes_count_db') + F('comments_count_db')
        ).select_related('user').prefetch_related(
            'likes', 'comments'
        ).order_by('-engagement_score', '-created_at')

        return posts


###################################### LIKE ######################################
@extend_schema(tags=['like'])
class PostLikeAPIView(APIView):
    def post(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)

        like, created = Like.objects.get_or_create(user=request.user, post=post)

        if not created:
            return Response({'error': 'You have already liked this post'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'success': True}, status=status.HTTP_201_CREATED)


@extend_schema(tags=['like'])
class PostUnlikeAPIView(APIView):
    def post(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            like = Like.objects.get(user=request.user, post=post)
            like.delete()
            return Response({'success': True}, status=status.HTTP_200_OK)
        except Like.DoesNotExist:
            return Response({'error': 'You have not liked this post'}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=['like'])
class PostLikesListAPIView(ListAPIView):
    serializer_class = LikeModelSerializer

    def get_queryset(self):
        post_id = self.kwargs.get('pk')
        return Like.objects.filter(post__id=post_id).order_by('-created_at')


###################################### COMMENT ######################################
@extend_schema(tags=['comment'])
class CommentCreateAPIView(CreateAPIView):
    serializer_class = CommentModelSerializer

    def perform_create(self, serializer):
        post = get_object_or_404(Post, id=self.kwargs["post_id"])
        serializer.save(
            user=self.request.user,
            post=post
        )


@extend_schema(tags=['comment'])
class CommentDeleteAPIView(DestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentModelSerializer
    lookup_field = 'pk'
    permission_classes = [IsOwnerOrAdmin]


@extend_schema(tags=['comment'])
class PostCommentsListAPIView(ListAPIView):
    serializer_class = CommentModelSerializer

    def get_queryset(self):
        post_id = self.kwargs.get('post_id')
        return Comment.objects.filter(post_id=post_id).order_by('-created_at')
