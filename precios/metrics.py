from django.db.models import Count, Sum, Avg, Q, F
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from .models import Producto, HistorialPrecio, EventoProducto
from caja.models import CajaDiaria, CajaElectronica

class MetricasKiosko:
    """
    Clase para generar métricas y estadísticas del negocio
    """
    
    @staticmethod
    def resumen_productos():
        """Resumen general de productos"""
        total_productos = Producto.objects.count()
        productos_activos = Producto.objects.filter(activo=True).count()
        productos_alerta = Producto.objects.filter(alerta_stock=True).count()
        productos_sin_stock = Producto.objects.filter(cantidad_stock=0).count()
        
        # Valor total del inventario
        valor_inventario = Producto.objects.filter(activo=True).aggregate(
            total=Sum('precio_venta_final')
        )['total'] or Decimal('0')
        
        return {
            'total_productos': total_productos,
            'productos_activos': productos_activos,
            'productos_inactivos': total_productos - productos_activos,
            'productos_alerta': productos_alerta,
            'productos_sin_stock': productos_sin_stock,
            'valor_inventario': valor_inventario,
            'porcentaje_activos': round((productos_activos / total_productos * 100), 1) if total_productos > 0 else 0
        }
    
    @staticmethod
    def productos_nuevos(dias=7):
        """Productos agregados en los últimos días"""
        fecha_limite = timezone.now() - timedelta(days=dias)
        
        # Usar eventos para mayor precisión
        eventos_creacion = EventoProducto.objects.filter(
            tipo_evento='CREACION',
            fecha_evento__gte=fecha_limite
        ).select_related('producto')
        
        productos_nuevos = []
        for evento in eventos_creacion:
            productos_nuevos.append({
                'producto': evento.producto,
                'fecha_creacion': evento.fecha_evento,
                'dias_transcurridos': (timezone.now() - evento.fecha_evento).days
            })
        
        return {
            'cantidad': len(productos_nuevos),
            'productos': productos_nuevos[:10],  # Solo los últimos 10
            'periodo': f"últimos {dias} días"
        }
    
    @staticmethod
    def cambios_precios(dias=7):
        """Cambios de precios en el período especificado"""
        fecha_limite = timezone.now() - timedelta(days=dias)
        
        cambios = HistorialPrecio.objects.filter(
            fecha_cambio__gte=fecha_limite
        ).select_related('producto').order_by('-fecha_cambio')
        
        # Estadísticas de cambios
        total_cambios = cambios.count()
        aumentos = cambios.filter(precio_nuevo__gt=F('precio_anterior')).count()
        descuentos = cambios.filter(precio_nuevo__lt=F('precio_anterior')).count()
        
        return {
            'total_cambios': total_cambios,
            'aumentos': aumentos,
            'descuentos': descuentos,
            'cambios_recientes': cambios[:10],
            'periodo': f"últimos {dias} días"
        }
    
    @staticmethod
    def estado_cajas():
        """Estado actual de las cajas"""
        hoy = timezone.now().date()
        
        # Caja diaria
        cajas_hoy = CajaDiaria.objects.filter(fecha=hoy)
        caja_abierta = cajas_hoy.filter(cerrada=False).first()
        
        # Caja electrónica
        caja_electronica = CajaElectronica.objects.filter(fecha=hoy).first()
        caja_elec_abierta = caja_electronica and not caja_electronica.cerrada
        
        return {
            'caja_diaria_abierta': caja_abierta is not None,
            'caja_electronica_abierta': caja_elec_abierta,
            'cajas_del_dia': cajas_hoy.count(),
            'fecha': hoy
        }
    
    @staticmethod
    def top_productos_alertas():
        """Productos que necesitan atención inmediata"""
        # Productos sin stock
        sin_stock = Producto.objects.filter(
            cantidad_stock=0,
            activo=True
        ).select_related('subcategoria__categoria')[:5]
        
        # Productos con stock bajo
        stock_bajo = Producto.objects.filter(
            alerta_stock=True,
            cantidad_stock__gt=0,
            activo=True
        ).select_related('subcategoria__categoria')[:5]
        
        # Productos nuevos que necesitan atención
        productos_nuevos = []
        for producto in Producto.objects.all()[:100]:  # Revisar solo los primeros 100
            if producto.es_producto_nuevo(24):  # Nuevos en 24h
                productos_nuevos.append(producto)
            if len(productos_nuevos) >= 5:
                break
        
        return {
            'sin_stock': sin_stock,
            'stock_bajo': stock_bajo,
            'productos_nuevos': productos_nuevos
        }
    
    @staticmethod
    def resumen_categorias():
        """Resumen por categorías"""
        from precios.models import Categoria
        
        categorias_stats = []
        for categoria in Categoria.objects.all():
            productos_categoria = Producto.objects.filter(
                subcategoria__categoria=categoria,
                activo=True
            )
            
            total = productos_categoria.count()
            con_stock = productos_categoria.filter(cantidad_stock__gt=0).count()
            alertas = productos_categoria.filter(alerta_stock=True).count()
            
            categorias_stats.append({
                'categoria': categoria,
                'total_productos': total,
                'con_stock': con_stock,
                'sin_stock': total - con_stock,
                'alertas': alertas,
                'porcentaje_stock': round((con_stock / total * 100), 1) if total > 0 else 0
            })
        
        return sorted(categorias_stats, key=lambda x: x['total_productos'], reverse=True)
    
    @classmethod
    def dashboard_completo(cls):
        """Genera todas las métricas para el dashboard"""
        return {
            'resumen_productos': cls.resumen_productos(),
            'productos_nuevos': cls.productos_nuevos(),
            'cambios_precios': cls.cambios_precios(),
            'estado_cajas': cls.estado_cajas(),
            'alertas': cls.top_productos_alertas(),
            'categorias': cls.resumen_categorias(),
            'fecha_actualizacion': timezone.now()
        }
