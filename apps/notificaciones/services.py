"""
Servicios para envío de notificaciones
RF-33: WhatsApp, SMS, Email, Push
"""
from django.conf import settings
from django.core.mail import send_mail
from twilio.rest import Client
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
            from .models import ClientePushSubscription
            from pywebpush import webpush, WebPushException

            # Buscar suscripciones activas del cliente específico
            suscripciones = ClientePushSubscription.objects.filter(
                cliente=cliente,
                activa=True
            )

            if not suscripciones.exists():
                return {'success': False, 'error': 'El cliente no tiene suscripciones activas'}

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

            # Enviar a todas las suscripciones activas del cliente
            enviados = 0
            suscripciones_fallidas = []

            for suscripcion in suscripciones:
                try:
                    # Convertir a formato de subscription_info
                    subscription_info = suscripcion.to_subscription_info()

                    # Enviar notificación usando pywebpush
                    webpush(
                        subscription_info=subscription_info,
                        data=json.dumps(payload),
                        vapid_private_key=settings.WEBPUSH_SETTINGS.get('VAPID_PRIVATE_KEY'),
                        vapid_claims={
                            'sub': f"mailto:{settings.WEBPUSH_SETTINGS.get('VAPID_ADMIN_EMAIL', 'admin@faciladmin.com')}"
                        }
                    )
                    enviados += 1

                except WebPushException as e:
                    logger.error(f"Error enviando push a suscripción {suscripcion.id}: {str(e)}")
                    # Si la suscripción expiró o es inválida, marcarla como inactiva
                    if e.response and e.response.status_code in [404, 410]:
                        suscripcion.desactivar()
                        logger.info(f"Suscripción {suscripcion.id} marcada como inactiva (endpoint inválido)")
                    suscripciones_fallidas.append(suscripcion.id)
                    continue
                except Exception as e:
                    logger.error(f"Error inesperado enviando push a suscripción {suscripcion.id}: {str(e)}")
                    suscripciones_fallidas.append(suscripcion.id)
                    continue

            if enviados > 0:
                result = {'success': True, 'enviados': enviados}
                if suscripciones_fallidas:
                    result['fallidas'] = suscripciones_fallidas
                return result
            else:
                return {
                    'success': False,
                    'error': 'No se pudo enviar a ninguna suscripción',
                    'fallidas': suscripciones_fallidas
                }

        except Exception as e:
            logger.error(f"Error enviando push notification: {str(e)}")
            return {'success': False, 'error': str(e)}
