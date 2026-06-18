"""
Servicios para envío de notificaciones
RF-33: WhatsApp, SMS, Email, Push
"""
from django.conf import settings
from django.core.mail import send_mail
from twilio.rest import Client
from webpush import send_user_notification
import logging
import json

logger = logging.getLogger(__name__)


class NotificacionService:
    """Servicio para enviar notificaciones por diferentes canales"""

    def __init__(self):
        # Inicializar cliente de Twilio
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            self.twilio_client = Client(
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN
            )
        else:
            self.twilio_client = None
            logger.warning("Credenciales de Twilio no configuradas")

    def enviar_whatsapp(self, numero_destino, mensaje):
        """
        RF-33: Enviar mensaje por WhatsApp usando Twilio
        """
        if not self.twilio_client:
            return {'success': False, 'error': 'Twilio no configurado'}

        try:
            message = self.twilio_client.messages.create(
                from_=settings.TWILIO_WHATSAPP_NUMBER,
                to=f'whatsapp:{numero_destino}',
                body=mensaje
            )
            return {'success': True, 'id': message.sid}
        except Exception as e:
            logger.error(f"Error enviando WhatsApp: {str(e)}")
            return {'success': False, 'error': str(e)}

    def enviar_sms(self, numero_destino, mensaje):
        """
        RF-33: Enviar SMS usando Twilio
        """
        if not self.twilio_client:
            return {'success': False, 'error': 'Twilio no configurado'}

        try:
            message = self.twilio_client.messages.create(
                from_=settings.TWILIO_PHONE_NUMBER,
                to=numero_destino,
                body=mensaje
            )
            return {'success': True, 'id': message.sid}
        except Exception as e:
            logger.error(f"Error enviando SMS: {str(e)}")
            return {'success': False, 'error': str(e)}

    def enviar_email(self, email_destino, asunto, mensaje):
        """
        RF-33: Enviar email
        """
        try:
            send_mail(
                subject=asunto,
                message=mensaje,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email_destino],
                fail_silently=False,
            )
            return {'success': True}
        except Exception as e:
            logger.error(f"Error enviando email: {str(e)}")
            return {'success': False, 'error': str(e)}

    def enviar_push(self, cliente, titulo, mensaje, cita=None):
        """
        Enviar notificación push (PWA)
        Gratis, no requiere Twilio
        """
        try:
            # Obtener usuario asociado al cliente (si existe)
            # Por ahora, enviamos a todas las suscripciones almacenadas
            from webpush.models import SubscriptionInfo

            # Buscar suscripciones del cliente por user_agent o datos guardados
            # TODO: Asociar SubscriptionInfo con modelo Cliente
            # Por ahora enviamos a todas las suscripciones activas

            # Preparar payload de la notificación
            payload = {
                'head': titulo,
                'body': mensaje,
                'icon': '/static/images/faciladmin-logo.png',
                'url': '/',
                'tag': f'notificacion-{cliente.id}',
                'requireInteraction': True,
                'vibrate': [200, 100, 200]
            }

            if cita:
                # Agregar URL específica para la cita
                payload['url'] = f'/{cita.negocio.slug}/'
                payload['data'] = {
                    'citaId': cita.id,
                    'tipo': 'recordatorio_cita'
                }

            # Intentar enviar a todas las suscripciones
            # TODO: Filtrar por cliente específico cuando tengamos la asociación
            suscripciones = SubscriptionInfo.objects.all()

            if not suscripciones.exists():
                return {'success': False, 'error': 'No hay suscripciones activas'}

            enviados = 0
            for suscripcion in suscripciones:
                try:
                    send_user_notification(
                        user=suscripcion.user if hasattr(suscripcion, 'user') and suscripcion.user else None,
                        payload=payload,
                        ttl=1000
                    )
                    enviados += 1
                except Exception as e:
                    logger.error(f"Error enviando push a suscripción {suscripcion.id}: {str(e)}")
                    continue

            if enviados > 0:
                return {'success': True, 'enviados': enviados}
            else:
                return {'success': False, 'error': 'No se pudo enviar a ninguna suscripción'}

        except Exception as e:
            logger.error(f"Error enviando push notification: {str(e)}")
            return {'success': False, 'error': str(e)}
