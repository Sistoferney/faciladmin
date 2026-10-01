from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class PlanSuscripcion(models.Model):
    """Planes disponibles: Trial, Mensual"""
    TIPO_PLAN = [
        ('trial', 'Trial Gratuito'),
        ('mensual', 'Mensual'),
    ]

    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPO_PLAN)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    duracion_dias = models.IntegerField()  # 120 para trial, 30 mensual
    descripcion = models.TextField()
    activo = models.BooleanField(default=True)

    # Límites del plan (None = ilimitado)
    # NOTA: Trial tiene acceso completo (todos en None/True)
    max_citas_mes = models.IntegerField(null=True, blank=True)  # None = ilimitado
    max_servicios = models.IntegerField(null=True, blank=True)  # None = ilimitado
    max_clientes = models.IntegerField(null=True, blank=True)   # None = ilimitado
    push_notifications = models.BooleanField(default=True)
    soporte_prioritario = models.BooleanField(default=False)    # Solo Premium

    class Meta:
        verbose_name = 'Plan de Suscripción'
        verbose_name_plural = 'Planes de Suscripción'

    def __str__(self):
        return f"{self.nombre} - ${self.precio}"


class Suscripcion(models.Model):
    """Suscripción activa de un negocio"""
    ESTADO_CHOICES = [
        ('trial', 'Trial Activo'),
        ('activa', 'Activa'),
        ('vencida', 'Vencida'),
        ('cancelada', 'Cancelada'),
        ('suspendida', 'Suspendida'),
    ]

    negocio = models.OneToOneField('negocios.Negocio', on_delete=models.CASCADE, related_name='suscripcion')
    plan = models.ForeignKey(PlanSuscripcion, on_delete=models.PROTECT)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='trial')

    # Fechas
    fecha_inicio = models.DateTimeField(default=timezone.now)
    fecha_fin = models.DateTimeField()
    fecha_cancelacion = models.DateTimeField(null=True, blank=True)

    # Pagos
    metodo_pago = models.CharField(max_length=50, null=True, blank=True)  # 'wompi', 'stripe', etc.
    token_pago = models.CharField(max_length=255, null=True, blank=True)  # Token de Wompi/Stripe
    referencia_externa = models.CharField(max_length=255, null=True, blank=True)  # Subscription ID externo

    # Renovación automática
    auto_renovacion = models.BooleanField(default=False)

    # Auditoría
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Suscripción'
        verbose_name_plural = 'Suscripciones'

    def __str__(self):
        return f"{self.negocio.nombre} - {self.plan.nombre} ({self.get_estado_display()})"

    @property
    def esta_activa(self):
        """Verifica si la suscripción está activa"""
        if self.estado in ['cancelada', 'suspendida']:
            return False
        return timezone.now() <= self.fecha_fin

    @property
    def dias_restantes(self):
        """Días hasta que expire"""
        if not self.esta_activa:
            return 0
        delta = self.fecha_fin - timezone.now()
        return max(delta.days, 0)

    def puede_usar_feature(self, feature):
        """Verifica si puede usar una característica según límites del plan"""
        if not self.esta_activa:
            return False

        # Implementar lógica de límites aquí
        if feature == 'push_notifications':
            return self.plan.push_notifications

        return True


class PagoSuscripcion(models.Model):
    """Historial de pagos"""
    ESTADO_PAGO = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('reembolsado', 'Reembolsado'),
    ]

    suscripcion = models.ForeignKey(Suscripcion, on_delete=models.CASCADE, related_name='pagos')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADO_PAGO)

    # Referencia de pasarela
    pasarela = models.CharField(max_length=50)  # 'wompi', 'stripe'
    transaccion_id = models.CharField(max_length=255, unique=True)
    referencia = models.CharField(max_length=255, null=True, blank=True)

    # Metadata
    metodo_pago = models.CharField(max_length=50)  # 'pse', 'card', 'nequi'
    metadata = models.JSONField(null=True, blank=True)

    # Fechas
    fecha_pago = models.DateTimeField(default=timezone.now)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Pago de Suscripción'
        verbose_name_plural = 'Pagos de Suscripción'

    def __str__(self):
        return f"{self.suscripcion.negocio.nombre} - ${self.monto} ({self.get_estado_display()})"


class Cupon(models.Model):
    """
    Cupones de mes gratis.
    Se canjean DESPUÉS del período de trial (120 días) para extender la suscripción.
    El admin de negocio canjea el cupón ANTES de pagar y le extiende 30 días.
    """
    codigo = models.CharField(max_length=50, unique=True, db_index=True)  # Generado automáticamente

    # Siempre es 1 mes gratis (30 días)
    meses_gratis = models.IntegerField(default=1, editable=False)

    # Restricciones
    activo = models.BooleanField(default=True)
    fecha_inicio = models.DateTimeField(default=timezone.now)
    fecha_expiracion = models.DateTimeField(null=True, blank=True)

    # Un cupón puede ser de uso único o para un negocio específico
    negocio_asignado = models.ForeignKey('negocios.Negocio', on_delete=models.CASCADE, null=True, blank=True,
                                          related_name='cupones_asignados',
                                          help_text='Si se asigna, solo este negocio puede usarlo')

    # Metadata
    descripcion = models.TextField(blank=True)
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    usado = models.BooleanField(default=False)  # Si ya fue canjeado
    fecha_uso = models.DateTimeField(null=True, blank=True)  # Cuándo fue canjeado

    class Meta:
        verbose_name = 'Cupón'
        verbose_name_plural = 'Cupones'

    def __str__(self):
        if self.negocio_asignado:
            return f"{self.codigo} → {self.negocio_asignado.nombre}"
        return f"{self.codigo} (1 mes gratis)"

    @property
    def esta_valido(self):
        """Verifica si el cupón es válido"""
        if not self.activo or self.usado:
            return False

        # Verificar fechas
        ahora = timezone.now()
        if ahora < self.fecha_inicio:
            return False
        if self.fecha_expiracion and ahora > self.fecha_expiracion:
            return False

        return True

    def puede_canjear(self, negocio):
        """
        Verifica si un negocio específico puede canjear este cupón.
        Returns: (bool, mensaje)
        """
        if not self.esta_valido:
            return False, "El cupón no es válido, ha expirado o ya fue usado"

        # Si el cupón está asignado a un negocio específico
        if self.negocio_asignado and self.negocio_asignado != negocio:
            return False, "Este cupón no está asignado a tu negocio"

        return True, "Cupón válido"

    def canjear(self, negocio):
        """
        Canjea el cupón y extiende la suscripción del negocio por 30 días.
        Returns: (bool, mensaje, suscripcion)
        """
        puede, mensaje = self.puede_canjear(negocio)
        if not puede:
            return False, mensaje, None

        try:
            suscripcion = Suscripcion.objects.get(negocio=negocio)

            # Extender la suscripción 30 días
            suscripcion.fecha_fin = suscripcion.fecha_fin + timedelta(days=30)
            suscripcion.save()

            # Marcar cupón como usado
            self.usado = True
            self.fecha_uso = timezone.now()
            self.save()

            # Registrar el uso
            UsoCupon.objects.create(
                cupon=self,
                negocio=negocio,
                meses_extendidos=1
            )

            return True, "¡Cupón canjeado! Tu suscripción se extendió 30 días", suscripcion

        except Suscripcion.DoesNotExist:
            return False, "No tienes una suscripción activa", None
        except Exception as e:
            return False, f"Error al canjear cupón: {str(e)}", None


class UsoCupon(models.Model):
    """Registro de uso/canje de cupones"""
    cupon = models.ForeignKey(Cupon, on_delete=models.CASCADE, related_name='usos')
    negocio = models.ForeignKey('negocios.Negocio', on_delete=models.CASCADE)
    aplicado_en = models.DateTimeField(default=timezone.now)

    # Siempre es 1 mes (30 días)
    meses_extendidos = models.IntegerField(default=1)

    class Meta:
        unique_together = ['cupon', 'negocio']
        verbose_name = 'Uso de Cupón'
        verbose_name_plural = 'Usos de Cupones'

    def __str__(self):
        return f"{self.negocio.nombre} - {self.cupon.codigo}"


class RegistroNegocio(models.Model):
    """Datos de registro simplificado antes de crear el negocio completo"""
    ESTADO_REGISTRO = [
        ('pendiente_email', 'Pendiente Validación Email'),
        ('completado', 'Registro Completado'),
        ('expirado', 'Expirado'),
    ]

    # Datos básicos del usuario
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20)

    # Validación
    estado = models.CharField(max_length=20, choices=ESTADO_REGISTRO, default='pendiente_email')
    token_validacion = models.CharField(max_length=100, unique=True, db_index=True)
    fecha_token_expira = models.DateTimeField()
    email_validado_en = models.DateTimeField(null=True, blank=True)

    # Relación con negocio creado
    negocio_creado = models.ForeignKey('negocios.Negocio', on_delete=models.SET_NULL, null=True, blank=True)

    # Auditoría
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Registro de Negocio'
        verbose_name_plural = 'Registros de Negocios'

    def __str__(self):
        return f"{self.nombre} {self.apellido} - {self.email} ({self.get_estado_display()})"

    @property
    def token_valido(self):
        """Verifica si el token aún es válido"""
        return timezone.now() < self.fecha_token_expira


class ProgramaReferidos(models.Model):
    """
    Sistema de referidos para obtener cupones mensuales gratis.
    El admin de negocio debe referir 3 negocios activos para recibir 1 cupón cada mes.
    """
    # Negocio que refiere (el que recibirá los cupones)
    negocio = models.OneToOneField('negocios.Negocio', on_delete=models.CASCADE, related_name='programa_referidos')

    # Los 3 negocios referidos (deben estar activos)
    negocio_referido_1 = models.ForeignKey(
        'negocios.Negocio',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referido_por_slot_1',
        help_text='Primer negocio referido'
    )
    negocio_referido_2 = models.ForeignKey(
        'negocios.Negocio',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referido_por_slot_2',
        help_text='Segundo negocio referido'
    )
    negocio_referido_3 = models.ForeignKey(
        'negocios.Negocio',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referido_por_slot_3',
        help_text='Tercer negocio referido'
    )

    # Control de generación de cupones
    activo = models.BooleanField(default=False, help_text='True si tiene los 3 referidos activos')
    fecha_ultimo_cupon = models.DateTimeField(null=True, blank=True, help_text='Última vez que se generó un cupón')
    total_cupones_generados = models.IntegerField(default=0)

    # Auditoría
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Programa de Referidos'
        verbose_name_plural = 'Programas de Referidos'

    def __str__(self):
        return f"{self.negocio.nombre} - {self.referidos_activos()}/3 referidos"

    def referidos_activos(self):
        """Cuenta cuántos referidos están activos"""
        count = 0
        if self.negocio_referido_1 and self.negocio_referido_1.esta_activo:
            count += 1
        if self.negocio_referido_2 and self.negocio_referido_2.esta_activo:
            count += 1
        if self.negocio_referido_3 and self.negocio_referido_3.esta_activo:
            count += 1
        return count

    def cumple_requisitos(self):
        """Verifica si cumple con los 3 referidos activos"""
        return self.referidos_activos() == 3

    def actualizar_estado(self):
        """Actualiza el estado activo según los referidos"""
        self.activo = self.cumple_requisitos()
        self.save()
        return self.activo

    def puede_generar_cupon(self):
        """
        Verifica si puede generar un nuevo cupón mensual.
        Returns: (bool, mensaje)
        """
        if not self.cumple_requisitos():
            faltantes = 3 - self.referidos_activos()
            return False, f"Necesitas {faltantes} referido(s) activo(s) más"

        # Verificar si ya generó cupón este mes
        ahora = timezone.now()
        if self.fecha_ultimo_cupon:
            ultimo_mes = self.fecha_ultimo_cupon.month
            ultimo_año = self.fecha_ultimo_cupon.year
            if ultimo_mes == ahora.month and ultimo_año == ahora.year:
                return False, "Ya generaste tu cupón este mes"

        return True, "Puedes generar tu cupón mensual"

    def generar_cupon_mensual(self):
        """
        Genera un cupón de mes gratis si cumple requisitos.
        Returns: (bool, mensaje, cupon)
        """
        puede, mensaje = self.puede_generar_cupon()
        if not puede:
            return False, mensaje, None

        # Generar código único
        import secrets
        codigo = f"REF-{self.negocio.id}-{secrets.token_hex(4).upper()}"

        # Crear cupón
        cupon = Cupon.objects.create(
            codigo=codigo,
            descripcion=f"Cupón mensual por programa de referidos - {timezone.now().strftime('%B %Y')}",
            negocio_asignado=self.negocio,
            activo=True,
            fecha_inicio=timezone.now(),
            fecha_expiracion=timezone.now() + timedelta(days=90)  # Expira en 90 días
        )

        # Actualizar registro
        self.fecha_ultimo_cupon = timezone.now()
        self.total_cupones_generados += 1
        self.save()

        return True, f"¡Cupón {codigo} generado exitosamente!", cupon

    def slots_disponibles(self):
        """Retorna lista de slots (1, 2, 3) que están vacíos"""
        slots = []
        if not self.negocio_referido_1:
            slots.append(1)
        if not self.negocio_referido_2:
            slots.append(2)
        if not self.negocio_referido_3:
            slots.append(3)
        return slots

    def puede_agregar_referido(self, negocio_telefono):
        """
        Verifica si un teléfono puede ser agregado como referido.
        Returns: (bool, mensaje, negocio)
        """
        from apps.negocios.models import Negocio

        # Verificar que hay slots disponibles
        if not self.slots_disponibles():
            return False, "Ya tienes los 3 referidos registrados", None

        # Buscar negocio por teléfono
        try:
            negocio_referido = Negocio.objects.get(telefono=negocio_telefono)
        except Negocio.DoesNotExist:
            return False, "No existe un negocio registrado con ese teléfono", None

        # No puede referirse a sí mismo
        if negocio_referido == self.negocio:
            return False, "No puedes referirte a ti mismo", None

        # Verificar que no esté ya referido por este negocio
        if negocio_referido in [self.negocio_referido_1, self.negocio_referido_2, self.negocio_referido_3]:
            return False, "Este negocio ya está en tu lista de referidos", None

        # Verificar que no esté siendo usado por otro referidor
        if ProgramaReferidos.objects.filter(negocio_referido_1=negocio_referido).exists() or \
           ProgramaReferidos.objects.filter(negocio_referido_2=negocio_referido).exists() or \
           ProgramaReferidos.objects.filter(negocio_referido_3=negocio_referido).exists():
            return False, "Este negocio ya ha sido referido por otro usuario", None

        # Verificar que el negocio esté activo
        if not negocio_referido.esta_activo:
            return False, "Este negocio no está activo en FacilAdmin", None

        return True, "Negocio válido para referir", negocio_referido

    def agregar_referido(self, negocio_telefono):
        """
        Agrega un negocio referido al primer slot disponible.
        Returns: (bool, mensaje)
        """
        puede, mensaje, negocio = self.puede_agregar_referido(negocio_telefono)
        if not puede:
            return False, mensaje

        # Agregar al primer slot disponible
        slots = self.slots_disponibles()
        if 1 in slots:
            self.negocio_referido_1 = negocio
        elif 2 in slots:
            self.negocio_referido_2 = negocio
        elif 3 in slots:
            self.negocio_referido_3 = negocio

        self.save()
        self.actualizar_estado()

        return True, f"Negocio {negocio.nombre} agregado como referido"
