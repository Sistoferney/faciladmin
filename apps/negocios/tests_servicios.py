"""
Tope de servicios activos por negocio y eliminación de servicios con citas
"""
from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.authentication.models import Usuario
from apps.citas.models import Cita
from apps.clientes.models import Cliente
from apps.servicios.models import MAX_SERVICIOS_ACTIVOS, Servicio

from .models import Negocio


class TopeServiciosTests(TestCase):

    def setUp(self):
        dueno = Usuario.objects.create_user(telefono='3000000000', password='x', nombre='Dueña', email='d@d.com')
        self.negocio = Negocio.objects.create(administrador=dueno, nombre='Spa Tope', telefono='3000000000')
        self.client.force_login(dueno)
        self.slug = self.negocio.slug
        self.url_crear = reverse('public:servicio_crear', args=[self.slug])

    def _llenar(self, cantidad):
        return [
            Servicio.objects.create(negocio=self.negocio, nombre=f'Servicio {i}', precio=10000, duracion_minutos=30)
            for i in range(cantidad)
        ]

    def _datos(self, nombre='Nuevo', activo=True):
        datos = {'nombre': nombre, 'precio': '20000', 'duracion_minutos': '45', 'orden': '0'}
        if activo:
            datos['esta_activo'] = 'on'
        return datos

    def test_crea_hasta_el_tope(self):
        self._llenar(MAX_SERVICIOS_ACTIVOS - 1)
        self.client.post(self.url_crear, self._datos())
        self.assertEqual(Servicio.objects.filter(negocio=self.negocio, esta_activo=True).count(), MAX_SERVICIOS_ACTIVOS)

    def test_en_el_tope_no_deja_crear(self):
        self._llenar(MAX_SERVICIOS_ACTIVOS)
        resp = self.client.get(self.url_crear, follow=True)
        self.assertContains(resp, 'el máximo')
        self.client.post(self.url_crear, self._datos())
        self.assertFalse(Servicio.objects.filter(nombre='Nuevo').exists())

    def test_lista_muestra_conteo_y_oculta_boton_en_el_tope(self):
        self._llenar(MAX_SERVICIOS_ACTIVOS)
        resp = self.client.get(reverse('public:admin_servicios', args=[self.slug]))
        self.assertContains(resp, f'{MAX_SERVICIOS_ACTIVOS} de {MAX_SERVICIOS_ACTIVOS} servicios activos')
        self.assertNotContains(resp, self.url_crear)

    def test_desactivados_no_cuentan(self):
        servicios = self._llenar(MAX_SERVICIOS_ACTIVOS)
        servicios[0].esta_activo = False
        servicios[0].save()
        self.client.post(self.url_crear, self._datos())
        self.assertTrue(Servicio.objects.filter(nombre='Nuevo', esta_activo=True).exists())

    def test_no_reactiva_uno_desactivado_si_esta_en_el_tope(self):
        servicios = self._llenar(MAX_SERVICIOS_ACTIVOS)
        inactivo = Servicio.objects.create(
            negocio=self.negocio, nombre='Inactivo', precio=1, duracion_minutos=30, esta_activo=False,
        )
        resp = self.client.post(
            reverse('public:servicio_editar', args=[self.slug, inactivo.id]), self._datos('Inactivo'),
        )
        self.assertContains(resp, 'Desactiva o elimina uno')
        inactivo.refresh_from_db()
        self.assertFalse(inactivo.esta_activo)

        # Editar uno que ya estaba activo sí se permite estando en el tope
        self.client.post(
            reverse('public:servicio_editar', args=[self.slug, servicios[0].id]), self._datos('Renombrado'),
        )
        servicios[0].refresh_from_db()
        self.assertEqual(servicios[0].nombre, 'Renombrado')

    def test_imagen_de_mas_de_5_mb(self):
        from django.forms import ImageField
        from unittest.mock import patch
        grande = SimpleUploadedFile('foto.png', b'x' * (5 * 1024 * 1024 + 1), content_type='image/png')
        # Saltar la validación de Pillow: solo se prueba el tamaño
        with patch.object(ImageField, 'to_python', lambda campo, dato: dato):
            resp = self.client.post(self.url_crear, {**self._datos(), 'imagen': grande})
        self.assertContains(resp, 'no debe superar 5 MB')
        self.assertFalse(Servicio.objects.filter(nombre='Nuevo').exists())

    def test_eliminar_servicio_con_citas_lo_desactiva(self):
        servicio, = self._llenar(1)
        cliente = Cliente.objects.create(negocio=self.negocio, nombre='Ana', telefono='3001111111')
        Cita.objects.create(
            negocio=self.negocio, cliente=cliente, servicio=servicio,
            fecha_hora=timezone.now() - timedelta(days=3), duracion_minutos=30, estado='completada',
        )
        resp = self.client.post(reverse('public:servicio_eliminar', args=[self.slug, servicio.id]), follow=True)
        self.assertContains(resp, 'desactivado')
        servicio.refresh_from_db()
        self.assertFalse(servicio.esta_activo)

    def test_eliminar_servicio_sin_citas_lo_borra(self):
        servicio, = self._llenar(1)
        self.client.post(reverse('public:servicio_eliminar', args=[self.slug, servicio.id]))
        self.assertFalse(Servicio.objects.filter(id=servicio.id).exists())
