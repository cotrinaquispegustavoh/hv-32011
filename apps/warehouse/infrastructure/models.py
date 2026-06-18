from django.db import models
from django.conf import settings

class Material(models.Model):
    name = models.CharField('Nombre', max_length=200)
    stock = models.PositiveIntegerField('Stock Actual', default=0)
    unit = models.CharField('Unidad de medida', max_length=50) # ej: Unidades, Cajas, Kits
    state = models.CharField('Estado físico', max_length=50) # ej: Nuevo, Bueno, Regular
    location = models.CharField('Ubicación en almacén', max_length=100)
    cycle = models.CharField('Ciclo', max_length=50) # ej: Ciclo I, Ciclo II
    pedagogical_use = models.TextField('Uso pedagógico', blank=True, null=True)
    manual = models.FileField('Manual opcional', upload_to='manuals/', blank=True, null=True)

    class Meta:
        app_label = 'warehouse'
        verbose_name = 'Material'
        verbose_name_plural = 'Materiales'

    def __str__(self):
        return self.name

class MaterialImage(models.Model):
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField('Imagen', upload_to='materials/')
    is_main = models.BooleanField('Es imagen principal', default=False)

    class Meta:
        app_label = 'warehouse'

class LoanRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('DISPATCHED', 'Despachado'),
        ('RETURNED', 'Devuelto'),
        ('CANCELLED', 'Cancelado'),
    ]
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='loan_requests')
    request_date = models.DateTimeField('Fecha de solicitud', auto_now_add=True)
    required_for = models.DateTimeField('Requerido para', null=True, blank=True)
    expected_return_date = models.DateTimeField('Devolución esperada', null=True, blank=True)
    status = models.CharField('Estado', max_length=20, choices=STATUS_CHOICES, default='PENDING')
    notes = models.TextField('Observaciones', blank=True, null=True)

    class Meta:
        app_label = 'warehouse'
        verbose_name = 'Solicitud de Préstamo'
        verbose_name_plural = 'Solicitudes de Préstamo'

class LoanDetail(models.Model):
    loan_request = models.ForeignKey(LoanRequest, on_delete=models.CASCADE, related_name='details')
    material = models.ForeignKey(Material, on_delete=models.PROTECT)
    quantity_requested = models.PositiveIntegerField('Cantidad solicitada')
    quantity_returned = models.PositiveIntegerField('Cantidad devuelta', default=0)
    quantity_waste = models.PositiveIntegerField('Merma / Dañados', default=0)

    class Meta:
        app_label = 'warehouse'