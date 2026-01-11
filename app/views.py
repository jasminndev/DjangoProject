import logging
from datetime import timedelta

from celery.utils.time import timezone
from django.db.models import Count, Q, F
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import CreateAPIView, ListAPIView, DestroyAPIView, RetrieveAPIView, UpdateAPIView, \
    get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from app.error_codes import ErrorCode
from app.models import Post, PostView, Comment, Like
from app.permissions import IsOwnerOrReadOnly, IsOwnerOrAdmin
from app.serializers import PostModelSerializer, CommentModelSerializer, LikeModelSerializer
from authentication.models import Follow
from authentication.permissions import IsActiveUser
from core.functions import api_response
from core.utils import RequestLoggingMiddleware

logger = logging.getLogger(__name__)


###################################### POST ######################################
@extend_schema(tags=['post'])
class PostCreateAPIView(CreateAPIView):
    serializer_class = PostModelSerializer
    permission_classes = [IsActiveUser]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        ip = RequestLoggingMiddleware.get_client_ip(request)
        logger.info("Post create attempt | user_id=%s | ip=%s", request.user.id, ip)
        response = super().create(request, *args, **kwargs)
        logger.info("Post created successfully | user_id=%s | ip=%s", request.user.id, ip)
        return api_response(
            success=True,
            message=_("Post created successfully"),
            data=response.data,
            status=status.HTTP_201_CREATED
        )


@extend_schema(tags=['post'])
class PostListAPIView(ListAPIView):
    queryset = Post.objects.all().order_by('-created_at')
    serializer_class = PostModelSerializer
    permission_classes = [IsAuthenticated, IsActiveUser]

    def list(self, request, *args, **kwargs):
        ip = RequestLoggingMiddleware.get_client_ip(request)
        logger.debug("Post list accessed | user_id=%s | ip=%s", request.user.id, ip)
        response = super().list(request, *args, **kwargs)
        return api_response(
            success=True,
            message=_("Posts retrieved successfully"),
            data=response.data
        )


@extend_schema(tags=['post'])
class PostDeleteAPIView(DestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostModelSerializer
    permission_classes = [IsOwnerOrReadOnly, IsActiveUser]
    lookup_field = 'pk'

    def destroy(self, request, *args, **kwargs):
        ip = RequestLoggingMiddleware.get_client_ip(request)
        try:
            post = self.get_object()
            super().destroy(request, *args, **kwargs)
            logger.warning("Post deleted | user_id=%s | post_id=%s | ip=%s", request.user.id, post.id, ip)
            return api_response(
                success=True,
                message=_("Post deleted successfully"),
                data=None
            )
        except Exception:
            logger.error("Post delete failed | user_id=%s | pk=%s | ip=%s", request.user.id, kwargs.get('pk'), ip)
            return api_response(
                success=False,
                error_code=ErrorCode.POST_NOT_FOUND,
                message=_("Post not found or you don't have permission"),
                status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema(tags=['post'])
class PostUpdateAPIView(UpdateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostModelSerializer
    permission_classes = [IsOwnerOrReadOnly, IsActiveUser]
    lookup_field = 'pk'

    def update(self, request, *args, **kwargs):
        ip = RequestLoggingMiddleware.get_client_ip(request)
        logger.info("Post update attempt | user_id=%s | post_id=%s | ip=%s", request.user.id, kwargs.get('pk'), ip)
        response = super().update(request, *args, **kwargs)
        logger.info("Post updated successfully | user_id=%s | post_id=%s | ip=%s", request.user.id, kwargs.get('pk'),
                    ip)
        return api_response(
            success=True,
            message=_("Post updated successfully"),
            data=response.data
        )


@extend_schema(tags=['post'])
class PostDetailAPIView(RetrieveAPIView):
    queryset = Post.objects.all()
    serializer_class = PostModelSerializer
    lookup_field = 'pk'
    permission_classes = [IsAuthenticated, IsActiveUser]

    def retrieve(self, request, *args, **kwargs):
        ip = RequestLoggingMiddleware.get_client_ip(request)
        instance = self.get_object()
        logger.debug("Post detail viewed | user_id=%s | post_id=%s | ip=%s", request.user.id, instance.id, ip)

        if request.user.is_authenticated:
            PostView.objects.get_or_create(post=instance, user=request.user)

        serializer = self.get_serializer(instance)
        data = serializer.data
        data['views'] = instance.views.count()
        return api_response(
            success=True,
            message=_("Post retrieved successfully"),
            data=data
        )


@extend_schema(tags=['post-feed'])
class PostFeedAPIView(ListAPIView):
    serializer_class = PostModelSerializer
    permission_classes = [IsAuthenticated, IsActiveUser]

    def get_queryset(self):
        user = self.request.user
        following_ids = Follow.objects.filter(follower=user).values_list("following_id", flat=True)
        return Post.objects.filter(
            Q(user=user) | Q(user_id__in=following_ids)
        ).order_by("-created_at")

    def list(self, request, *args, **kwargs):
        ip = RequestLoggingMiddleware.get_client_ip(request)
        logger.debug("Post feed accessed | user_id=%s | ip=%s", request.user.id, ip)
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return api_response(
            success=True,
            message=_("Feed retrieved successfully"),
            data=serializer.data
        )


@extend_schema(tags=['post-feed'])
class TopPostsAPIView(ListAPIView):
    serializer_class = PostModelSerializer
    permission_classes = [IsAuthenticated, IsActiveUser]

    def get_queryset(self):
        time_threshold = timezone.now() - timedelta(days=7)
        return Post.objects.filter(
            created_at__gte=time_threshold
        ).annotate(
            likes_count_db=Count("likes", distinct=True),
            comments_count_db=Count("comments", distinct=True),
            engagement_score=F("likes_count_db") + F("comments_count_db")
        ).order_by("-engagement_score", "-created_at")

    def list(self, request, *args, **kwargs):
        ip = RequestLoggingMiddleware.get_client_ip(request)
        logger.debug("Top posts accessed | user_id=%s | ip=%s", request.user.id, ip)
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return api_response(
            success=True,
            message=_("Top posts retrieved successfully"),
            data=serializer.data
        )


@extend_schema(tags=['profile'])
class MyPostsAPIView(ListAPIView):
    serializer_class = PostModelSerializer
    permission_classes = [IsAuthenticated, IsActiveUser]

    def get_queryset(self):
        return Post.objects.filter(
            user=self.request.user
        ).order_by("-created_at")

    def list(self, request, *args, **kwargs):
        ip = RequestLoggingMiddleware.get_client_ip(request)
        logger.debug("My posts accessed | user_id=%s | ip=%s", request.user.id, ip)
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return api_response(
            success=True,
            message=_("My posts retrieved successfully"),
            data=serializer.data
        )


###################################### LIKE ######################################
@extend_schema(tags=['like'])
class PostLikeAPIView(APIView):
    permission_classes = [IsActiveUser]

    def post(self, request, pk):
        ip = RequestLoggingMiddleware.get_client_ip(request)
        post = get_object_or_404(Post, pk=pk)
        logger.info("Post like attempt | user_id=%s | post_id=%s | ip=%s", request.user.id, pk, ip)

        like, created = Like.objects.get_or_create(
            user=request.user,
            post=post
        )

        if not created:
            logger.warning("Post already liked | user_id=%s | post_id=%s | ip=%s", request.user.id, pk, ip)
            return api_response(
                success=False,
                error_code=ErrorCode.POST_ALREADY_LIKED,
                message=_("You have already liked this post"),
                status=status.HTTP_400_BAD_REQUEST
            )

        logger.info("Post liked successfully | user_id=%s | post_id=%s | ip=%s", request.user.id, pk, ip)
        return api_response(
            success=True,
            message=_("Post liked successfully"),
            data=None,
            status=status.HTTP_201_CREATED
        )


@extend_schema(tags=['like'])
class PostUnlikeAPIView(APIView):
    permission_classes = [IsActiveUser]

    def post(self, request, pk):
        ip = RequestLoggingMiddleware.get_client_ip(request)
        post = get_object_or_404(Post, pk=pk)
        logger.info("Post unlike attempt | user_id=%s | post_id=%s | ip=%s", request.user.id, pk, ip)

        try:
            like = Like.objects.get(user=request.user, post=post)
            like.delete()
            logger.info("Post unliked successfully | user_id=%s | post_id=%s | ip=%s", request.user.id, pk, ip)
            return api_response(
                success=True,
                message=_("Post unliked successfully"),
                data=None
            )
        except Like.DoesNotExist:
            logger.warning("Post not liked | user_id=%s | post_id=%s | ip=%s", request.user.id, pk, ip)
            return api_response(
                success=False,
                error_code=ErrorCode.POST_NOT_LIKED,
                message=_("You have not liked this post"),
                status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema(tags=['like'])
class PostLikesListAPIView(ListAPIView):
    serializer_class = LikeModelSerializer
    permission_classes = [IsAuthenticated, IsActiveUser]

    def get_queryset(self):
        return Like.objects.filter(
            post_id=self.kwargs["pk"]
        ).order_by("-created_at")

    def list(self, request, *args, **kwargs):
        ip = RequestLoggingMiddleware.get_client_ip(request)
        logger.debug("Post likes list accessed | user_id=%s | post_id=%s | ip=%s", request.user.id, self.kwargs["pk"],
                     ip)
        response = super().list(request, *args, **kwargs)
        return api_response(
            success=True,
            message=_("Post likes retrieved successfully"),
            data=response.data
        )


###################################### COMMENT ######################################
@extend_schema(tags=['comment'])
class CommentCreateAPIView(CreateAPIView):
    serializer_class = CommentModelSerializer
    permission_classes = [IsActiveUser]

    def perform_create(self, serializer):
        post = get_object_or_404(Post, id=self.kwargs["post_id"])
        serializer.save(
            user=self.request.user,
            post=post
        )

    def create(self, request, *args, **kwargs):
        ip = RequestLoggingMiddleware.get_client_ip(request)
        logger.info("Comment create attempt | user_id=%s | post_id=%s | ip=%s", request.user.id, self.kwargs["post_id"],
                    ip)
        response = super().create(request, *args, **kwargs)
        logger.info("Comment created successfully | user_id=%s | post_id=%s | comment_id=%s | ip=%s",
                    request.user.id, self.kwargs["post_id"], response.data.get("id"), ip)
        return api_response(
            success=True,
            message=_("Comment created successfully"),
            data=response.data,
            status=status.HTTP_201_CREATED
        )


@extend_schema(tags=['comment'])
class CommentDeleteAPIView(DestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentModelSerializer
    lookup_field = 'pk'
    permission_classes = [IsOwnerOrAdmin, IsActiveUser]

    def destroy(self, request, *args, **kwargs):
        ip = RequestLoggingMiddleware.get_client_ip(request)
        try:
            comment = self.get_object()
            super().destroy(request, *args, **kwargs)
            logger.warning("Comment deleted | user_id=%s | comment_id=%s | ip=%s", request.user.id, comment.id, ip)
            return api_response(
                success=True,
                message=_("Comment deleted successfully"),
                data=None
            )
        except Exception:
            logger.error("Comment delete failed | user_id=%s | pk=%s | ip=%s", request.user.id, kwargs.get('pk'), ip)
            return api_response(
                success=False,
                error_code=ErrorCode.COMMENT_NOT_FOUND,
                message=_("Comment not found or you don't have permission"),
                status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema(tags=['comment'])
class PostCommentsListAPIView(ListAPIView):
    serializer_class = CommentModelSerializer
    permission_classes = [IsAuthenticated, IsActiveUser]

    def get_queryset(self):
        post_id = self.kwargs.get('post_id')
        return Comment.objects.filter(post_id=post_id).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        ip = RequestLoggingMiddleware.get_client_ip(request)
        logger.debug("Post comments list accessed | user_id=%s | post_id=%s | ip=%s", request.user.id,
                     self.kwargs.get('post_id'), ip)
        response = super().list(request, *args, **kwargs)
        return api_response(
            success=True,
            message=_("Comments retrieved successfully"),
            data=response.data
        )
