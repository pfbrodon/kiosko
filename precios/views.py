from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Producto, Categoria, Proveedor, Subcategoria, Marca
from .forms import ProductoForm, ProductoSearchForm, SubcategoriaForm, CategoriaForm, ProveedorForm, MarcaForm
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from datetime import datetime
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

#---------------------------------PDF EXPORT---------------------------------

def exportar_productos_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="lista_productos.pdf"'
    
    # Usar orientación vertical
    doc = SimpleDocTemplate(
        response,
        pagesize=letter,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )
    
    elements = []
    
    # Obtener los productos
    productos = Producto.objects.all().order_by('nombre')
    
    # Estilos para el texto
    styles = getSampleStyleSheet()
    styleN = styles["BodyText"]
    
    # Datos para la tabla con menos columnas
    data = [[
        'Nombre',
        'Marca',
        'Subcategoría',
        'Proveedor',
        'Precio',
        'Estado'
    ]]
    
    # Agregar datos de productos (omitiendo categoría, precio compra y descuento)
    for producto in productos:
        data.append([
            Paragraph(producto.nombre, styleN),
            Paragraph(str(producto.marca) if producto.marca else "Sin marca", styleN),
            Paragraph(str(producto.subcategoria), styleN),
            Paragraph(str(producto.proveedor), styleN),
            f"${producto.precio_venta_final:.2f}",
            "Activo" if producto.activo else "Inactivo"
        ])
    
    # Definir anchos de columna (en porcentaje del ancho disponible)
    col_widths = [
        doc.width * 0.25,  # Nombre
        doc.width * 0.15,  # Marca
        doc.width * 0.20,  # Subcategoría
        doc.width * 0.20,  # Proveedor
        doc.width * 0.10,  # Precio Venta
        doc.width * 0.10   # Estado
    ]
    
    # Crear tabla con los anchos definidos
    table = Table(data, colWidths=col_widths, repeatRows=1)
    
    # Estilo de la tabla
    table.setStyle(TableStyle([
        # Estilo del encabezado
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        
        # Estilo del contenido
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        
        # Alineación especial para precios
        ('ALIGN', (4, 1), (4, -1), 'RIGHT'),  # Precio alineado a la derecha
        
        # Espaciado
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        
        # Separación entre filas
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.lightgrey]),
    ]))
    
    # Agregar fecha de generación
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    elementos_header = [
        Paragraph(f"Lista de Productos - Generado: {fecha}", styles['Heading1']),
        table
    ]
    
    doc.build(elementos_header)
    return response