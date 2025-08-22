from django import forms
from .models import CajaDiaria, Recreo, EventoEspecial, PagoProveedor
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