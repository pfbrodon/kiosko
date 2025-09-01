from django import forms
from .models import Categoria, Subcategoria, Proveedor, Producto, Marca, MovimientoStock

class ProductoForm(forms.ModelForm):
    stock_inicial = forms.IntegerField(
        min_value=0,
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Cantidad inicial en stock'
        })
    )

    class Meta:
        model = Producto
        fields = [
            'nombre',
            'marca',
            'subcategoria',
            'proveedor',
            'tipo_compra',
            'unidades_por_paquete',
            'precio_compra_paquete',
            'descuento_compra',
            'tipo_venta',
            'margen_ganancia',
            'precio_venta_final',
            'stock_inicial',
            'stock_minimo',
            'activo'
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'precio_compra_paquete': forms.NumberInput(attrs={'step': '0.01'}),
            'descuento_compra': forms.NumberInput(attrs={'step': '0.01'}),
            'margen_ganancia': forms.NumberInput(attrs={'step': '0.01'}),
            'precio_venta_final': forms.NumberInput(attrs={'step': '0.01'}),
            'stock_inicial': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'Cantidad inicial en stock'
            }),
            'stock_minimo': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Stock mínimo para alertas'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'role': 'switch'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if instance:
            # Si estamos editando, deshabilitamos el campo stock_inicial
            self.fields['stock_inicial'].widget.attrs['disabled'] = True
            self.fields['stock_inicial'].required = False
            # Establecemos el valor inicial del campo
            self.fields['stock_inicial'].initial = instance.cantidad_stock
            
            # PRESERVAR EL PRECIO DE VENTA ACTUAL AL EDITAR
            self._precio_venta_original = instance.precio_venta_final
            
            # Forzar el valor inicial del precio de venta final
            self.fields['precio_venta_final'].initial = instance.precio_venta_final
            
            # Agregar atributo data para JavaScript
            self.fields['precio_venta_final'].widget.attrs.update({
                'data-precio-original': str(instance.precio_venta_final),
                'data-editing': 'true'
            })
        
        # Agregar clases de Bootstrap excepto para el campo activo
        for field in self.fields:
            if field != 'activo':
                self.fields[field].widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Si estamos editando, usar el precio original a menos que haya sido cambiado manualmente
        if hasattr(self, '_precio_venta_original') and self.instance.pk:
            # Verificar si el precio fue modificado intencionalmente
            precio_form = self.cleaned_data.get('precio_venta_final')
            
            # Si el precio no cambió o es None, usar el original
            if not precio_form or precio_form == self._precio_venta_original:
                instance.precio_venta_final = self._precio_venta_original
            else:
                instance.precio_venta_final = precio_form
        
        if commit:
            instance.save()
        return instance

class SubcategoriaForm(forms.ModelForm):
    class Meta:
        model = Subcategoria
        fields = ['categoria', 'nombre']
        widgets = {
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
        }

class ProductoSearchForm(forms.Form):
    ESTADO_CHOICES = [
        ('', 'Todos'),
        ('1', 'Activos'),
        ('0', 'Inactivos'),
        ('B', 'Stock Bajo')
    ]
    
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.all(),
        required=False,
        empty_label="Todas las categorías"
    )
    subcategoria = forms.ModelChoiceField(
        queryset=Subcategoria.objects.all(),
        required=False,
        empty_label="Todas las subcategorías"
    )
    proveedor = forms.ModelChoiceField(
        queryset=Proveedor.objects.all(),
        required=False,
        empty_label="Todos los proveedores"
    )
    estado = forms.ChoiceField(
        choices=ESTADO_CHOICES,
        required=False
    )
    busqueda = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Buscar por nombre...'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
            
class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la categoría'
            })
        }
class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['nombre', 'telefono', 'direccion', 'email']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
        
class MarcaForm(forms.ModelForm):
    class Meta:
        model = Marca
        fields = ['nombre', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la marca'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        
class MovimientoStockForm(forms.ModelForm):
    class Meta:
        model = MovimientoStock
        fields = ['tipo', 'cantidad', 'observacion']
        widgets = {
            'tipo': forms.Select(attrs={
                'class': 'form-select'
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'observacion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Motivo del movimiento'
            })
        }