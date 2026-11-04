"""
URL configuration for facilacces project.
"""
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.core import views as core_views, seo
from apps.authentication.forms import FormularioAccesoAdmin
from apps.authentication.views import (
    RateLimitedLoginView,
    SolicitarRecuperacionView,
    RestablecerPasswordView
)

urlpatterns = [
    # Service Worker (debe ir primero para tener scope en toda la app)
    path('sw.js', core_views.service_worker, name='service_worker'),

    # Buscadores: qué se puede indexar y lista de páginas públicas
    path('robots.txt', seo.robots_txt, name='robots_txt'),
    path('sitemap.xml', seo.sitemap_xml, name='sitemap_xml'),

    # Landing page y páginas principales
    path('', include('apps.core.urls')),

    # Autenticación (con protección contra fuerza bruta)
    path('login/', RateLimitedLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('recuperar-password/', SolicitarRecuperacionView.as_view(), name='solicitar_recuperacion'),
    path('recuperar-password/<uuid:token>/', RestablecerPasswordView.as_view(), name='restablecer_password'),

    # Panel de administración
    path('admin/', admin.site.urls),

    # Onboarding (vistas HTML)
    path('negocios/', include(('apps.negocios.urls_onboarding', 'negocios'))),

    # API endpoints
    path('api/auth/', include('apps.authentication.urls')),
    path('api/negocios/', include('apps.negocios.urls')),
    path('api/servicios/', include('apps.servicios.urls')),
    path('api/clientes/', include('apps.clientes.urls')),
    path('api/citas/', include('apps.citas.urls')),
    path('api/abonos/', include('apps.abonos.urls')),
    path('api/notificaciones/', include('apps.notificaciones.urls')),
    path('api/fidelizacion/', include('apps.fidelizacion.urls')),
    path('api/promociones/', include('apps.promociones.urls')),
    path('api/reportes/', include('apps.reportes.urls')),

    # Suscripciones (registro público)
    path('', include('apps.suscripciones.urls')),

    # Mini páginas públicas de cada negocio (debe ir al final)
    path('', include('apps.negocios.public_urls')),
]

# Configuración para servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Personalización del admin
admin.site.login_form = FormularioAccesoAdmin
admin.site.site_header = "facilacces - Administración"
admin.site.site_title = "facilacces"
admin.site.index_title = "Panel de Administración"
