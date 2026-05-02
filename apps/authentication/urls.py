"""
URLs para autenticación
"""
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

app_name = 'authentication'

urlpatterns = [
    # JWT Authentication
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Implementar vistas personalizadas en el futuro:
    # path('register/', views.RegisterView.as_view(), name='register'),
    # path('password-reset/', views.PasswordResetView.as_view(), name='password_reset'),
]
