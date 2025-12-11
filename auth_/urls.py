from django.urls import path

from auth_.views import CustomTokenObtainPairView, CustomTokenRefreshView, UserGenericAPIView, VerifyEmailGenericAPIView

urlpatterns = [
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('register/', UserGenericAPIView.as_view())
]

urlpatterns += [
    path('verify-code/', VerifyEmailGenericAPIView.as_view()),
]
