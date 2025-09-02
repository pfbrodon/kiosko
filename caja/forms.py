from django import forms
from .models import CajaDiaria, Recreo, EventoEspecial, PagoProveedor
from precios.models import Proveedor  # Asegúrate de que este import exista
from .models import BilleteraElectronica, MovimientoBilletera

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

class AbrirBilleteraForm(forms.ModelForm):
    class Meta:
        model = BilleteraElectronica
        fields = ['saldo_inicial']
        widgets = {
            'saldo_inicial': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Ingrese el saldo inicial'
            })
        }
        labels = {
            'saldo_inicial': 'Saldo Inicial'
        }

class MovimientoBilleteraForm(forms.ModelForm):
    class Meta:
        model = MovimientoBilletera
        fields = ['tipo_movimiento', 'tipo_operacion', 'monto', 'descripcion', 'comprobante', 'proveedor']
        widgets = {
            'tipo_movimiento': forms.Select(attrs={'class': 'form-control'}),
            'tipo_operacion': forms.Select(attrs={'class': 'form-control'}),
            'monto': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción del movimiento'
            }),
            'comprobante': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de comprobante (opcional)'
            }),
            'proveedor': forms.Select(attrs={'class': 'form-control'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['proveedor'].required = False
        self.fields['proveedor'].queryset = Proveedor.objects.all()
        
        # JavaScript para mostrar/ocultar campo proveedor
        self.fields['tipo_operacion'].widget.attrs['onchange'] = 'toggleProveedorField()'