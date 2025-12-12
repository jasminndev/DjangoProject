from django.urls import path

from app.views import PostCreateAPIView, PostListAPIView, PostImageCreateAPIView, PostImageListAPIView, \
    PostViewCreateAPIView, CommentCreateAPIView, CommentListAPIView, LikeCreateAPIView, LikeListAPIView, \
    PostDestroyAPIView, PostUpdateAPIView, PostDetailAPIView, PostImageDestroyAPIView, PostImageUpdateAPIView, \
    CommentDestroyAPIView

urlpatterns = [
    path('posts/', PostListAPIView.as_view()),
    path('posts/create/', PostCreateAPIView.as_view()),
    path('posts/<int:pk>/delete/', PostDestroyAPIView.as_view()),
    path('posts/<int:pk>/update/', PostUpdateAPIView.as_view()),
    path('posts/<int:pk>/detail/', PostDetailAPIView.as_view()),
]

urlpatterns += [
    path('posts/<int:post_id>/images/', PostImageListAPIView.as_view()),
    path('posts/<int:post_id>/images/create/', PostImageCreateAPIView.as_view()),
    path('posts/<int:post_id>/images/delete/', PostImageDestroyAPIView.as_view()),
    path('posts/<int:post_id>/images/update/', PostImageUpdateAPIView.as_view()),
]

urlpatterns += [
    path('posts/<int:post_id>/views/create/', PostViewCreateAPIView.as_view()),
]

urlpatterns += [
    path('posts/<int:post_id>/comments/', CommentListAPIView.as_view()),
    path('posts/<int:post_id>/comments/create/', CommentCreateAPIView.as_view()),
    path('posts/<int:post_id>/comments/delete/', CommentDestroyAPIView.as_view()),
]

urlpatterns += [
    path('posts/<int:post_id>/likes/', LikeListAPIView.as_view()),
    path('posts/<int:post_id>/likes/create/', LikeCreateAPIView.as_view()),
]
