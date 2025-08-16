from django.db import models
from decimal import Decimal


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
    nombre = models.CharField(max_length=200)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Proveedores"

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

    # Trazabilidad
    fecha_ultima_compra = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Productos"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        """
        Calcula los precios antes de guardar.
        """
        # Calcula precio unitario de compra
        if self.tipo_compra in ['C', 'B']:
            precio_base = self.precio_compra_paquete / self.unidades_por_paquete
        else:
            precio_base = self.precio_compra_paquete

        # Aplica descuento si existe
        if self.descuento_compra:
            self.precio_compra_unitario = precio_base * (1 - (self.descuento_compra / Decimal(100)))
        else:
            self.precio_compra_unitario = precio_base

        # Calcula precio de venta sugerido
        self.precio_venta_sugerido = self.precio_compra_unitario * (1 + (self.margen_ganancia / Decimal(100)))
        
        super().save(*args, **kwargs)
