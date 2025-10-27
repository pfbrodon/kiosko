# caja/logging_utils.py
"""
Utilidades de logging para rastrear cambios en saldos y detectar problemas
"""

import logging
from decimal import Decimal
from django.utils import timezone

# Configurar logger específico para caja
logger = logging.getLogger('caja.saldos')

def log_cambio_saldo_general(
    accion: str,
    caja_id: int,
    saldo_anterior: Decimal,
    saldo_nuevo: Decimal,
    diferencia_aplicada: Decimal,
    usuario=None,
    observaciones=""
):
    """
    Registra cambios en el saldo general para auditoría
    
    Args:
        accion: 'CIERRE', 'REAPERTURA', 'AJUSTE_MANUAL', etc.
        caja_id: ID de la caja que causó el cambio
        saldo_anterior: Saldo antes del cambio
        saldo_nuevo: Saldo después del cambio
        diferencia_aplicada: Diferencia que se aplicó
        usuario: Usuario que realizó la acción
        observaciones: Información adicional
    """
    timestamp = timezone.now()
    usuario_str = f"Usuario: {usuario.username}" if usuario else "Sistema"
    
    mensaje = (
        f"[{accion}] Caja ID: {caja_id} | "
        f"Saldo: ${saldo_anterior} → ${saldo_nuevo} | "
        f"Diferencia: {'+' if diferencia_aplicada >= 0 else ''}${diferencia_aplicada} | "
        f"{usuario_str} | "
        f"Timestamp: {timestamp} | "
        f"Observaciones: {observaciones or 'N/A'}"
    )
    
    logger.info(mensaje)
    
    # También imprimir para debugging inmediato
    print(f"AUDIT_LOG: {mensaje}")

def log_discrepancia_detectada(
    caja_id: int,
    diferencia_esperada: Decimal,
    diferencia_calculada: Decimal,
    saldo_general: Decimal
):
    """
    Registra cuando se detecta una discrepancia en los cálculos
    """
    discrepancia = diferencia_calculada - diferencia_esperada
    timestamp = timezone.now()
    
    mensaje = (
        f"[DISCREPANCIA] Caja ID: {caja_id} | "
        f"Esperado: ${diferencia_esperada} vs Calculado: ${diferencia_calculada} | "
        f"Discrepancia: ${discrepancia} | "
        f"Saldo General: ${saldo_general} | "
        f"Timestamp: {timestamp}"
    )
    
    logger.warning(mensaje)
    print(f"WARNING: {mensaje}")

def validar_consistencia_saldo(caja, saldo_general_actual):
    """
    Valida que los cálculos de la caja sean consistentes
    
    Returns:
        tuple (es_valido: bool, mensaje: str)
    """
    try:
        # Recalcular saldo parcial
        saldo_parcial_calculado = caja.calcular_saldo_parcial()
        
        # Verificar si coincide con el almacenado
        if abs(saldo_parcial_calculado - caja.saldo_parcial) > Decimal('0.01'):
            return False, f"Saldo parcial inconsistente: BD=${caja.saldo_parcial}, Calculado=${saldo_parcial_calculado}"
        
        # Verificar diferencia almacenada vs calculada
        if caja.diferencia_al_cerrar is not None:
            diferencia_calculada = caja.saldo_parcial - caja.saldo_inicial
            if abs(diferencia_calculada - caja.diferencia_al_cerrar) > Decimal('0.01'):
                return False, f"Diferencia inconsistente: Guardada=${caja.diferencia_al_cerrar}, Calculada=${diferencia_calculada}"
        
        return True, "Caja consistente"
        
    except Exception as e:
        return False, f"Error en validación: {str(e)}"