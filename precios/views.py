from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Producto, Categoria, Proveedor, Subcategoria, Marca
from .forms import ProductoForm, ProductoSearchForm, SubcategoriaForm, CategoriaForm, ProveedorForm, MarcaForm

# Create your views here.

def home(request):
    return render(request, 'home.html')


#---------------------------------PRODUCTOS---------------------------------


def crear_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto creado exitosamente.')
            return redirect('lista_productos')
    else:
        form = ProductoForm()
    return render(request, 'crear_producto.html', {'form': form})

def editar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto actualizado exitosamente.')
            return redirect('lista_productos')
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'crear_producto.html', {
        'form': form,
        'editing': True,
        'producto': producto
    })

def eliminar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        producto.delete()
        messages.success(request, f'El producto {producto.nombre} ha sido eliminado.')
    return redirect('lista_productos')

def lista_productos(request):
    productos = Producto.objects.all()
    form = ProductoSearchForm(request.GET)
    
    if form.is_valid():
        if form.cleaned_data['categoria']:
            productos = productos.filter(subcategoria__categoria=form.cleaned_data['categoria'])
        if form.cleaned_data['subcategoria']:
            productos = productos.filter(subcategoria=form.cleaned_data['subcategoria'])
        if form.cleaned_data['proveedor']:
            productos = productos.filter(proveedor=form.cleaned_data['proveedor'])
        if form.cleaned_data['estado']:
            estado = form.cleaned_data['estado'] == '1'
            productos = productos.filter(activo=estado)
        if form.cleaned_data['busqueda']:
            productos = productos.filter(nombre__icontains=form.cleaned_data['busqueda'])
        if form.cleaned_data.get('estado') == 'B':
            productos = productos.filter(alerta_stock=True)
    
    return render(request, 'lista_productos.html', {
        'productos': productos,
        'form': form
    })
    

#---------------------------------SUBCATEGORIAS---------------------------------
    
def lista_subcategorias(request):
    subcategorias = Subcategoria.objects.all().select_related('categoria')
    return render(request, 'lista_subcategorias.html', {
        'subcategorias': subcategorias
    })
def crear_subcategoria(request):
    if request.method == 'POST':
        form = SubcategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subcategoría creada exitosamente.')
            return redirect('lista_productos')
    else:
        form = SubcategoriaForm()
    return render(request, 'crear_subcategoria.html', {'form': form})


#---------------------------------CATEGORIAS---------------------------------

def lista_categorias(request):
    categorias = Categoria.objects.all().order_by('nombre')
    return render(request, 'categorias.html', {'categorias': categorias})

def crear_categoria(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría creada exitosamente.')
            return redirect('lista_categorias')
    else:
        form = CategoriaForm()
    return render(request, 'crear_categoria.html', {'form': form})



#---------------------------------PROVEEDORES---------------------------------

def lista_proveedores(request):
    proveedor = Proveedor.objects.all().order_by('nombre')
    return render(request, 'proveedores.html', {'proveedor': proveedor})

def crear_proveedor(request):
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Proveedor creado exitosamente.')
            return redirect('lista_proveedores')
    else:
        form = ProveedorForm()
    return render(request, 'crear_proveedor.html', {'form': form})


#---------------------------------MARCAS---------------------------------


def lista_marcas(request):
    marcas = Marca.objects.all()
    return render(request, 'lista_marcas.html', {'marcas': marcas})

def crear_marca(request):
    if request.method == 'POST':
        form = MarcaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Marca creada exitosamente.')
            return redirect('lista_marcas')
    else:
        form = MarcaForm()
    return render(request, 'crear_marca.html', {'form': form})

def editar_marca(request, pk):
    marca = get_object_or_404(Marca, pk=pk)
    if request.method == 'POST':
        form = MarcaForm(request.POST, instance=marca)
        if form.is_valid():
            form.save()
            messages.success(request, 'Marca actualizada exitosamente.')
            return redirect('lista_marcas')
    else:
        form = MarcaForm(instance=marca)
    return render(request, 'crear_marca.html', {
        'form': form,
        'editing': True,
        'marca': marca
    })
def eliminar_marca(request, pk):
    marca = get_object_or_404(Marca, pk=pk)
    if request.method == 'POST':
        marca.delete()
        messages.success(request, f'La marca {marca.nombre} ha sido eliminada.')
    return redirect('lista_marcas')
