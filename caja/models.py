from django.db import models
from django.core.exceptions import ValidationError
from decimal import Decimal

class SaldoGeneral(models.Model):
    monto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Saldo General: ${self.monto}"

class CajaDiaria(models.Model):
    TURNOS = [
        ('M', 'Mañana'),
        ('T', 'Tarde')
    ]
    NIVELES = [
        ('P', 'Primario'),
        ('S', 'Secundario')
    ]

    fecha = models.DateField()
    turno = models.CharField(max_length=1, choices=TURNOS)
    nivel = models.CharField(max_length=1, choices=NIVELES)
    saldo_inicial = models.DecimalField(max_digits=10, decimal_places=2)
    saldo_parcial = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cerrada = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['fecha', 'turno', 'nivel']
        ordering = ['-fecha', 'turno']

    def clean(self):
        # Validar que no exista otro nivel para el mismo turno y fecha
        if CajaDiaria.objects.filter(
            fecha=self.fecha,
            turno=self.turno,
            nivel=self.nivel
        ).exclude(id=self.id).exists():
            raise ValidationError('Ya existe una caja para esta fecha, turno y nivel')

    def __str__(self):
        return f"{self.fecha} - {self.get_turno_display()} - {self.get_nivel_display()}"

class Recreo(models.Model):
    caja = models.ForeignKey(CajaDiaria, on_delete=models.CASCADE)
    numero = models.IntegerField()
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['caja', 'numero']
        ordering = ['numero']

class EventoEspecial(models.Model):
    caja = models.ForeignKey(CajaDiaria, on_delete=models.CASCADE)
    descripcion = models.CharField(max_length=255, blank=True, default='')  # Agregamos blank y default
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.descripcion} - ${self.monto}"

class PagoProveedor(models.Model):
    caja = models.ForeignKey(CajaDiaria, on_delete=models.CASCADE)
    proveedor = models.ForeignKey('precios.Proveedor', on_delete=models.PROTECT)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    comprobante = models.CharField(max_length=50)
    observacion = models.TextField(blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
