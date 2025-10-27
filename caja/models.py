from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Sum
from decimal import Decimal
from django.contrib.auth.models import User

class SaldoGeneral(models.Model):
    monto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Saldo General Efectivo: ${self.monto}"
    
    def get_saldo_total(self):
        """Retorna el saldo total: efectivo + electrónico"""
        try:
            saldo_electronico = SaldoElectronico.objects.first()
            monto_electronico = saldo_electronico.monto if saldo_electronico else Decimal('0')
            return self.monto + monto_electronico
        except:
            return self.monto
    
    def get_saldo_electronico(self):
        """Retorna el saldo electrónico actual"""
        try:
            saldo_electronico = SaldoElectronico.objects.first()
            return saldo_electronico.monto if saldo_electronico else Decimal('0')
        except:
            return Decimal('0')

class SaldoElectronico(models.Model):
    monto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Saldo Electrónico: ${self.monto}"
    
    class Meta:
        verbose_name = "Saldo Electrónico"
        verbose_name_plural = "Saldos Electrónicos"

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
    
    # Campos para rastrear reaperturas
    fue_reabierta = models.BooleanField(default=False)
    fecha_reapertura = models.DateTimeField(null=True, blank=True)
    usuario_reapertura = models.ForeignKey(User, null=True, blank=True, on_delete=models.PROTECT,
                                         related_name='cajas_reabiertas',
                                         help_text="Usuario que reabrió esta caja")
    
    # Campo para prevenir discrepancias en reaperturas
    diferencia_al_cerrar = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Diferencia exacta aplicada al saldo general cuando se cerró la caja"
    )

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
        
        # Obtener el saldo inicial a considerar (0 para primarias, valor real para secundarias)
        saldo_inicial_a_usar = self.get_saldo_inicial_display()
        
        # Calcula el saldo parcial
        return saldo_inicial_a_usar + ingresos_recreos + ingresos_eventos - egresos_pagos

    def actualizar_saldo_parcial(self):
        self.saldo_parcial = self.calcular_saldo_parcial()
        self.save()

    def reabrir_caja(self, usuario):
        """Reabre una caja cerrada, solo para el mismo día"""
        from datetime import date, datetime
        
        if not self.cerrada:
            raise ValidationError("Esta caja ya está abierta")
        
        # Verificar que sea del mismo día
        if self.fecha != date.today():
            raise ValidationError("Solo se pueden reabrir cajas del día actual")
        
        # Verificar que no haya otra caja abierta del mismo nivel y turno
        if CajaDiaria.objects.filter(
            nivel=self.nivel,
            turno=self.turno,
            cerrada=False
        ).exists():
            raise ValidationError(f"Ya existe una caja abierta para {self.get_nivel_display()} - {self.get_turno_display()}")
        
        # Reabrir la caja
        self.cerrada = False
        self.fue_reabierta = True
        self.fecha_reapertura = datetime.now()
        self.usuario_reapertura = usuario
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

class CajaElectronica(models.Model):
    fecha = models.DateField()
    saldo_inicial = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    saldo_parcial = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cerrada = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    usuario_responsable = models.ForeignKey(User, on_delete=models.PROTECT, 
                                          help_text="Usuario responsable de esta caja electrónica")

    class Meta:
        ordering = ['-fecha']
        verbose_name = "Caja Electrónica"
        verbose_name_plural = "Cajas Electrónicas"
        # Solo puede haber una caja electrónica por fecha
        unique_together = ['fecha']
        # Solo puede haber una caja electrónica abierta
        constraints = [
            models.UniqueConstraint(
                fields=['cerrada'],
                condition=models.Q(cerrada=False),
                name='unique_open_electronica_constraint'
            )
        ]

    def clean(self):
        import datetime
        
        # Si estamos creando una nueva caja electrónica
        if not self.id:
            # Verificar que no exista otra caja electrónica para la misma fecha
            if CajaElectronica.objects.filter(fecha=self.fecha).exists():
                raise ValidationError('Ya existe una caja electrónica para esta fecha')
            
            # Verificar que no exista otra caja electrónica abierta
            if CajaElectronica.objects.filter(cerrada=False).exists():
                raise ValidationError('Ya existe una caja electrónica abierta')
        else:
            # Si estamos editando una caja existente
            if not self.cerrada:
                caja_abierta = CajaElectronica.objects.filter(
                    cerrada=False
                ).exclude(pk=self.pk).exists()
                
                if caja_abierta:
                    raise ValidationError('Ya existe una caja electrónica abierta')

    def __str__(self):
        return f"Caja Electrónica - {self.fecha} - {self.usuario_responsable.username}"

    def calcular_saldo_parcial(self):
        """Calcula el saldo parcial basado en ingresos y egresos"""
        # Suma todos los ingresos por transferencias
        ingresos_transferencias = self.ingresoelectronico_set.aggregate(
            total=Sum('monto'))['total'] or Decimal('0')
        
        # Suma todos los egresos por pagos
        egresos_pagos = self.pagoelectronico_set.aggregate(
            total=Sum('monto'))['total'] or Decimal('0')
        
        # Calcula el saldo parcial
        return self.saldo_inicial + ingresos_transferencias - egresos_pagos

    def actualizar_saldo_parcial(self):
        """Actualiza el saldo parcial y guarda el modelo"""
        self.saldo_parcial = self.calcular_saldo_parcial()
        self.save()

    def get_total_ingresos(self):
        """Retorna el total de ingresos por transferencias"""
        return self.ingresoelectronico_set.aggregate(
            total=Sum('monto')
        )['total'] or Decimal('0')
        
    def get_total_egresos(self):
        """Retorna el total de egresos por pagos electrónicos"""
        return self.pagoelectronico_set.aggregate(
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

class IngresoElectronico(models.Model):
    """Ingresos por transferencias en la caja electrónica"""
    caja_electronica = models.ForeignKey(CajaElectronica, on_delete=models.CASCADE)
    descripcion = models.CharField(max_length=255, help_text="Descripción de la transferencia")
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    usuario_registro = models.ForeignKey(User, on_delete=models.PROTECT,
                                       help_text="Usuario que registró el ingreso")

    class Meta:
        ordering = ['-fecha_registro']
        verbose_name = "Ingreso Electrónico"
        verbose_name_plural = "Ingresos Electrónicos"

    def __str__(self):
        return f"{self.descripcion} - ${self.monto}"

class PagoElectronico(models.Model):
    """Egresos por pagos a proveedores desde la caja electrónica"""
    caja_electronica = models.ForeignKey(CajaElectronica, on_delete=models.CASCADE)
    proveedor = models.ForeignKey('precios.Proveedor', on_delete=models.PROTECT)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    comprobante = models.CharField(max_length=50, help_text="Número de comprobante o referencia")
    observacion = models.TextField(blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    usuario_registro = models.ForeignKey(User, on_delete=models.PROTECT,
                                       help_text="Usuario que registró el pago")

    class Meta:
        ordering = ['-fecha_registro']
        verbose_name = "Pago Electrónico"
        verbose_name_plural = "Pagos Electrónicos"

    def __str__(self):
        return f"Pago a {self.proveedor.nombre} - ${self.monto}"
