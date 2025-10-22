from django.utils import timezone

def global_context(request):
    """Procesador de contexto global para variables comunes"""
    now = timezone.now()
    return {
        'mes_actual': now.month,
        'anio_actual': now.year,
    }