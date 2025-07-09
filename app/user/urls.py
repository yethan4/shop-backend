from django.urls import path

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from . import views

app_name = "user"

urlpatterns = [
    path('register/', views.UserRegistrationAPIView.as_view(),
         name='register-user'),
    path('token/', TokenObtainPairView.as_view(),
         name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(),
         name='token_refresh'),
    path('current/', views.CurrentUserAPIView.as_view(),
         name='current-user'),
    path('current/detail/', views.CurrentUserDetailAPIView.as_view(),
         name='current-user-detail'),
]
