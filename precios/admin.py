from django.contrib import admin
from .models import Categoria, Subcategoria, Proveedor, Marca, Producto, MovimientoStock, HistorialPrecio

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
    list_display = ['nombre', 'subcategoria', 'proveedor', 'precio_venta_final', 'cantidad_stock', 'activo']
    list_filter = ['subcategoria__categoria', 'proveedor', 'activo', 'alerta_stock']
    search_fields = ['nombre', 'descripcion']
    readonly_fields = ['precio_compra_unitario', 'precio_venta_sugerido']

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
