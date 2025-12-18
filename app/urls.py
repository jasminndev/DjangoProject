from django.urls import path

from app.views import (
    PostCreateAPIView, PostListAPIView,
    CommentCreateAPIView, CommentListAPIView,
    LikeCreateAPIView, LikeListAPIView, PostDestroyAPIView,
    PostUpdateAPIView, PostDetailAPIView,
    CommentDestroyAPIView, LikeCountAPIView
)

urlpatterns = [
    path('posts/', PostListAPIView.as_view()),
    path('posts/create/', PostCreateAPIView.as_view()),
    path('posts/<int:pk>/delete/', PostDestroyAPIView.as_view()),
    path('posts/<int:pk>/update/', PostUpdateAPIView.as_view()),
    path('posts/<int:pk>/detail/', PostDetailAPIView.as_view()),
]

urlpatterns += [
    path('posts/<int:post_id>/comments/', CommentListAPIView.as_view()),
    path('posts/<int:post_id>/comments/create/', CommentCreateAPIView.as_view()),
    path('posts/<int:pk>/comments/delete/', CommentDestroyAPIView.as_view()),
]

urlpatterns += [
    path('posts/<int:post_id>/likes/', LikeListAPIView.as_view()),
    path('posts/<int:post_id>/likes/create/', LikeCreateAPIView.as_view()),
    path('posts/<int:post_id>/likes/count/', LikeCountAPIView.as_view()),
]
