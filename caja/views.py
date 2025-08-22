from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from .models import SaldoGeneral, CajaDiaria, Recreo, EventoEspecial, PagoProveedor
from .forms import InicioCajaForm, InicioCajaExtraForm, RecreoForm, EventoEspecialForm, PagoProveedorForm
from django import forms
from usuarios.decorators import solo_admin, admin_o_encargado
from django.shortcuts import get_object_or_404

class SaldoGeneralForm(forms.Form):
    monto = forms.DecimalField(
        max_digits=10, 
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01'
        })
    )
    tipo_operacion = forms.ChoiceField(
        choices=[
            ('establecer', 'Establecer nuevo saldo'),
            ('sumar', 'Sumar al saldo actual'),
            ('restar', 'Restar al saldo actual')
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

@login_required
def lista_cajas(request):
    import datetime
    from itertools import groupby
    from operator import attrgetter
    
    today = datetime.date.today()
    
    saldo_general = SaldoGeneral.objects.first()
    if not saldo_general:
        saldo_general = SaldoGeneral.objects.create()
    
    # Obtenemos el filtro de fecha si existe
    fecha_filtro = request.GET.get('fecha')
    
    # Obtenemos fechas únicas para el dropdown del filtro
    fechas_disponibles = CajaDiaria.objects.values_list('fecha', flat=True).distinct().order_by('-fecha')
    
    # Obtenemos todas las cajas ordenadas por fecha (descendente)
    cajas_query = CajaDiaria.objects.all()
    
    # Aplicamos filtro si existe
    if fecha_filtro:
        try:
            fecha_filtro = datetime.datetime.strptime(fecha_filtro, '%Y-%m-%d').date()
            cajas_query = cajas_query.filter(fecha=fecha_filtro)
        except (ValueError, TypeError):
            # Si hay un error en el formato de fecha, ignoramos el filtro
            pass
    
    cajas = cajas_query.order_by('-fecha', 'turno', 'nivel', 'es_extra')
    
    # Agrupar cajas por fecha
    cajas_por_fecha = []
    for fecha, grupo in groupby(cajas, key=attrgetter('fecha')):
        cajas_grupo = list(grupo)
        cajas_por_fecha.append({
            'fecha': fecha,
            'cajas': cajas_grupo,
            'es_hoy': fecha == today
        })
    
    # Verificar si hay cajas abiertas (en proceso)
    hay_cajas_abiertas = cajas.filter(cerrada=False).exists()
    
    # Verificar si hay al menos una caja cerrada
    hay_alguna_caja_cerrada = cajas.filter(cerrada=True).exists()
    
    # Calcular saldo parcial total
    # Primero, obtenemos todas las cajas abiertas
    cajas_abiertas = cajas.filter(cerrada=False)
    
    # Inicializamos variables
    saldo_inicial_total = Decimal('0')  # Importante para cajas secundarias
    ingresos_total = Decimal('0')
    egresos_total = Decimal('0')
    
    # Para cada caja abierta, calculamos sus componentes
    for caja in cajas_abiertas:
        # Sumamos el saldo inicial (importante para secundarias)
        if caja.nivel == 'S':
            saldo_inicial_total += caja.saldo_inicial
        
        # Sumamos todos los ingresos (recreos + eventos)
        ingresos_total += caja.get_total_ingresos()
        
        # Sumamos todos los pagos
        total_pagos = caja.pagoproveedor_set.aggregate(
            total=Sum('monto'))['total'] or Decimal('0')
        egresos_total += total_pagos
    
    # Calculamos el saldo parcial total como en la vista de registrar_movimientos
    saldo_parcial = saldo_inicial_total + ingresos_total - egresos_total
    
    # Verificar si hay cajas cerradas hoy disponibles para crear cajas extra
    hay_cajas_extras_disponibles = False
    cajas_cerradas_hoy = CajaDiaria.objects.filter(
        fecha=today,
        cerrada=True,
        es_extra=False
    )
    
    for caja in cajas_cerradas_hoy:
        # Verificar si ya existe una caja extra para esta combinación de turno y nivel
        if not CajaDiaria.objects.filter(
            fecha=today,
            turno=caja.turno,
            nivel=caja.nivel,
            es_extra=True
        ).exists():
            hay_cajas_extras_disponibles = True
            break
    
    return render(request, 'lista_cajas.html', {
        'saldo_general': saldo_general,
        'saldo_parcial': saldo_parcial,
        'cajas_por_fecha': cajas_por_fecha,
        'hay_cajas_extras_disponibles': hay_cajas_extras_disponibles,
        'hay_cajas_abiertas': hay_cajas_abiertas,
        'hay_alguna_caja_cerrada': hay_alguna_caja_cerrada,
        'today': today,
        'fechas_disponibles': fechas_disponibles,
        'fecha_filtro': fecha_filtro
    })

@admin_o_encargado
def iniciar_caja(request):
    """Vista para iniciar una caja normal"""
    import datetime
    today = datetime.date.today()
    
    # Verificar si hay cajas abiertas (en proceso)
    hay_cajas_abiertas = CajaDiaria.objects.filter(cerrada=False).exists()
    if hay_cajas_abiertas:
        messages.error(request, "No se puede iniciar una nueva caja mientras haya cajas en proceso")
        return redirect('caja:lista_cajas')
    
    saldo_general = SaldoGeneral.objects.first()
    if not saldo_general:
        saldo_general = SaldoGeneral.objects.create()
    
    if request.method == 'POST':
        form = InicioCajaForm(request.POST)
        if form.is_valid():
            # Crear y guardar la caja normal
            caja = form.save(commit=False)
            caja.es_extra = False  # Asegurarnos que sea caja normal
            
            # Solo asignar saldo inicial si es caja secundaria
            if caja.nivel == 'S':
                caja.saldo_inicial = saldo_general.monto
            else:
                caja.saldo_inicial = Decimal('0')
                
            try:
                caja.save()  # Intentar guardar la caja
                messages.success(request, 'Caja iniciada correctamente')
                return redirect('caja:registrar_movimientos', caja_id=caja.id)
            except ValidationError as e:
                form.add_error(None, e)  # Añadir error al formulario
            except Exception as e:
                messages.error(request, f"Error inesperado: {str(e)}")
    else:
        form = InicioCajaForm()
    
    return render(request, 'iniciar_caja.html', {
        'form': form,
        'saldo_general': saldo_general,
        'es_caja_extra': False,
        'today': today
    })

@admin_o_encargado
def iniciar_caja_extra(request):
    """Vista para iniciar una caja extra"""
    import datetime
    today = datetime.date.today()
    
    saldo_general = SaldoGeneral.objects.first()
    if not saldo_general:
        saldo_general = SaldoGeneral.objects.create()
    
    # Verificar si hay cajas cerradas hoy disponibles
    cajas_cerradas_hoy = CajaDiaria.objects.filter(
        fecha=today,
        cerrada=True,
        es_extra=False
    ).order_by('turno', 'nivel')
    
    # Si no hay cajas cerradas disponibles, mostrar error y redirigir
    if not cajas_cerradas_hoy.exists():
        messages.error(request, f"No hay cajas cerradas del día actual disponibles para crear cajas extras")
        return redirect('caja:lista_cajas')
    
    # Buscar todas las cajas normales cerradas hoy que podrían tener una caja extra
    cajas_disponibles = []
    for caja in cajas_cerradas_hoy:
        # Verificar si ya existe una caja extra para esta
        if not CajaDiaria.objects.filter(
            fecha=today,
            turno=caja.turno,
            nivel=caja.nivel,
            es_extra=True
        ).exists():
            cajas_disponibles.append({
                'turno': caja.get_turno_display(),
                'nivel': caja.get_nivel_display(),
                'turno_valor': caja.turno,
                'nivel_valor': caja.nivel
            })
    
    # Si no hay cajas disponibles (todas tienen ya una caja extra), mostrar error
    if not cajas_disponibles:
        messages.error(request, "Todas las cajas cerradas de hoy ya tienen una caja extra asociada")
        return redirect('caja:lista_cajas')
    
    if request.method == 'POST':
        # Usar el formulario específico para cajas extra (sin campo fecha)
        form = InicioCajaExtraForm(request.POST)
        if form.is_valid():
            # Crear la caja extra con la fecha de hoy fija
            caja = form.save(commit=False)
            caja.fecha = today  # Fecha fija de hoy
            caja.es_extra = True  # Siempre es una caja extra
            caja.saldo_inicial = Decimal('0')  # Saldo inicial siempre 0
            
            # Verificar que exista la caja normal cerrada correspondiente
            caja_normal_cerrada = CajaDiaria.objects.filter(
                fecha=today,
                turno=caja.turno,
                nivel=caja.nivel,
                cerrada=True,
                es_extra=False
            ).exists()
            
            if not caja_normal_cerrada:
                form.add_error(None, "No existe una caja cerrada para el turno y nivel seleccionado")
            else:
                try:
                    caja.save()
                    messages.success(request, 'Caja extra iniciada correctamente')
                    return redirect('caja:registrar_movimientos', caja_id=caja.id)
                except ValidationError as e:
                    form.add_error(None, e)
                except Exception as e:
                    messages.error(request, f"Error inesperado: {str(e)}")
    else:
        # Preparar formulario inicial
        initial_data = {}
        # Preseleccionar turno y nivel de la primera caja cerrada disponible
        if cajas_disponibles:
            primera_caja = cajas_cerradas_hoy.filter(
                turno=cajas_disponibles[0]['turno_valor'],
                nivel=cajas_disponibles[0]['nivel_valor']
            ).first()
            if primera_caja:
                initial_data['turno'] = primera_caja.turno
                initial_data['nivel'] = primera_caja.nivel
        
        form = InicioCajaExtraForm(initial=initial_data)
    
    return render(request, 'iniciar_caja_extra.html', {
        'form': form,
        'saldo_general': saldo_general,
        'cajas_disponibles': cajas_disponibles,
        'today': today
    })

@login_required
def registrar_movimientos(request, caja_id):
    caja = get_object_or_404(CajaDiaria, id=caja_id)
    saldo_general = SaldoGeneral.objects.first()
    if not saldo_general:
        saldo_general = SaldoGeneral.objects.create()
    
    # Determinar si es una caja extra
    es_caja_extra = caja.es_extra
    
    # Obtener los recreos existentes
    recreos = Recreo.objects.filter(caja=caja).order_by('numero')
    
    # Para cajas normales: próximo recreo disponible
    # Para cajas extras: verificar si ya existe un ingreso extra
    if es_caja_extra:
        # En cajas extras solo permitimos un ingreso
        proximo_recreo = None if recreos.exists() else 1
    else:
        # En cajas normales, comportamiento original
        proximo_recreo = 1
        if recreos.exists():
            ultimo_recreo = recreos.last()
            if ultimo_recreo.numero < 3:
                proximo_recreo = ultimo_recreo.numero + 1
            else:
                proximo_recreo = None
    
    if request.method == 'POST':
        if 'agregar_recreo' in request.POST:
            form = RecreoForm(request.POST)
            if form.is_valid():
                recreo = form.save(commit=False)
                recreo.caja = caja
                
                # Para cajas extras, siempre usar número 1
                if es_caja_extra:
                    recreo.numero = 1
                    
                try:
                    recreo.full_clean()
                    recreo.save()
                    caja.actualizar_saldo_parcial()
                    mensaje = 'Ingreso Extra registrado correctamente' if es_caja_extra else 'Recreo registrado correctamente'
                    messages.success(request, mensaje)
                    # Redirigir a la página actual para que se actualice el saldo parcial
                    return redirect('caja:registrar_movimientos', caja_id=caja.id)
                except ValidationError as e:
                    messages.error(request, e.messages[0])
        
        elif 'agregar_evento' in request.POST and not caja.es_extra:
            # Solo permitir eventos especiales en cajas normales, no en cajas extras
            descripcion = request.POST.get('descripcion_evento')
            monto = Decimal(request.POST.get('monto_evento', '0'))
            
            EventoEspecial.objects.create(
                caja=caja,
                descripcion=descripcion,
                monto=monto
            )
            caja.actualizar_saldo_parcial()
            messages.success(request, 'Evento especial registrado correctamente')
            # Redirigir a la página actual para que se actualice el saldo parcial
            return redirect('caja:registrar_movimientos', caja_id=caja.id)
        
        elif 'agregar_pago' in request.POST and (caja.nivel == 'S' and not (caja.es_extra and caja.nivel == 'P')):
            # Solo permitir pagos en cajas secundarias (normal o extra) o primaria normal
            form = PagoProveedorForm(request.POST)
            if form.is_valid():
                pago = form.save(commit=False)
                pago.caja = caja
                pago.save()
                caja.actualizar_saldo_parcial()
                messages.success(request, 'Pago registrado correctamente')
                # Redirigir a la página actual para que se actualice el saldo parcial
                return redirect('caja:registrar_movimientos', caja_id=caja.id)
        
        elif 'cerrar_caja' in request.POST:
            # Antes de cerrar la caja, calculamos el saldo parcial final
            caja.actualizar_saldo_parcial()
            
            # Al cerrar la caja, actualizamos el saldo general
            saldo_diferencia = caja.saldo_parcial - caja.saldo_inicial
            saldo_general.monto += saldo_diferencia
            saldo_general.save()
            
            caja.cerrada = True
            caja.save()
            
            mensaje = 'Caja extra cerrada correctamente' if caja.es_extra else 'Caja cerrada correctamente'
            messages.success(request, mensaje)
            return redirect('caja:lista_cajas')
        
        return redirect('caja:registrar_movimientos', caja_id=caja.id)

    # Antes de mostrar la página, calculamos el saldo parcial total de todas las cajas abiertas
    # Obtenemos todas las cajas abiertas
    cajas_abiertas = CajaDiaria.objects.filter(cerrada=False)
    
    # Inicializamos variables
    saldo_inicial_total = Decimal('0')  # Importante para cajas secundarias
    ingresos_total = Decimal('0')
    egresos_total = Decimal('0')
    
    # Para cada caja abierta, calculamos sus componentes
    for caja_abierta in cajas_abiertas:
        # Actualizamos su saldo parcial para asegurarnos que esté actualizado
        caja_abierta.actualizar_saldo_parcial()
        
        # Sumamos el saldo inicial (importante para secundarias)
        if caja_abierta.nivel == 'S':
            saldo_inicial_total += caja_abierta.saldo_inicial
        
        # Sumamos todos los ingresos (recreos + eventos)
        ingresos_total += caja_abierta.get_total_ingresos()
        
        # Sumamos todos los pagos
        total_pagos = caja_abierta.pagoproveedor_set.aggregate(
            total=Sum('monto'))['total'] or Decimal('0')
        egresos_total += total_pagos
    
    # Calculamos el saldo parcial total
    saldo_parcial_total = saldo_inicial_total + ingresos_total - egresos_total
    
    # Para mantener la compatibilidad con el template, calculamos los ingresos de recreos primario por separado
    cajas_primarias_abiertas = cajas_abiertas.filter(nivel='P').exclude(id=caja.id)
    ingresos_recreos_primario = Recreo.objects.filter(
        caja__in=cajas_primarias_abiertas
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0')
    
    # Determinamos si se pueden hacer pagos en esta caja
    puede_hacer_pagos = caja.nivel == 'S' or (caja.es_extra and caja.nivel == 'S')
    
    context = {
        'caja': caja,
        'saldo_general': saldo_general,
        'recreo_form': RecreoForm(),
        'pago_form': PagoProveedorForm() if puede_hacer_pagos else None,
        # Solo incluir eventos para cajas normales, no para cajas extras
        'eventos': EventoEspecial.objects.filter(caja=caja) if not caja.es_extra else [],
        'pagos': PagoProveedor.objects.filter(caja=caja) if puede_hacer_pagos else None,
        'recreos': recreos,
        'proximo_recreo': proximo_recreo,
        'saldo_parcial_total': saldo_parcial_total,
        'ingresos_recreos_primario': ingresos_recreos_primario,
        'es_extra': caja.es_extra,
        'puede_hacer_pagos': puede_hacer_pagos,
    }
    
    return render(request, 'registrar_movimientos.html', context)

@solo_admin
def limpiar_cajas(request):
    if request.method == 'POST':
        try:
            EventoEspecial.objects.all().delete()
            PagoProveedor.objects.all().delete()
            Recreo.objects.all().delete()
            CajaDiaria.objects.all().delete()
            
            saldo_general = SaldoGeneral.objects.first()
            if saldo_general:
                saldo_general.monto = 0
                saldo_general.save()
            
            messages.success(request, 'Datos de caja limpiados correctamente')
        except Exception as e:
            messages.error(request, f'Error al limpiar datos: {str(e)}')
    
    return redirect('caja:lista_cajas')

@admin_o_encargado
def gestionar_saldo_general(request):
    saldo_general = SaldoGeneral.objects.first()
    if not saldo_general:
        saldo_general = SaldoGeneral.objects.create()

    if request.method == 'POST':
        form = SaldoGeneralForm(request.POST)
        if form.is_valid():
            monto = form.cleaned_data['monto']
            tipo_operacion = form.cleaned_data['tipo_operacion']

            if tipo_operacion == 'establecer':
                saldo_general.monto = monto
            elif tipo_operacion == 'sumar':
                saldo_general.monto += monto
            else:
                saldo_general.monto -= monto

            saldo_general.save()
            messages.success(request, 'Saldo general actualizado correctamente')
            return redirect('caja:lista_cajas')
    else:
        form = SaldoGeneralForm()

    return render(request, 'gestionar_saldo.html', {
        'form': form,
        'saldo_general': saldo_general
    })

@login_required
def editar_pago(request, pago_id):
    pago = get_object_or_404(PagoProveedor, id=pago_id)
    caja = pago.caja

    if request.method == 'POST':
        form = PagoProveedorForm(request.POST, instance=pago)
        if form.is_valid():
            form.save()
            caja.actualizar_saldo_parcial()
            messages.success(request, 'Pago actualizado correctamente')
            return redirect('caja:registrar_movimientos', caja_id=caja.id)
    else:
        form = PagoProveedorForm(instance=pago)

    return render(request, 'editar_pago.html', {
        'form': form,
        'pago': pago,
        'caja': caja
    })

@login_required
def eliminar_pago(request, pago_id):
    pago = get_object_or_404(PagoProveedor, id=pago_id)
    caja = pago.caja
    
    if request.method == 'POST':
        pago.delete()
        caja.actualizar_saldo_parcial()
        messages.success(request, 'Pago eliminado correctamente')
        return redirect('caja:registrar_movimientos', caja_id=caja.id)
    
    return render(request, 'confirmar_eliminar_pago.html', {
        'pago': pago,
        'caja': caja
    })

@solo_admin
def eliminar_caja_extra(request, caja_id):
    caja = get_object_or_404(CajaDiaria, id=caja_id)
    
    # Verificar que sea una caja extra
    if not caja.es_extra:
        messages.error(request, 'Solo se pueden eliminar cajas extras')
        return redirect('caja:lista_cajas')
    
    if request.method == 'POST':
        # Calcular el impacto en el saldo general antes de eliminar
        total_ingresos = caja.get_total_ingresos()
        total_egresos = Decimal('0')
        
        # Si es caja secundaria, calcular también los pagos a proveedores
        if caja.nivel == 'S':
            total_egresos = caja.pagoproveedor_set.aggregate(
                total=Sum('monto'))['total'] or Decimal('0')
        
        # Impacto neto en el saldo
        impacto_saldo = total_ingresos - total_egresos
        
        # Obtener saldo general
        saldo_general = SaldoGeneral.objects.first()
        if not saldo_general:
            saldo_general = SaldoGeneral.objects.create()
        
        # Restar el impacto del saldo general (porque estamos eliminando la caja)
        saldo_general.monto -= impacto_saldo
        saldo_general.save()
        
        # Eliminamos todos los registros asociados a esta caja
        caja.recreo_set.all().delete()
        caja.pagoproveedor_set.all().delete()
        caja.delete()
        
        # Mensaje de éxito con el detalle del ajuste
        messages.success(request, f'Caja extra eliminada correctamente. Se ha ajustado el saldo general: ${impacto_saldo:.2f}')
    
    return redirect('caja:lista_cajas')

@login_required
def ver_movimientos_caja(request, caja_id):
    caja = get_object_or_404(CajaDiaria, id=caja_id)
    recreos = Recreo.objects.filter(caja=caja)
    # Solo mostrar eventos especiales para cajas normales, no para cajas extras
    eventos = EventoEspecial.objects.filter(caja=caja) if not caja.es_extra else []
    pagos = PagoProveedor.objects.filter(caja=caja)
    return render(request, 'ver_movimientos_caja.html', {
        'caja': caja,
        'recreos': recreos,
        'eventos': eventos,
        'pagos': pagos,
    })

@login_required
def editar_recreo(request, recreo_id):
    recreo = get_object_or_404(Recreo, id=recreo_id)
    caja = recreo.caja

    if request.method == 'POST':
        form = RecreoForm(request.POST, instance=recreo)
        if form.is_valid():
            form.save()
            caja.actualizar_saldo_parcial()
            messages.success(request, 'Recreo actualizado correctamente')
            return redirect('caja:registrar_movimientos', caja_id=caja.id)
    else:
        form = RecreoForm(instance=recreo)

    return render(request, 'editar_recreo.html', {
        'form': form,
        'recreo': recreo,
        'caja': caja
    })