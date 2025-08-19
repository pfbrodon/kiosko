from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from usuarios.decorators import admin_o_encargado, solo_admin
from .models import Producto, Categoria, Proveedor, Subcategoria, Marca, MovimientoStock
from .forms import ProductoForm, ProductoSearchForm, SubcategoriaForm, CategoriaForm, ProveedorForm, MarcaForm, MovimientoStockForm

# Create your views here.

@login_required
def home(request):
    return render(request, 'home.html')


#---------------------------------PRODUCTOS---------------------------------

@login_required
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

@admin_o_encargado
def crear_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save(commit=False)
            stock_inicial = form.cleaned_data.get('stock_inicial', 0)
            producto.cantidad_stock = stock_inicial
            producto.save()
            
            # Crear el movimiento de stock inicial si es mayor a 0
            if stock_inicial > 0:
                MovimientoStock.objects.create(
                    producto=producto,
                    tipo='E',
                    cantidad=stock_inicial,
                    observacion='Stock inicial'
                )
            
            messages.success(request, 'Producto creado exitosamente.')
            return redirect('lista_productos')
    else:
        form = ProductoForm()
    return render(request, 'crear_producto.html', {
        'form': form,
        'editing': False
    })

@admin_o_encargado
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

@solo_admin
def eliminar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        producto.delete()
        messages.success(request, f'El producto {producto.nombre} ha sido eliminado.')
    return redirect('lista_productos')

@login_required
def movimientos_stock(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    movimientos = MovimientoStock.objects.filter(producto=producto)
    
    if request.method == 'POST':
        form = MovimientoStockForm(request.POST)
        if form.is_valid():
            movimiento = form.save(commit=False)
            movimiento.producto = producto
            
            # Validar y actualizar stock
            cantidad = form.cleaned_data['cantidad']
            if movimiento.tipo == 'S' and cantidad > producto.cantidad_stock:
                messages.error(request, 'No hay suficiente stock disponible')
                return redirect('movimientos_stock', pk=pk)
            
            # Actualizar stock
            if movimiento.tipo == 'E':
                producto.cantidad_stock += cantidad
            else:
                producto.cantidad_stock -= cantidad
            
            movimiento.save()
            producto.save()
            
            messages.success(request, f'Stock actualizado: {producto.cantidad_stock} unidades')
            return redirect('movimientos_stock', pk=pk)
    else:
        form = MovimientoStockForm()
    
    return render(request, 'movimientos_stock.html', {
        'producto': producto,
        'movimientos': movimientos,
        'form': form
    })

#---------------------------------SUBCATEGORIAS---------------------------------

@login_required    
def lista_subcategorias(request):
    subcategorias = Subcategoria.objects.all().select_related('categoria')
    return render(request, 'lista_subcategorias.html', {
        'subcategorias': subcategorias
    })

@admin_o_encargado
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

@login_required
def lista_categorias(request):
    categorias = Categoria.objects.all().order_by('nombre')
    return render(request, 'categorias.html', {'categorias': categorias})

@admin_o_encargado
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

@login_required
def lista_proveedores(request):
    proveedor = Proveedor.objects.all().order_by('nombre')
    return render(request, 'proveedores.html', {'proveedor': proveedor})

@admin_o_encargado
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

@login_required
def editar_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    
    if request.method == 'POST':
        form = ProveedorForm(request.POST, instance=proveedor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Proveedor actualizado correctamente')
            return redirect('lista_proveedores')
    else:
        form = ProveedorForm(instance=proveedor)
    
    return render(request, 'editar_proveedor.html', {
        'form': form,
        'proveedor': proveedor
    })

@solo_admin
def eliminar_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    
    if request.method == 'POST':
        proveedor.delete()
        messages.success(request, 'Proveedor eliminado correctamente')
        return redirect('lista_proveedores')
    
    return render(request, 'confirmar_eliminar_proveedor.html', {
        'proveedor': proveedor
    })

#---------------------------------MARCAS---------------------------------

@login_required
def lista_marcas(request):
    marcas = Marca.objects.all()
    return render(request, 'lista_marcas.html', {'marcas': marcas})

@admin_o_encargado
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

@admin_o_encargado
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

@solo_admin
def eliminar_marca(request, pk):
    marca = get_object_or_404(Marca, pk=pk)
    if request.method == 'POST':
        marca.delete()
        messages.success(request, f'La marca {marca.nombre} ha sido eliminada.')
    return redirect('lista_marcas')