"""
Backend de email personalizado para Resend
Usa HTTPS (puerto 443) en lugar de SMTP - funciona en Railway sin plan Pro
"""
import logging
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings
import resend

logger = logging.getLogger(__name__)


class ResendEmailBackend(BaseEmailBackend):
    """
    Backend de email que usa Resend API en lugar de SMTP

    Variables de entorno requeridas:
    - RESEND_API_KEY: Tu API key de Resend
    - DEFAULT_FROM_EMAIL: Email verificado en Resend (ej: noreply@tudominio.com)
    """

    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = getattr(settings, 'RESEND_API_KEY', None)

        if not self.api_key:
            if not self.fail_silently:
                raise ValueError(
                    "RESEND_API_KEY no está configurada. "
                    "Agrega RESEND_API_KEY en tus variables de entorno."
                )
            logger.error("RESEND_API_KEY no está configurada")
        else:
            resend.api_key = self.api_key

    def send_messages(self, email_messages):
        """
        Envía una lista de mensajes de email usando Resend API
        Retorna el número de mensajes enviados exitosamente
        """
        if not email_messages:
            return 0

        if not self.api_key:
            if not self.fail_silently:
                raise ValueError("RESEND_API_KEY no está configurada")
            return 0

        num_sent = 0
        for message in email_messages:
            try:
                sent = self._send(message)
                if sent:
                    num_sent += 1
            except Exception as e:
                logger.error(f"Error enviando email con Resend: {e}")
                if not self.fail_silently:
                    raise

        return num_sent

    def _send(self, message):
        """
        Envía un mensaje individual usando Resend API
        """
        if not message.recipients():
            return False

        # Convertir mensaje de Django a formato de Resend
        params = {
            "from": message.from_email or settings.DEFAULT_FROM_EMAIL,
            "to": message.to,
            "subject": message.subject,
        }

        # Agregar CC si existe
        if message.cc:
            params["cc"] = message.cc

        # Agregar BCC si existe
        if message.bcc:
            params["bcc"] = message.bcc

        # Agregar Reply-To si existe
        if message.reply_to:
            params["reply_to"] = message.reply_to

        # Manejar contenido HTML vs texto plano
        if message.content_subtype == 'html':
            params["html"] = message.body
        else:
            params["text"] = message.body

        # Si hay alternativas (ej: texto + HTML), usar ambas
        if hasattr(message, 'alternatives') and message.alternatives:
            for alternative_content, mimetype in message.alternatives:
                if mimetype == 'text/html':
                    params["html"] = alternative_content

        # Enviar usando Resend API
        try:
            response = resend.Emails.send(params)
            logger.info(f"Email enviado exitosamente vía Resend. ID: {response.get('id')}")
            return True
        except Exception as e:
            logger.error(f"Error al enviar email con Resend: {e}")
            if not self.fail_silently:
                raise
            return False
