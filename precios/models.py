from django.db import models
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "Categorías"

    def __str__(self):
        return self.nombre


class Subcategoria(models.Model):
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.CASCADE,
        related_name='subcategorias'
    )
    nombre = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = "Subcategorías"
        unique_together = ('categoria', 'nombre')

    def __str__(self):
        return f"{self.categoria.nombre} > {self.nombre}"


class Proveedor(models.Model):
    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.CharField(max_length=200, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'

    def __str__(self):
        return self.nombre


class Marca(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Marcas"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    TIPO_VENTA = [
        ('U', 'Unidad'),
        ('P', 'Promoción'),
    ]
    
    TIPO_COMPRA = [
        ('U', 'Unidad'),
        ('C', 'Caja'),
        ('B', 'Bolsa'),
    ]

    subcategoria = models.ForeignKey(
        Subcategoria,
        on_delete=models.CASCADE,
        related_name='productos'
    )
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.SET_NULL,
        null=True,
        related_name='productos'
    )
    marca = models.ForeignKey(
        Marca,
        on_delete=models.SET_NULL,
        null=True,
        related_name='productos'
    )
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    
    # Información de compra
    tipo_compra = models.CharField(max_length=1, choices=TIPO_COMPRA)
    unidades_por_paquete = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Cantidad de unidades por caja/bolsa"
    )
    precio_compra_paquete = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Precio de compra del paquete/caja/unidad"
    )
    descuento_compra = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Porcentaje de descuento en la compra"
    )
    precio_compra_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        editable=False,
        help_text="Precio de compra por unidad (calculado)"
    )
    
    # Información de venta
    tipo_venta = models.CharField(max_length=1, choices=TIPO_VENTA)
    margen_ganancia = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Porcentaje de ganancia sugerido"
    )
    precio_venta_sugerido = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        editable=False
    )
    precio_venta_final = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Precio final de venta al público"
    )

    # Información de stock
    cantidad_stock = models.PositiveIntegerField(
        default=0,
        help_text="Cantidad actual en stock"
    )
    stock_minimo = models.PositiveIntegerField(
        default=1,
        help_text="Cantidad mínima antes de necesitar reposición"
    )
    alerta_stock = models.BooleanField(
        default=False,
        help_text="Indica si se debe alertar cuando el stock está bajo"
    )

    # Trazabilidad
    fecha_creacion = models.DateTimeField(auto_now_add=True, help_text="Fecha de creación del producto")
    fecha_ultima_compra = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Productos"
        ordering = ['nombre']
        # 🚀 ÍNDICES PARA MEJOR PERFORMANCE
        indexes = [
            models.Index(fields=['nombre'], name='producto_nombre_idx'),
            models.Index(fields=['precio_venta_final'], name='producto_precio_idx'),
            models.Index(fields=['cantidad_stock'], name='producto_stock_idx'),
            models.Index(fields=['fecha_creacion'], name='producto_fecha_idx'),
            models.Index(fields=['subcategoria', 'activo'], name='producto_cat_activo_idx'),
            models.Index(fields=['proveedor', 'activo'], name='producto_prov_activo_idx'),
            models.Index(fields=['alerta_stock'], name='producto_alerta_idx'),
            models.Index(fields=['activo', 'cantidad_stock'], name='producto_estado_stock_idx'),
        ]

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        """
        Calcula los precios antes de guardar, verifica el estado del stock,
        y registra cambios en el precio de venta final.
        """
        # Obtener el precio anterior si el producto ya existe
        precio_anterior = None
        if self.pk:
            try:
                producto_anterior = Producto.objects.get(pk=self.pk)
                precio_anterior = producto_anterior.precio_venta_final
            except Producto.DoesNotExist:
                pass
        
        # Calcula precio unitario de compra
        if self.tipo_compra in ['C', 'B']:
            precio_base = Decimal(str(self.precio_compra_paquete)) / Decimal(str(self.unidades_por_paquete))
        else:
            precio_base = Decimal(str(self.precio_compra_paquete))

        # Aplica descuento si existe
        if self.descuento_compra:
            descuento_decimal = Decimal(str(self.descuento_compra))
            self.precio_compra_unitario = precio_base * (Decimal('1') - (descuento_decimal / Decimal('100')))
        else:
            self.precio_compra_unitario = precio_base

        # Calcula precio de venta sugerido
        margen_decimal = Decimal(str(self.margen_ganancia))
        self.precio_venta_sugerido = self.precio_compra_unitario * (Decimal('1') + (margen_decimal / Decimal('100')))
        
        # Actualiza el estado de la alerta de stock
        self.alerta_stock = self.cantidad_stock <= self.stock_minimo
        
        super().save(*args, **kwargs)
        
        # Registrar cambio de precio si hubo modificación
        if precio_anterior is not None and precio_anterior != self.precio_venta_final:
            HistorialPrecio.objects.create(
                producto=self,
                precio_anterior=precio_anterior,
                precio_nuevo=self.precio_venta_final,
                motivo="Modificación manual del precio"
            )

    def tiene_cambio_precio_reciente(self, horas=73):
        """
        Verifica si el producto tuvo cambios de precio en las últimas X horas.
        Por defecto verifica las últimas 73 horas.
        """
        fecha_limite = timezone.now() - timedelta(hours=horas)
        return self.historial_precios.filter(fecha_cambio__gte=fecha_limite).exists()
    
    def es_producto_nuevo(self, horas=72):
        """
        Verifica si el producto fue creado en las últimas X horas.
        Utiliza el registro de eventos para mayor precisión.
        """
        # Buscar el evento de creación más antiguo
        evento_creacion = self.eventos.filter(tipo_evento='CREACION').order_by('fecha_evento').first()
        
        if evento_creacion:
            # Usar la fecha del evento de creación
            fecha_limite = timezone.now() - timedelta(hours=horas)
            return evento_creacion.fecha_evento >= fecha_limite
        else:
            # Fallback: usar fecha_creacion del modelo si no hay evento
            fecha_limite = timezone.now() - timedelta(hours=horas)
            return self.fecha_creacion >= fecha_limite
    
    def fecha_creacion_real(self):
        """
        Retorna la fecha de creación real del producto basada en eventos.
        """
        evento_creacion = self.eventos.filter(tipo_evento='CREACION').order_by('fecha_evento').first()
        if evento_creacion:
            return evento_creacion.fecha_evento
        else:
            return self.fecha_creacion
    
    def registrar_evento(self, tipo_evento, descripcion="", valor_anterior=None, valor_nuevo=None, usuario=""):
        """
        Método helper para registrar eventos del producto.
        """
        return EventoProducto.objects.create(
            producto=self,
            tipo_evento=tipo_evento,
            descripcion=descripcion,
            valor_anterior=valor_anterior,
            valor_nuevo=valor_nuevo,
            usuario=usuario
        )

    @property
    def estado_stock(self):
        """
        Retorna el estado del stock como texto.
        """
        if self.cantidad_stock <= 0:
            return "Sin stock"
        elif self.cantidad_stock <= self.stock_minimo:
            return "Stock bajo"
        else:
            return "En stock"


class MovimientoStock(models.Model):
    TIPO_MOVIMIENTO = [
        ('E', 'Entrada'),
        ('S', 'Salida')
    ]

    producto = models.ForeignKey(
        Producto, 
        on_delete=models.CASCADE,
        related_name='movimientos'
    )
    fecha = models.DateTimeField(auto_now_add=True)
    tipo = models.CharField(
        max_length=1, 
        choices=TIPO_MOVIMIENTO
    )
    cantidad = models.PositiveIntegerField()
    observacion = models.CharField(
        max_length=255, 
        blank=True
    )

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.producto.nombre} - {self.get_tipo_display()} - {self.cantidad} unidades"


class HistorialPrecio(models.Model):
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='historial_precios'
    )
    precio_anterior = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Precio anterior al cambio"
    )
    precio_nuevo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Nuevo precio después del cambio"
    )
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    motivo = models.CharField(
        max_length=255,
        blank=True,
        help_text="Razón del cambio de precio"
    )
    
    class Meta:
        ordering = ['-fecha_cambio']
        verbose_name = "Historial de Precio"
        verbose_name_plural = "Historial de Precios"
    
    def __str__(self):
        return f"{self.producto.nombre} - ${self.precio_anterior} → ${self.precio_nuevo}"


class EventoProducto(models.Model):
    """
    Modelo para registrar eventos importantes en la vida de un producto
    """
    TIPO_EVENTO_CHOICES = [
        ('CREACION', 'Creación del producto'),
        ('MODIFICACION_PRECIO', 'Modificación de precio'),
        ('ACTIVACION', 'Activación del producto'),
        ('DESACTIVACION', 'Desactivación del producto'),
        ('ACTUALIZACION_STOCK', 'Actualización de stock'),
        ('CAMBIO_INFO', 'Cambio de información general'),
    ]
    
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='eventos'
    )
    tipo_evento = models.CharField(
        max_length=20,
        choices=TIPO_EVENTO_CHOICES,
        help_text="Tipo de evento registrado"
    )
    fecha_evento = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora del evento"
    )
    descripcion = models.TextField(
        blank=True,
        help_text="Descripción detallada del evento"
    )
    valor_anterior = models.TextField(
        blank=True,
        null=True,
        help_text="Valor anterior (en formato JSON si es complejo)"
    )
    valor_nuevo = models.TextField(
        blank=True,
        null=True,
        help_text="Nuevo valor (en formato JSON si es complejo)"
    )
    usuario = models.CharField(
        max_length=100,
        blank=True,
        help_text="Usuario que realizó el cambio"
    )
    
    class Meta:
        ordering = ['-fecha_evento']
        verbose_name = "Evento de Producto"
        verbose_name_plural = "Eventos de Productos"
        indexes = [
            models.Index(fields=['producto', 'tipo_evento']),
            models.Index(fields=['fecha_evento']),
            models.Index(fields=['tipo_evento']),
        ]
    
    def __str__(self):
        return f"{self.producto.nombre} - {self.get_tipo_evento_display()} ({self.fecha_evento.strftime('%d/%m/%Y %H:%M')})"
