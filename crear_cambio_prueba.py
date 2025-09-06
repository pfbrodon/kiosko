from precios.models import Producto, HistorialPrecio
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

# Obtener el primer producto
try:
    producto = Producto.objects.first()
    if producto:
        print(f"Producto encontrado: {producto.nombre}")
        print(f"Precio actual: ${producto.precio_venta_final}")
        
        # Crear un cambio de precio reciente (10 horas atrás)
        fecha_cambio = timezone.now() - timedelta(hours=10)
        historial = HistorialPrecio.objects.create(
            producto=producto,
            precio_anterior=producto.precio_venta_final - Decimal('5.00'),
            precio_nuevo=producto.precio_venta_final,
            motivo="Prueba de cambio reciente"
        )
        
        # Modificar la fecha para que sea reciente
        historial.fecha_cambio = fecha_cambio
        historial.save()
        
        print("✅ Cambio de precio creado")
        print(f"¿Tiene cambio reciente? {producto.tiene_cambio_precio_reciente()}")
    else:
        print("No hay productos en la base de datos")
except Exception as e:
    print(f"Error: {e}")
