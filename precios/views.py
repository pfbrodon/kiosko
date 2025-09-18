from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.core.cache import cache
from django.utils import timezone
from django.conf import settings
from usuarios.decorators import admin_o_encargado, solo_admin
from .models import Producto, Categoria, Proveedor, Subcategoria, Marca, MovimientoStock
from .forms import ProductoForm, ProductoSearchForm, SubcategoriaForm, CategoriaForm, ProveedorForm, MarcaForm, MovimientoStockForm
from .metrics import MetricasKiosko
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from io import BytesIO

# Función auxiliar para limpiar cache relacionado
def limpiar_cache_productos():
    """Limpia el cache relacionado con productos y métricas"""
    cache.delete_many([
        'dashboard_metricas_*',  # Esto no funciona con wildcards, así que vamos a mejorar
    ])
    # Alternativa: limpiar todo el cache
    cache.clear()
    print("🧹 Cache de productos y métricas limpiado")

# Importaciones de reportlab condicionales
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Create your views here.

@login_required
def home(request):
    return render(request, 'home.html')

@login_required 
def dashboard(request):
    """Vista del dashboard con métricas del negocio"""
    
    # Clave de cache única por usuario
    cache_key = f'dashboard_metricas_{request.user.id}'
    
    # Intentar obtener datos del cache
    metricas = cache.get(cache_key)
    
    if metricas is None:
        # Si no está en cache, calcular métricas
        print("🔄 Calculando métricas del dashboard...")
        metricas = MetricasKiosko.dashboard_completo()
        
        # Guardar en cache por 5 minutos
        cache.set(cache_key, metricas, timeout=getattr(settings, 'CACHE_TIMEOUT_DASHBOARD', 300))
        print("💾 Métricas guardadas en cache")
    else:
        print("⚡ Métricas obtenidas del cache")
    
    return render(request, 'dashboard.html', {
        'metricas': metricas
    })


#---------------------------------PRODUCTOS---------------------------------

@login_required
def lista_productos(request):
    from django.utils import timezone
    from datetime import timedelta
    from django.core.paginator import Paginator
    
    # 🚀 OPTIMIZACIÓN: Usar select_related y prefetch_related para evitar consultas N+1
    productos = Producto.objects.select_related(
        'subcategoria__categoria',  # Para acceso a categoría
        'proveedor',               # Para información del proveedor
        'marca'                    # Para información de marca
    ).prefetch_related(
        'historial_precios',       # Para cambios de precio
        'eventos'                  # Para eventos del sistema
    )
    
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
        if form.cleaned_data.get('estado') == 'N':
            # Filtrar productos nuevos (últimas 72 horas)
            fecha_limite = timezone.now() - timedelta(hours=72)
            productos = productos.filter(fecha_creacion__gte=fecha_limite)
        
        # Filtro por cambios de precio recientes
        if form.cleaned_data.get('precio_modificado'):
            horas = int(form.cleaned_data['precio_modificado'])
            fecha_limite = timezone.now() - timedelta(hours=horas)
            # Filtrar productos que tienen cambios en el período especificado
            productos_con_cambios = productos.filter(
                historial_precios__fecha_cambio__gte=fecha_limite
            ).distinct()
            productos = productos_con_cambios
    
    # � PAGINACIÓN: Mostrar 25 productos por página
    paginator = Paginator(productos, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # �📊 DEBUG: Mostrar cantidad de consultas (temporal)
    from django.db import connection
    initial_queries = len(connection.queries)
    
    # Renderizar template
    response = render(request, 'lista_productos.html', {
        'page_obj': page_obj,
        'productos': page_obj,  # Compatibilidad con template actual
        'form': form,
        'is_paginated': paginator.num_pages > 1,
        'total_productos': paginator.count
    })
    
    # 📊 DEBUG: Mostrar estadísticas de consultas
    final_queries = len(connection.queries)
    print(f"🔍 Consultas ejecutadas: {final_queries - initial_queries}")
    print(f"📦 Productos en página: {len(page_obj)}")
    print(f"📊 Total productos: {paginator.count}")
    print(f"📄 Página {page_obj.number} de {paginator.num_pages}")
    
    return response

@login_required
def busqueda_productos_ajax(request):
    """Vista AJAX para búsqueda rápida de productos"""
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'error': 'Solicitud no válida'}, status=400)
    
    query = request.GET.get('q', '').strip()
    categoria_id = request.GET.get('categoria')
    proveedor_id = request.GET.get('proveedor')
    
    if len(query) < 2:
        return JsonResponse({'productos': []})
    
    # Cache para búsquedas frecuentes
    cache_key = f'busqueda_{query}_{categoria_id}_{proveedor_id}'
    resultados = cache.get(cache_key)
    
    if resultados is None:
        productos = Producto.objects.select_related(
            'subcategoria__categoria', 'proveedor', 'marca'
        ).filter(
            Q(nombre__icontains=query) | 
            Q(descripcion__icontains=query) |
            Q(marca__nombre__icontains=query)
        )
        
        if categoria_id:
            productos = productos.filter(subcategoria__categoria_id=categoria_id)
        if proveedor_id:
            productos = productos.filter(proveedor_id=proveedor_id)
            
        productos = productos[:10]  # Limitar a 10 resultados
        
        resultados = [{
            'id': p.id,
            'nombre': p.nombre,
            'descripcion': p.descripcion or '',
            'precio': float(p.precio_venta_final),
            'stock': p.cantidad_stock,
            'categoria': p.subcategoria.categoria.nombre,
            'proveedor': p.proveedor.nombre if p.proveedor else ''
        } for p in productos]
        
        # Guardar en cache por 2 minutos
        cache.set(cache_key, resultados, timeout=120)
    
    return JsonResponse({'productos': resultados})

@login_required
def filtrar_productos_dinamico(request):
    """Vista AJAX para filtrado dinámico de productos con todos los filtros"""
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'error': 'Solicitud no válida'}, status=400)
    
    from django.utils import timezone
    from datetime import timedelta
    
    # Obtener parámetros de filtrado
    busqueda = request.GET.get('busqueda', '').strip()
    categoria_id = request.GET.get('categoria')
    subcategoria_id = request.GET.get('subcategoria')
    proveedor_id = request.GET.get('proveedor')
    estado = request.GET.get('estado')
    precio_modificado = request.GET.get('precio_modificado')
    page = int(request.GET.get('page', 1))
    
    # Base de productos con optimización
    productos = Producto.objects.select_related(
        'subcategoria__categoria',
        'proveedor',
        'marca'
    ).prefetch_related(
        'historial_precios',
        'eventos'
    )
    
    # Aplicar filtros
    if busqueda and len(busqueda) >= 1:
        productos = productos.filter(
            Q(nombre__icontains=busqueda) | 
            Q(descripcion__icontains=busqueda) |
            Q(marca__nombre__icontains=busqueda)
        )
    
    if categoria_id:
        productos = productos.filter(subcategoria__categoria_id=categoria_id)
    
    if subcategoria_id:
        productos = productos.filter(subcategoria_id=subcategoria_id)
    
    if proveedor_id:
        productos = productos.filter(proveedor_id=proveedor_id)
    
    if estado:
        if estado == '1':
            productos = productos.filter(activo=True)
        elif estado == '0':
            productos = productos.filter(activo=False)
        elif estado == 'B':
            productos = productos.filter(alerta_stock=True)
        elif estado == 'N':
            fecha_limite = timezone.now() - timedelta(hours=72)
            productos = productos.filter(fecha_creacion__gte=fecha_limite)
    
    if precio_modificado:
        try:
            horas = int(precio_modificado)
            fecha_limite = timezone.now() - timedelta(hours=horas)
            productos = productos.filter(
                historial_precios__fecha_cambio__gte=fecha_limite
            ).distinct()
        except ValueError:
            pass
    
    # Paginación
    from django.core.paginator import Paginator
    paginator = Paginator(productos, 25)
    page_obj = paginator.get_page(page)
    
    # Preparar datos para respuesta
    productos_data = []
    for producto in page_obj:
        # Verificar si el precio fue modificado recientemente
        precio_modificado_reciente = False
        if precio_modificado:
            try:
                horas = int(precio_modificado)
                fecha_limite = timezone.now() - timedelta(hours=horas)
                precio_modificado_reciente = producto.historial_precios.filter(
                    fecha_cambio__gte=fecha_limite
                ).exists()
            except:
                pass
        
        # Verificar si es producto nuevo
        es_nuevo = (timezone.now() - producto.fecha_creacion).total_seconds() < 72 * 3600
        
        productos_data.append({
            'id': producto.id,
            'nombre': producto.nombre,
            'descripcion': producto.descripcion or '',
            'marca': producto.marca.nombre if producto.marca else '',
            'categoria': producto.subcategoria.categoria.nombre,
            'subcategoria': producto.subcategoria.nombre,
            'proveedor': producto.proveedor.nombre if producto.proveedor else '',
            'precio_compra': float(producto.precio_compra_unitario) if producto.precio_compra_unitario else 0,
            'precio_venta': float(producto.precio_venta_final),
            'stock': producto.cantidad_stock,
            'stock_minimo': producto.stock_minimo,
            'descuento_compra': float(producto.descuento_compra) if producto.descuento_compra else 0,
            'activo': producto.activo,
            'alerta_stock': producto.alerta_stock,
            'precio_modificado': precio_modificado_reciente,
            'es_nuevo': es_nuevo,
            'fecha_creacion': producto.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
        })
    
    return JsonResponse({
        'productos': productos_data,
        'has_previous': page_obj.has_previous(),
        'has_next': page_obj.has_next(),
        'current_page': page_obj.number,
        'total_pages': paginator.num_pages,
        'total_productos': paginator.count,
        'start_index': page_obj.start_index(),
        'end_index': page_obj.end_index(),
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
            
            # Limpiar cache de productos y métricas
            limpiar_cache_productos()
            
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
            
            # Limpiar cache de productos y métricas
            limpiar_cache_productos()
            
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

@admin_o_encargado
def editar_categoria(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    
    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            limpiar_cache_productos()  # Limpiar cache por si afecta productos
            messages.success(request, f'Categoría "{categoria.nombre}" actualizada exitosamente.')
            return redirect('lista_categorias')
    else:
        form = CategoriaForm(instance=categoria)
    
    return render(request, 'editar_categoria.html', {
        'form': form, 
        'categoria': categoria
    })

@admin_o_encargado
def eliminar_categoria(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    
    # Verificar si la categoría tiene subcategorías asociadas
    subcategorias_count = categoria.subcategorias.count()
    
    # Verificar si hay productos asociados a través de subcategorías
    productos_count = 0
    for subcategoria in categoria.subcategorias.all():
        productos_count += subcategoria.producto_set.count()
    
    if request.method == 'POST':
        if subcategorias_count > 0 or productos_count > 0:
            messages.error(request, 
                f'No se puede eliminar la categoría "{categoria.nombre}" porque tiene '
                f'{subcategorias_count} subcategoría(s) y {productos_count} producto(s) asociado(s). '
                'Elimine primero las subcategorías y productos relacionados.'
            )
        else:
            nombre_categoria = categoria.nombre
            categoria.delete()
            limpiar_cache_productos()  # Limpiar cache
            messages.success(request, f'Categoría "{nombre_categoria}" eliminada exitosamente.')
        
        return redirect('lista_categorias')
    
    return render(request, 'confirmar_eliminar_categoria.html', {
        'categoria': categoria,
        'subcategorias_count': subcategorias_count,
        'productos_count': productos_count,
        'puede_eliminar': subcategorias_count == 0 and productos_count == 0
    })



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

@login_required
def lista_precios_pdf(request):
    if not REPORTLAB_AVAILABLE:
        messages.error(request, 'ReportLab no está disponible. No se puede generar el PDF.')
        return redirect('lista_productos')
    
    from .models import Subcategoria
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin_x = 30
    gutter = 18  # espacio entre columnas
    col_width = (width - 2 * margin_x - gutter) / 2
    col_positions = [margin_x, margin_x + col_width + gutter]
    y_start = height - 30
    y = y_start
    col = 0
    p.setFont("Helvetica-Bold", 16)
    p.drawString(margin_x, y, "Lista de Precios")
    y -= 30
    p.setFont("Helvetica", 11)
    subcategorias = Subcategoria.objects.all().order_by('nombre')
    for subcat in subcategorias:
        productos = subcat.productos.all().order_by('nombre')
        if not productos:
            continue
        if y < 80:
            col += 1
            if col > 1:
                p.showPage()
                col = 0
            y = y_start
        x = col_positions[col]
        p.setFont("Helvetica-Bold", 12)
        p.setFillColor(colors.HexColor('#0d6efd'))
        p.drawString(x, y, subcat.nombre)
        y -= 18
        p.setFont("Helvetica-Bold", 11)
        p.setFillColor(colors.black)
        p.drawString(x + 5, y, "Producto")
        p.drawRightString(x + col_width - 5, y, "Precio Venta al Público")
        y -= 14
        p.setFont("Helvetica", 10)
        for producto in productos:
            if y < 50:
                col += 1
                if col > 1:
                    p.showPage()
                    col = 0
                y = y_start
                x = col_positions[col]
                p.setFont("Helvetica-Bold", 12)
                p.setFillColor(colors.HexColor('#0d6efd'))
                p.drawString(x, y, subcat.nombre + " (cont.)")
                y -= 18
                p.setFont("Helvetica-Bold", 11)
                p.setFillColor(colors.black)
                p.drawString(x + 5, y, "Producto")
                p.drawRightString(x + col_width - 5, y, "Precio Venta al Público")
                y -= 14
                p.setFont("Helvetica", 10)
            p.drawString(x + 5, y, producto.nombre[:38])  # recorta si es muy largo
            p.drawRightString(x + col_width - 5, y, f"${producto.precio_venta_final:.2f}")
            y -= 13
        y -= 10
    p.save()
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')

@login_required
def productos_filtrados_pdf(request):
    """Genera PDF con productos filtrados según los parámetros enviados"""
    if not REPORTLAB_AVAILABLE:
        messages.error(request, 'ReportLab no está disponible. No se puede generar el PDF.')
        return redirect('lista_productos')
    
    from django.utils import timezone
    from datetime import timedelta
    
    # Obtener parámetros de filtrado (mismos que filtrar_productos_dinamico)
    busqueda = request.GET.get('busqueda', '').strip()
    categoria_id = request.GET.get('categoria')
    subcategoria_id = request.GET.get('subcategoria')
    proveedor_id = request.GET.get('proveedor')
    estado = request.GET.get('estado')
    precio_modificado = request.GET.get('precio_modificado')
    
    # Aplicar filtros (mismo código que filtrar_productos_dinamico)
    productos = Producto.objects.select_related(
        'subcategoria__categoria',
        'proveedor',
        'marca'
    ).prefetch_related(
        'historial_precios',
        'eventos'
    )
    
    # Variables para título del PDF
    filtros_aplicados = []
    
    if busqueda and len(busqueda) >= 1:
        productos = productos.filter(
            Q(nombre__icontains=busqueda) | 
            Q(descripcion__icontains=busqueda) |
            Q(marca__nombre__icontains=busqueda)
        )
        filtros_aplicados.append(f'Búsqueda: "{busqueda}"')
    
    if categoria_id:
        productos = productos.filter(subcategoria__categoria_id=categoria_id)
        categoria = get_object_or_404(Categoria, id=categoria_id)
        filtros_aplicados.append(f'Categoría: {categoria.nombre}')
    
    if subcategoria_id:
        productos = productos.filter(subcategoria_id=subcategoria_id)
        subcategoria = get_object_or_404(Subcategoria, id=subcategoria_id)
        filtros_aplicados.append(f'Subcategoría: {subcategoria.nombre}')
    
    if proveedor_id:
        productos = productos.filter(proveedor_id=proveedor_id)
        proveedor = get_object_or_404(Proveedor, id=proveedor_id)
        filtros_aplicados.append(f'Proveedor: {proveedor.nombre}')
    
    if estado:
        if estado == '1':
            productos = productos.filter(activo=True)
            filtros_aplicados.append('Estado: Activos')
        elif estado == '0':
            productos = productos.filter(activo=False)
            filtros_aplicados.append('Estado: Inactivos')
        elif estado == 'B':
            productos = productos.filter(alerta_stock=True)
            filtros_aplicados.append('Estado: Stock Bajo')
        elif estado == 'N':
            fecha_limite = timezone.now() - timedelta(hours=72)
            productos = productos.filter(fecha_creacion__gte=fecha_limite)
            filtros_aplicados.append('Estado: Productos Nuevos')
    
    if precio_modificado:
        try:
            horas = int(precio_modificado)
            fecha_limite = timezone.now() - timedelta(hours=horas)
            productos = productos.filter(
                historial_precios__fecha_cambio__gte=fecha_limite
            ).distinct()
            filtros_aplicados.append(f'Precio modificado: últimas {horas} horas')
        except ValueError:
            pass
    
    # Ordenar productos por categoría, subcategoría y nombre
    productos = productos.order_by(
        'subcategoria__categoria__nombre',
        'subcategoria__nombre', 
        'nombre'
    )
    
    # Crear PDF
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin_x = 30
    margin_y = 30
    y_start = height - margin_y
    y = y_start
    
    # Título
    p.setFont("Helvetica-Bold", 16)
    p.drawString(margin_x, y, "Lista de Productos Filtrados")
    y -= 25
    
    # Información de filtros aplicados
    if filtros_aplicados:
        p.setFont("Helvetica-Bold", 10)
        p.drawString(margin_x, y, "Filtros aplicados:")
        y -= 15
        p.setFont("Helvetica", 9)
        for filtro in filtros_aplicados[:5]:  # Máximo 5 filtros para que quepa
            p.drawString(margin_x + 10, y, f"• {filtro}")
            y -= 12
    else:
        p.setFont("Helvetica", 10)
        p.drawString(margin_x, y, "Todos los productos")
        y -= 15
    
    # Información de resultados
    total_productos = productos.count()
    p.setFont("Helvetica-Bold", 10)
    p.drawString(margin_x, y, f"Total de productos: {total_productos}")
    y -= 20
    
    # Fecha de generación
    from django.utils import timezone
    fecha_actual = timezone.now().strftime('%d/%m/%Y %H:%M')
    p.setFont("Helvetica", 8)
    p.drawString(margin_x, y, f"Generado el: {fecha_actual}")
    y -= 25
    
    if not productos.exists():
        p.setFont("Helvetica", 12)
        p.drawString(margin_x, y, "No se encontraron productos con los filtros aplicados.")
        p.save()
        buffer.seek(0)
        return HttpResponse(buffer, content_type='application/pdf')
    
    # Cabeceras de tabla
    p.setFont("Helvetica-Bold", 10)
    col_x = [margin_x, margin_x + 200, margin_x + 320, margin_x + 420, margin_x + 480]
    headers = ["Producto", "Categoría", "Subcategoría", "Stock", "Precio"]
    
    for i, header in enumerate(headers):
        p.drawString(col_x[i], y, header)
    
    y -= 15
    
    # Línea separadora
    p.line(margin_x, y, width - margin_x, y)
    y -= 10
    
    # Productos
    p.setFont("Helvetica", 9)
    categoria_actual = None
    
    for producto in productos:
        # Verificar si necesitamos una nueva página
        if y < 50:
            p.showPage()
            y = y_start
            
            # Repetir cabeceras en nueva página
            p.setFont("Helvetica-Bold", 10)
            for i, header in enumerate(headers):
                p.drawString(col_x[i], y, header)
            y -= 15
            p.line(margin_x, y, width - margin_x, y)
            y -= 10
            p.setFont("Helvetica", 9)
        
        # Separador por categoría
        if categoria_actual != producto.subcategoria.categoria.nombre:
            categoria_actual = producto.subcategoria.categoria.nombre
            p.setFont("Helvetica-Bold", 9)
            p.setFillColor(colors.HexColor('#0d6efd'))
            p.drawString(margin_x, y, f"CATEGORÍA: {categoria_actual}")
            p.setFillColor(colors.black)
            y -= 15
            p.setFont("Helvetica", 9)
        
        # Datos del producto
        nombre_producto = producto.nombre[:35] + "..." if len(producto.nombre) > 35 else producto.nombre
        
        # Verificar si es producto nuevo
        es_nuevo = (timezone.now() - producto.fecha_creacion).total_seconds() < 72 * 3600
        
        # Colorear si tiene alerta de stock
        if producto.alerta_stock:
            p.setFillColor(colors.red)
        elif es_nuevo:
            p.setFillColor(colors.HexColor('#28a745'))
        else:
            p.setFillColor(colors.black)
        
        p.drawString(col_x[0], y, nombre_producto)
        p.drawString(col_x[1], y, producto.subcategoria.categoria.nombre[:15])
        p.drawString(col_x[2], y, producto.subcategoria.nombre[:15])
        p.drawString(col_x[3], y, str(producto.cantidad_stock))
        p.drawRightString(col_x[4] + 40, y, f"${producto.precio_venta_final:.2f}")
        
        p.setFillColor(colors.black)  # Resetear color
        y -= 12
    
    # Pie de página
    y = 30
    p.setFont("Helvetica", 8)
    p.drawString(margin_x, y, f"Página generada desde Sistema de Kiosko - {fecha_actual}")
    
    p.save()
    buffer.seek(0)
    
    # Nombre del archivo basado en filtros
    filename = "productos"
    if busqueda:
        filename += f"_busqueda_{busqueda[:10]}"
    if categoria_id:
        filename += f"_cat{categoria_id}"
    if estado:
        filename += f"_estado{estado}"
    filename += f"_{timezone.now().strftime('%Y%m%d_%H%M')}.pdf"
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

@login_required
def test_pdf_simple(request):
    """Vista de prueba simple para verificar que el PDF funciona"""
    if not REPORTLAB_AVAILABLE:
        return HttpResponse("ReportLab no está disponible", content_type="text/plain")
    
    # Crear PDF simple
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    p.setFont("Helvetica-Bold", 20)
    p.drawString(100, height - 100, "Prueba de PDF")
    p.setFont("Helvetica", 12)
    p.drawString(100, height - 150, "Si ves esto, el PDF funciona correctamente")
    p.drawString(100, height - 180, f"Generado el: {timezone.now().strftime('%d/%m/%Y %H:%M')}")
    
    # Parámetros de prueba
    params = dict(request.GET.items())
    if params:
        p.drawString(100, height - 220, "Parametros recibidos:")
        y = height - 250
        for key, value in params.items():
            p.drawString(120, y, f"{key}: {value}")
            y -= 20
    else:
        p.drawString(100, height - 220, "No se recibieron parametros")
    
    p.save()
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="test_pdf.pdf"'
    return response