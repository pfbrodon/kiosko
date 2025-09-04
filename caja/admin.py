from django.contrib import admin
from .models import (
    SaldoGeneral, SaldoElectronico, CajaDiaria, CajaElectronica,
    Recreo, EventoEspecial, PagoProveedor, IngresoElectronico, PagoElectronico
)

@admin.register(SaldoGeneral)
class SaldoGeneralAdmin(admin.ModelAdmin):
    list_display = ['monto', 'ultima_actualizacion']
    readonly_fields = ['ultima_actualizacion']

@admin.register(SaldoElectronico)
class SaldoElectronicoAdmin(admin.ModelAdmin):
    list_display = ['monto', 'ultima_actualizacion']
    readonly_fields = ['ultima_actualizacion']

@admin.register(CajaDiaria)
class CajaDiariaAdmin(admin.ModelAdmin):
    list_display = ['fecha', 'turno', 'nivel', 'saldo_inicial', 'saldo_parcial', 'cerrada', 'es_extra']
    list_filter = ['fecha', 'turno', 'nivel', 'cerrada', 'es_extra']
    search_fields = ['fecha']
    readonly_fields = ['fecha_creacion', 'saldo_parcial']

@admin.register(CajaElectronica)
class CajaElectronicaAdmin(admin.ModelAdmin):
    list_display = ['fecha', 'usuario_responsable', 'saldo_inicial', 'saldo_parcial', 'cerrada']
    list_filter = ['fecha', 'cerrada', 'usuario_responsable']
    search_fields = ['fecha', 'usuario_responsable__username']
    readonly_fields = ['fecha_creacion', 'saldo_parcial']

@admin.register(Recreo)
class RecreoAdmin(admin.ModelAdmin):
    list_display = ['caja', 'numero', 'monto', 'fecha_registro']
    list_filter = ['fecha_registro']

@admin.register(EventoEspecial)
class EventoEspecialAdmin(admin.ModelAdmin):
    list_display = ['caja', 'descripcion', 'monto', 'fecha_registro']
    list_filter = ['fecha_registro']

@admin.register(PagoProveedor)
class PagoProveedorAdmin(admin.ModelAdmin):
    list_display = ['caja', 'proveedor', 'monto', 'comprobante', 'fecha_registro']
    list_filter = ['fecha_registro', 'proveedor']

@admin.register(IngresoElectronico)
class IngresoElectronicoAdmin(admin.ModelAdmin):
    list_display = ['caja_electronica', 'descripcion', 'monto', 'usuario_registro', 'fecha_registro']
    list_filter = ['fecha_registro', 'usuario_registro']
    readonly_fields = ['fecha_registro']

@admin.register(PagoElectronico)
class PagoElectronicoAdmin(admin.ModelAdmin):
    list_display = ['caja_electronica', 'proveedor', 'monto', 'comprobante', 'usuario_registro', 'fecha_registro']
    list_filter = ['fecha_registro', 'proveedor', 'usuario_registro']
    readonly_fields = ['fecha_registro']
