from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Producto, EventoProducto
import json


@receiver(post_save, sender=Producto)
def registrar_evento_producto(sender, instance, created, **kwargs):
    """
    Registra automáticamente eventos cuando se crea o modifica un producto.
    """
    if created:
        # Producto recién creado
        EventoProducto.objects.create(
            producto=instance,
            tipo_evento='CREACION',
            descripcion=f'Producto "{instance.nombre}" creado',
            valor_nuevo=json.dumps({
                'nombre': instance.nombre,
                'precio_venta_final': str(instance.precio_venta_final),
                'categoria': str(instance.subcategoria.categoria.nombre),
                'subcategoria': str(instance.subcategoria.nombre),
            }),
            usuario='Sistema'
        )
    else:
        # Producto modificado - verificar qué cambió
        try:
            # Obtener la versión anterior del producto
            producto_anterior = Producto.objects.get(pk=instance.pk)
            
            cambios = []
            
            # Verificar cambios importantes
            if hasattr(instance, '_precio_anterior') and instance._precio_anterior != instance.precio_venta_final:
                cambios.append('precio')
                EventoProducto.objects.create(
                    producto=instance,
                    tipo_evento='MODIFICACION_PRECIO',
                    descripcion=f'Precio cambiado de ${instance._precio_anterior} a ${instance.precio_venta_final}',
                    valor_anterior=str(instance._precio_anterior),
                    valor_nuevo=str(instance.precio_venta_final),
                    usuario='Sistema'
                )
            
            # Verificar cambio de estado activo
            if hasattr(instance, '_estado_anterior'):
                if instance._estado_anterior != instance.activo:
                    if instance.activo:
                        EventoProducto.objects.create(
                            producto=instance,
                            tipo_evento='ACTIVACION',
                            descripcion=f'Producto "{instance.nombre}" activado',
                            valor_anterior='False',
                            valor_nuevo='True',
                            usuario='Sistema'
                        )
                    else:
                        EventoProducto.objects.create(
                            producto=instance,
                            tipo_evento='DESACTIVACION',
                            descripcion=f'Producto "{instance.nombre}" desactivado',
                            valor_anterior='True',
                            valor_nuevo='False',
                            usuario='Sistema'
                        )
            
            # Verificar cambio de stock significativo
            if hasattr(instance, '_stock_anterior'):
                diferencia_stock = abs(instance.cantidad_stock - instance._stock_anterior)
                if diferencia_stock >= 5:  # Solo registrar cambios significativos
                    EventoProducto.objects.create(
                        producto=instance,
                        tipo_evento='ACTUALIZACION_STOCK',
                        descripcion=f'Stock actualizado de {instance._stock_anterior} a {instance.cantidad_stock}',
                        valor_anterior=str(instance._stock_anterior),
                        valor_nuevo=str(instance.cantidad_stock),
                        usuario='Sistema'
                    )
            
            # Si hubo otros cambios generales
            if not cambios and not hasattr(instance, '_precio_anterior'):
                EventoProducto.objects.create(
                    producto=instance,
                    tipo_evento='CAMBIO_INFO',
                    descripcion=f'Información del producto "{instance.nombre}" actualizada',
                    usuario='Sistema'
                )
                
        except Exception as e:
            # En caso de error, no interrumpir el guardado
            pass


@receiver(pre_save, sender=Producto)
def preparar_seguimiento_cambios(sender, instance, **kwargs):
    """
    Prepara el seguimiento de cambios antes de guardar.
    """
    if instance.pk:  # Solo para productos existentes
        try:
            producto_anterior = Producto.objects.get(pk=instance.pk)
            instance._precio_anterior = producto_anterior.precio_venta_final
            instance._estado_anterior = producto_anterior.activo
            instance._stock_anterior = producto_anterior.cantidad_stock
        except Producto.DoesNotExist:
            pass
