from django import forms
from django.contrib.auth.models import User
from .models import CajaDiaria, Recreo, EventoEspecial, PagoProveedor, CajaElectronica, IngresoElectronico, PagoElectronico, SaldoElectronico
from precios.models import Proveedor  # Asegúrate de que este import exista

class InicioCajaForm(forms.ModelForm):
    class Meta:
        model = CajaDiaria
        fields = ['nivel', 'turno']
        widgets = {
            'nivel': forms.Select(attrs={'class': 'form-select'}),
            'turno': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'nivel': 'Nivel',
            'turno': 'Turno'
        }

class InicioCajaExtraForm(forms.ModelForm):
    class Meta:
        model = CajaDiaria
        fields = ['nivel', 'turno']  # Solo necesitamos estos campos para cajas extra
        widgets = {
            'nivel': forms.Select(attrs={'class': 'form-select'}),
            'turno': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'nivel': 'Nivel',
            'turno': 'Turno'
        }

class RecreoForm(forms.ModelForm):
    class Meta:
        model = Recreo
        fields = ['numero', 'monto']
        widgets = {
            'numero': forms.NumberInput(attrs={'class': 'form-control'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
        }

class EventoEspecialForm(forms.ModelForm):
    class Meta:
        model = EventoEspecial
        fields = ['descripcion', 'monto']
        widgets = {
            'descripcion': forms.TextInput(attrs={'class': 'form-control'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
        }

class PagoProveedorForm(forms.ModelForm):
    class Meta:
        model = PagoProveedor
        fields = ['proveedor', 'monto', 'comprobante', 'observacion']
        widgets = {
            'proveedor': forms.Select(attrs={'class': 'form-select'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'comprobante': forms.TextInput(attrs={'class': 'form-control'}),
            'observacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        }

# Formularios para Caja Electrónica

class InicioCajaElectronicaForm(forms.ModelForm):
    class Meta:
        model = CajaElectronica
        fields = ['saldo_inicial', 'usuario_responsable']
        widgets = {
            'saldo_inicial': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'usuario_responsable': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'saldo_inicial': 'Saldo Inicial',
            'usuario_responsable': 'Usuario Responsable'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo usuarios admin y encargados
        self.fields['usuario_responsable'].queryset = User.objects.filter(
            perfil__rol__in=['admin', 'encargado']
        ).select_related('perfil')
        self.fields['usuario_responsable'].empty_label = "Seleccionar usuario..."

class IngresoElectronicoForm(forms.ModelForm):
    class Meta:
        model = IngresoElectronico
        fields = ['descripcion', 'monto']
        widgets = {
            'descripcion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Descripción de la transferencia'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
        }
        labels = {
            'descripcion': 'Descripción',
            'monto': 'Monto'
        }

class PagoElectronicoForm(forms.ModelForm):
    class Meta:
        model = PagoElectronico
        fields = ['proveedor', 'monto', 'comprobante', 'observacion']
        widgets = {
            'proveedor': forms.Select(attrs={'class': 'form-select'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'comprobante': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de comprobante'}),
            'observacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        }
        labels = {
            'proveedor': 'Proveedor',
            'monto': 'Monto',
            'comprobante': 'Comprobante',
            'observacion': 'Observación'
        }

class SaldoElectronicoForm(forms.ModelForm):
    class Meta:
        model = SaldoElectronico
        fields = ['monto']
        widgets = {
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
        }
        labels = {
            'monto': 'Saldo Electrónico'
        }