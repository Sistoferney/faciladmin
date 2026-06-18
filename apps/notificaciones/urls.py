"""
URLs para API de notificaciones
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import push_views

app_name = 'notificaciones'

router = DefaultRouter()
# router.register(r'', views.NotificacionViewSet, basename='notificacion')

urlpatterns = [
    path('', include(router.urls)),

    # Push Notifications (PWA)
    path('push/vapid-key/', push_views.get_vapid_public_key, name='push_vapid_key'),
    path('push/subscribe/', push_views.subscribe_push, name='push_subscribe'),
    path('push/unsubscribe/', push_views.unsubscribe_push, name='push_unsubscribe'),
    path('push/test/', push_views.test_push_notification, name='push_test'),

    # django-webpush URLs
    path('webpush/', include('webpush.urls')),
]
