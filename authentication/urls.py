from django.urls import path

from authentication.views import (
    CustomTokenObtainPairView, CustomTokenRefreshView,
    UserGenericAPIView, VerifyEmailGenericAPIView,
    UserUpdateAPIView, UserDetailAPIView,
    UserDeleteAPIView, UserListAPIView,
    SuggestedUsersAPIView, UserProfileByUsernameAPIView,
    UserPostsAPIView, FollowUserAPIView,
    UnfollowUserAPIView, UserFollowersAPIView,
    UserFollowingAPIView, UpdateLanguageAPIView,
)

urlpatterns = [
    path('auth/register/', UserGenericAPIView.as_view()),
    path('auth/verify-code/', VerifyEmailGenericAPIView.as_view()),
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
]

urlpatterns += [
    path('user/me', UserDetailAPIView.as_view()),
    path('user/me/update', UserUpdateAPIView.as_view()),
    path('user/me/delete', UserDeleteAPIView.as_view()),
    path('users', UserListAPIView.as_view()),
    path('users/suggested', SuggestedUsersAPIView.as_view()),
    path('users/<str:username>/', UserProfileByUsernameAPIView.as_view()),
    path('users/<str:username>/posts/', UserPostsAPIView.as_view()),
]

urlpatterns += [
    path('users/<str:username>/follow/', FollowUserAPIView.as_view()),
    path('users/<str:username>/unfollow/', UnfollowUserAPIView.as_view()),
    path('users/<str:username>/followers/', UserFollowersAPIView.as_view()),
    path('users/<str:username>/following/', UserFollowingAPIView.as_view()),
]

urlpatterns += [
    path('user/me/language/', UpdateLanguageAPIView.as_view()),
]
