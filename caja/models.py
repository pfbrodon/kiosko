from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Sum
from decimal import Decimal
from django.contrib.auth.models import User
from django.utils import timezone

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
        # Asegurar que no puede haber dos cajas abiertas del mismo nivel y turno
        constraints = [
            models.UniqueConstraint(
                fields=['nivel', 'turno'],
                condition=models.Q(cerrada=False),
                name='unique_open_caja_nivel_turno'
            )
        ]

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
        
        # Validar que no exista otra caja abierta del mismo nivel y turno
        if not self.cerrada:
            caja_abierta = CajaDiaria.objects.filter(
                nivel=self.nivel,
                turno=self.turno,
                cerrada=False
            ).exclude(pk=self.pk).exists()
            
            if caja_abierta:
                raise ValidationError('Ya existe una caja abierta para este nivel y turno')

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
        
    def get_total_egresos(self):
        """Retorna el total de egresos por pagos a proveedores"""
        from django.db.models import Sum
        
        return self.pagoproveedor_set.aggregate(
            total=Sum('monto')
        )['total'] or Decimal('0')

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

class BilleteraElectronica(models.Model):
    fecha_apertura = models.DateField(default=timezone.now)
    saldo_inicial = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    saldo_actual = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cerrada = models.BooleanField(default=False)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    usuario_apertura = models.ForeignKey(User, on_delete=models.CASCADE, related_name='billeteras_abiertas')
    usuario_cierre = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='billeteras_cerradas')
    
    class Meta:
        ordering = ['-fecha_apertura']
    
    def __str__(self):
        return f"Billetera {self.fecha_apertura} - {'Cerrada' if self.cerrada else 'Abierta'}"
    
    def save(self, *args, **kwargs):
        if not self.pk:  # Si es una nueva instancia
            self.saldo_actual = self.saldo_inicial
        super().save(*args, **kwargs)

class MovimientoBilletera(models.Model):
    TIPO_MOVIMIENTO = [
        ('ingreso', 'Ingreso'),
        ('egreso', 'Egreso'),
    ]
    
    TIPO_OPERACION = [
        ('transferencia', 'Transferencia'),
        ('pago_proveedor', 'Pago a Proveedor'),
        ('otro', 'Otro'),
    ]
    
    billetera = models.ForeignKey(BilleteraElectronica, on_delete=models.CASCADE, related_name='movimientos')
    tipo_movimiento = models.CharField(max_length=10, choices=TIPO_MOVIMIENTO)
    tipo_operacion = models.CharField(max_length=20, choices=TIPO_OPERACION)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    descripcion = models.TextField()
    comprobante = models.CharField(max_length=100, blank=True, null=True)
    proveedor = models.ForeignKey('precios.Proveedor', on_delete=models.SET_NULL, null=True, blank=True)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        ordering = ['-fecha_hora']
    
    def __str__(self):
        return f"{self.get_tipo_movimiento_display()} - ${self.monto} - {self.descripcion[:50]}"
    
    def save(self, *args, **kwargs):
        # Actualizar saldo de la billetera
        if not self.pk:  # Solo si es un nuevo movimiento
            if self.tipo_movimiento == 'ingreso':
                self.billetera.saldo_actual += self.monto
            else:  # egreso
                self.billetera.saldo_actual -= self.monto
            self.billetera.save()
        super().save(*args, **kwargs)
