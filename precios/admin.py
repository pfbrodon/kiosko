from django.contrib import admin
from .models import Categoria, Subcategoria, Proveedor, Marca, Producto, MovimientoStock, HistorialPrecio, EventoProducto

# Register your models here.

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre']
    search_fields = ['nombre']

@admin.register(Subcategoria)
class SubcategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'categoria']
    list_filter = ['categoria']
    search_fields = ['nombre', 'categoria__nombre']

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'telefono', 'email']
    search_fields = ['nombre', 'telefono', 'email']

@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'activo']
    list_filter = ['activo']
    search_fields = ['nombre']

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'subcategoria', 'proveedor', 'precio_venta_final', 'cantidad_stock', 'activo', 'fecha_creacion_real']
    list_filter = ['subcategoria__categoria', 'proveedor', 'activo', 'alerta_stock']
    search_fields = ['nombre', 'descripcion']
    readonly_fields = ['precio_compra_unitario', 'precio_venta_sugerido', 'fecha_creacion', 'fecha_creacion_real']
    
    def fecha_creacion_real(self, obj):
        """Mostrar la fecha de creación real basada en eventos"""
        return obj.fecha_creacion_real().strftime('%d/%m/%Y %H:%M')
    fecha_creacion_real.short_description = 'Fecha Creación Real'

@admin.register(MovimientoStock)
class MovimientoStockAdmin(admin.ModelAdmin):
    list_display = ['producto', 'tipo', 'cantidad', 'fecha']
    list_filter = ['tipo', 'fecha']
    search_fields = ['producto__nombre', 'observacion']

@admin.register(HistorialPrecio)
class HistorialPrecioAdmin(admin.ModelAdmin):
    list_display = ['producto', 'precio_anterior', 'precio_nuevo', 'fecha_cambio', 'motivo']
    list_filter = ['fecha_cambio']
    search_fields = ['producto__nombre', 'motivo']
    readonly_fields = ['fecha_cambio']

@admin.register(EventoProducto)
class EventoProductoAdmin(admin.ModelAdmin):
    list_display = ['producto', 'tipo_evento', 'fecha_evento', 'usuario', 'descripcion_corta']
    list_filter = ['tipo_evento', 'fecha_evento', 'usuario']
    search_fields = ['producto__nombre', 'descripcion', 'usuario']
    readonly_fields = ['fecha_evento']
    date_hierarchy = 'fecha_evento'
    
    def descripcion_corta(self, obj):
        """Mostrar una descripción corta del evento"""
        return obj.descripcion[:50] + '...' if len(obj.descripcion) > 50 else obj.descripcion
    descripcion_corta.short_description = 'Descripción'
