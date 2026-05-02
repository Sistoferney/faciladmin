"""
Servicios para envío de notificaciones
RF-33: WhatsApp, SMS, Email
"""
from django.conf import settings
from django.core.mail import send_mail
from twilio.rest import Client
import logging

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
