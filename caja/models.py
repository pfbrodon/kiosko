from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Sum
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
    saldo_inicial = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    saldo_parcial = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cerrada = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    es_extra = models.BooleanField(default=False)

    class Meta:
        unique_together = ['fecha', 'turno', 'nivel', 'es_extra']
        ordering = ['-fecha', 'turno']

    def clean(self):
        # Si estamos creando una nueva caja (sin ID aún)
        if not self.id:
            # Validar que no exista otra caja para el mismo turno, fecha, nivel y tipo (normal/extra)
            queryset = CajaDiaria.objects.filter(
                fecha=self.fecha,
                turno=self.turno,
                nivel=self.nivel
            )
            
            # Si es una caja extra
            if self.es_extra:
                # Verificar que la fecha sea la actual
                import datetime
                today = datetime.date.today()
                if self.fecha != today:
                    raise ValidationError(f'Las cajas extras solo pueden crearse para el día actual ({today.strftime("%d/%m/%Y")})')
                
                # Verificar que exista una caja normal cerrada
                caja_normal = queryset.filter(es_extra=False).first()
                if not caja_normal:
                    raise ValidationError('No existe una caja normal para esta fecha, turno y nivel')
                if not caja_normal.cerrada:
                    raise ValidationError('La caja normal para esta fecha, turno y nivel no está cerrada')
                
                # Verificar que no exista ya una caja extra
                if queryset.filter(es_extra=True).exists():
                    raise ValidationError('Ya existe una caja extra para esta fecha, turno y nivel')
            else:
                # Si no es una caja extra, no debe existir ninguna otra caja normal
                if queryset.filter(es_extra=False).exists():
                    raise ValidationError('Ya existe una caja para esta fecha, turno y nivel')
        else:
            # Si estamos editando una caja existente
            queryset = CajaDiaria.objects.filter(
                fecha=self.fecha,
                turno=self.turno,
                nivel=self.nivel
            ).exclude(id=self.id)
            
            # Si es una caja extra, verificar que no exista otra caja extra
            if self.es_extra and queryset.filter(es_extra=True).exists():
                raise ValidationError('Ya existe una caja extra para esta fecha, turno y nivel')
            # Si es una caja normal, verificar que no exista otra caja normal
            elif not self.es_extra and queryset.filter(es_extra=False).exists():
                raise ValidationError('Ya existe una caja normal para esta fecha, turno y nivel')

    def __str__(self):
        return f"{self.fecha} - {self.get_turno_display()} - {self.get_nivel_display()}"

    def calcular_saldo_parcial(self):
        # Suma todos los ingresos de recreos
        ingresos_recreos = self.recreo_set.aggregate(
            total=Sum('monto'))['total'] or Decimal('0')
        
        # Suma todos los ingresos de eventos especiales (solo para cajas normales)
        ingresos_eventos = Decimal('0')
        if not self.es_extra:
            ingresos_eventos = self.eventoespecial_set.aggregate(
                total=Sum('monto'))['total'] or Decimal('0')
        
        # Suma todos los egresos por pagos
        egresos_pagos = self.pagoproveedor_set.aggregate(
            total=Sum('monto'))['total'] or Decimal('0')
        
        # Calcula el saldo parcial
        return self.saldo_inicial + ingresos_recreos + ingresos_eventos - egresos_pagos

    def actualizar_saldo_parcial(self):
        self.saldo_parcial = self.calcular_saldo_parcial()
        self.save()

    def get_saldo_inicial_display(self):
        """Retorna el saldo inicial solo si es caja secundaria, sino retorna 0"""
        return self.saldo_inicial if self.nivel == 'S' else Decimal('0')

    def get_total_ingresos(self):
        """Retorna el total de ingresos (recreos + eventos especiales para cajas normales)"""
        from django.db.models import Sum
        
        total_recreos = self.recreo_set.aggregate(
            total=Sum('monto')
        )['total'] or Decimal('0')
        
        total_eventos = Decimal('0')
        if not self.es_extra:
            total_eventos = self.eventoespecial_set.aggregate(
                total=Sum('monto')
            )['total'] or Decimal('0')
        
        return total_recreos + total_eventos

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
