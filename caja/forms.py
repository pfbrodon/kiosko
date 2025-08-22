from django import forms
from .models import CajaDiaria, Recreo, EventoEspecial, PagoProveedor

class InicioCajaForm(forms.ModelForm):
    class Meta:
        model = CajaDiaria
        fields = ['fecha', 'turno', 'nivel']
        widgets = {
            'fecha': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'turno': forms.Select(attrs={'class': 'form-select'}),
            'nivel': forms.Select(attrs={'class': 'form-select'})
        }

class InicioCajaExtraForm(forms.ModelForm):
    class Meta:
        model = CajaDiaria
        fields = ['turno', 'nivel']
        widgets = {
            'turno': forms.Select(attrs={'class': 'form-select'}),
            'nivel': forms.Select(attrs={'class': 'form-select'})
        }

class RecreoForm(forms.ModelForm):
    class Meta:
        model = Recreo
        fields = ['numero', 'monto']
        widgets = {
            'numero': forms.Select(
                attrs={'class': 'form-select'},
                choices=[(1, 'Primer Recreo'), (2, 'Segundo Recreo'), (3, 'Tercer Recreo')]
            ),
            'monto': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01'
            })
        }

class EventoEspecialForm(forms.ModelForm):
    class Meta:
        model = EventoEspecial
        fields = ['monto']
        widgets = {
            'monto': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01'
            })
        }

class PagoProveedorForm(forms.ModelForm):
    class Meta:
        model = PagoProveedor
        fields = ['proveedor', 'monto', 'comprobante', 'observacion']
        widgets = {
            'proveedor': forms.Select(attrs={'class': 'form-select'}),
            'monto': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01'
            }),
            'comprobante': forms.TextInput(attrs={'class': 'form-control'}),
            'observacion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            })
        }