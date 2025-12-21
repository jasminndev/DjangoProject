from django.urls import path

from app.views import (
    PostCreateAPIView, PostListAPIView, CommentCreateAPIView,
    PostUpdateAPIView, PostDetailAPIView, PostFeedAPIView,
    PostDeleteAPIView, PostLikeAPIView, PostUnlikeAPIView,
    PostLikesListAPIView, CommentDeleteAPIView, PostCommentsListAPIView,
    TopPostsAPIView, MyPostsAPIView
)

urlpatterns = [
    path('posts/', PostListAPIView.as_view()),
    path('posts/create/', PostCreateAPIView.as_view()),
    path('posts/<int:pk>/detail', PostDetailAPIView.as_view()),
    path('posts/<int:pk>/update/', PostUpdateAPIView.as_view()),
    path('posts/<int:pk>/delete/', PostDeleteAPIView.as_view()),
    path('posts/<int:pk>/like/', PostLikeAPIView.as_view()),
    path('posts/<int:pk>/unlike/', PostUnlikeAPIView.as_view()),
    path('posts/<int:pk>/likes/', PostLikesListAPIView.as_view()),
    path('home/', PostFeedAPIView.as_view()),
    path('home/feed', TopPostsAPIView.as_view()),
    path('posts/me/', MyPostsAPIView.as_view()),
]

urlpatterns += [
    path('comments/<int:post_id>/create', CommentCreateAPIView.as_view()),
    path('comments/<int:pk>/delete', CommentDeleteAPIView.as_view()),
    path('posts/<int:post_id>/comments', PostCommentsListAPIView.as_view()),
]
