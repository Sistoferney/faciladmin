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

# Entrega de los push:
# - ttl: Google guarda el mensaje hasta 24 h si el celular está en reposo o sin
#   conexión. Con el valor por defecto de pywebpush (0) lo descartaba si no
#   podía entregarlo en ese instante.
# - Urgency high: Android lo entrega aunque esté ahorrando batería (Doze).
OPCIONES_ENTREGA_PUSH = {
    'ttl': 24 * 60 * 60,
    'headers': {'Urgency': 'high'},
}


def elegir_canal(cliente):
    """
    Canal por el que se notificará al cliente, o None si no hay ninguno disponible.

    Prioridad: Push (gratis) > WhatsApp > SMS > Email.
    WhatsApp y SMS solo se eligen si Twilio está configurado: los clientes
    aceptan WhatsApp por defecto, y sin Twilio el envío fallaría siempre.
    """
    from .models import ClientePushSubscription

    # Cliente dado de baja por el dueño: no recibe ningún mensaje automático
    if not cliente.esta_activo:
        return None

    twilio = bool(settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN)

    if ClientePushSubscription.objects.filter(cliente=cliente, activa=True).exists():
        return 'push'
    if cliente.acepta_whatsapp and twilio and settings.TWILIO_WHATSAPP_NUMBER:
        return 'whatsapp'
    if cliente.acepta_sms and twilio and settings.TWILIO_PHONE_NUMBER:
        return 'sms'
    if cliente.acepta_email and cliente.email:
        return 'email'
    return None


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

    def enviar_push(self, cliente, titulo, mensaje, cita=None, enviar_a_admin=False, url=None):
        """
        Enviar notificación push (PWA)
        Gratis, no requiere Twilio

        Args:
            cliente: Cliente que recibirá la notificación
            titulo: Título de la notificación
            mensaje: Cuerpo de la notificación
            cita: Cita relacionada (opcional)
            enviar_a_admin: Si True, también envía al dueño del negocio
            url: Página a abrir al tocar la notificación (por defecto agenda o Mis citas)
        """
        try:
            from .models import ClientePushSubscription, UsuarioPushSubscription
            from pywebpush import webpush, WebPushException

            # IMPORTANTE: enviar_a_admin es EXCLUYENTE, no aditivo
            # Si enviar_a_admin=True, SOLO envía al admin (NO al cliente)
            # Si enviar_a_admin=False, SOLO envía al cliente (NO al admin)

            if enviar_a_admin and cita:
                # Solo enviar al admin del negocio
                total_suscripciones = UsuarioPushSubscription.objects.filter(
                    negocio=cita.negocio,
                    activa=True
                )
            else:
                # Solo enviar al cliente
                total_suscripciones = ClientePushSubscription.objects.filter(
                    cliente=cliente,
                    activa=True
                )

            if not total_suscripciones:
                return {'success': False, 'error': 'No hay suscripciones activas'}

            # Preparar payload de la notificación
            payload = {
                'head': titulo,
                'body': mensaje,
                'icon': '/static/images/faciladmin-logo.png',
                'url': '/',
                'requireInteraction': True,
                'vibrate': [200, 100, 200]
            }

            if cita:
                # Las notificaciones de una misma cita (nueva, editada, cancelada)
                # se reemplazan entre sí; las de citas distintas se acumulan.
                # Sin cita no hay tag: cada notificación se muestra por separado.
                payload['tag'] = f'cita-{cita.id}'
                # Al tocar la notificación: el dueño va a su agenda y el cliente
                # a sus citas (cada uno dentro de su app instalada)
                if url:
                    payload['url'] = url
                elif enviar_a_admin:
                    # La bandeja de pendientes reúne lo que el dueño debe hacer
                    payload['url'] = f'/{cita.negocio.slug}/admin/pendientes/'
                else:
                    payload['url'] = f'/{cita.negocio.slug}/mis-citas/'

                # Botón "WhatsApp" en la notificación para resolver dudas:
                # el dueño escribe al cliente y el cliente escribe al negocio.
                # (iPhone no muestra botones en notificaciones: allí están en la app)
                from apps.core.whatsapp import enlace_cliente_a_negocio, enlace_negocio_a_cliente
                enlace = enlace_negocio_a_cliente(cita) if enviar_a_admin else enlace_cliente_a_negocio(cita)
                if enlace:
                    payload['whatsapp'] = enlace
                    payload['actions'] = [{
                        'action': 'whatsapp',
                        'title': '💬 WhatsApp al cliente' if enviar_a_admin else '💬 Escribir por WhatsApp',
                    }]
                payload['data'] = {
                    'citaId': cita.id,
                    'tipo': 'recordatorio_cita'
                }

            if url and not cita:
                payload['url'] = url

            # Enviar a las suscripciones activas (cliente O admin, nunca ambos)
            enviados = 0
            enviados_cliente = 0
            enviados_admin = 0
            suscripciones_fallidas = []

            for suscripcion in total_suscripciones:
                try:
                    # Convertir a formato de subscription_info
                    subscription_info = suscripcion.to_subscription_info()

                    # Crear objeto Vapid desde la key PEM
                    # IMPORTANTE: No usar vapid_private_key como string porque
                    # Vapid.from_string() NO soporta formato PEM, solo RAW y DER
                    from py_vapid import Vapid
                    vapid = Vapid.from_pem(
                        settings.WEBPUSH_SETTINGS.get('VAPID_PRIVATE_KEY').encode('utf-8')
                    )

                    # Enviar notificación usando pywebpush
                    webpush(
                        subscription_info=subscription_info,
                        data=json.dumps(payload),
                        vapid_private_key=vapid,
                        vapid_claims={
                            'sub': f"mailto:{settings.WEBPUSH_SETTINGS.get('VAPID_ADMIN_EMAIL', 'admin@faciladmin.app')}"
                        },
                        **OPCIONES_ENTREGA_PUSH,
                    )
                    enviados += 1

                    # Trackear si fue a cliente o admin
                    if isinstance(suscripcion, ClientePushSubscription):
                        enviados_cliente += 1
                    elif isinstance(suscripcion, UsuarioPushSubscription):
                        enviados_admin += 1

                except WebPushException as e:
                    logger.error(f"Error enviando push a suscripción {suscripcion.id}: {str(e)}")
                    # Si la suscripción expiró o es inválida, marcarla como inactiva
                    # IMPORTANTE: Verificar que e.response no sea None antes de acceder a status_code
                    respuesta = getattr(e, 'response', None)
                    if respuesta is not None and respuesta.status_code in [404, 410]:
                        suscripcion.desactivar()
                        logger.info(f"Suscripción {suscripcion.id} marcada como inactiva (endpoint inválido)")
                    elif respuesta is not None and respuesta.status_code == 403 and 'VAPID' in (respuesta.text or ''):
                        # Creada con otra clave VAPID (el servidor cambió sus claves):
                        # nunca va a funcionar. El navegador la renueva sola al abrir la app.
                        suscripcion.desactivar()
                        logger.info(f"Suscripción {suscripcion.id} marcada como inactiva (clave VAPID distinta)")
                    suscripciones_fallidas.append(suscripcion.id)
                    continue
                except Exception as e:
                    logger.error(f"Error inesperado enviando push a suscripción {suscripcion.id}: {str(e)}")
                    suscripciones_fallidas.append(suscripcion.id)
                    continue

            if enviados > 0:
                result = {
                    'success': True,
                    'enviados': enviados,
                    'enviados_cliente': enviados_cliente,
                    'enviados_admin': enviados_admin
                }
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
