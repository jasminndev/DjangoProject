from django.urls import path

from auth_.views import CustomTokenObtainPairView, CustomTokenRefreshView, UserGenericAPIView, \
    VerifyEmailGenericAPIView, UserUpdateAPIView, UserDetailAPIView, UserDeleteAPIView

urlpatterns = [
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('register/', UserGenericAPIView.as_view()),
    path('verify-code/', VerifyEmailGenericAPIView.as_view()),
]

urlpatterns += [
    path('user-update', UserUpdateAPIView.as_view()),
    path('user-detail', UserDetailAPIView.as_view()),
    path('user-delete', UserDeleteAPIView.as_view()),
]
