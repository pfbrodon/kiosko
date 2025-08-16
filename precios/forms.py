from django import forms
from .models import Categoria, Subcategoria, Proveedor, Producto, Marca

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            'subcategoria',
            'proveedor',
            'marca',
            'nombre',
            'descripcion',
            'tipo_compra',
            'unidades_por_paquete',
            'precio_compra_paquete',
            'descuento_compra',
            'tipo_venta',
            'margen_ganancia',
            'precio_venta_final',
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'precio_compra_paquete': forms.NumberInput(attrs={'step': '0.01'}),
            'descuento_compra': forms.NumberInput(attrs={'step': '0.01'}),
            'margen_ganancia': forms.NumberInput(attrs={'step': '0.01'}),
            'precio_venta_final': forms.NumberInput(attrs={'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Agregar clases de Bootstrap
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
            
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
        ('0', 'Inactivos')
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
        fields = ['nombre', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del proveedor'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
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