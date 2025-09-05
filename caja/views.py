
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Q
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from .models import (SaldoGeneral, SaldoElectronico, CajaDiaria, CajaElectronica, 
                    Recreo, EventoEspecial, PagoProveedor, IngresoElectronico, PagoElectronico)
from .forms import (InicioCajaForm, InicioCajaExtraForm, RecreoForm, EventoEspecialForm, 
                   PagoProveedorForm, InicioCajaElectronicaForm, IngresoElectronicoForm, 
                   PagoElectronicoForm, SaldoElectronicoForm)
from django import forms
from usuarios.decorators import solo_admin, admin_o_encargado
from django.utils import timezone
from precios.models import Proveedor

# Vista de egresos por proveedor y fechas
@login_required
def egresos_por_proveedor(request):
    proveedores = Proveedor.objects.all()
    pagos = []
    total_egresos = 0
    filtro = Q()
    proveedor_id = request.GET.get('proveedor')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    if proveedor_id:
        filtro &= Q(proveedor_id=proveedor_id)
    if fecha_inicio:
        filtro &= Q(fecha_registro__date__gte=fecha_inicio)
    if fecha_fin:
        filtro &= Q(fecha_registro__date__lte=fecha_fin)
    if proveedor_id or fecha_inicio or fecha_fin:
        pagos = PagoProveedor.objects.filter(filtro).select_related('proveedor')
        total_egresos = pagos.aggregate(total=Sum('monto'))['total'] or 0
    return render(request, 'egresos_por_proveedor.html', {
        'proveedores': proveedores,
        'pagos': pagos,
        'total_egresos': total_egresos,
    })

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
    # Detectar si hay cajas abiertas en primario y secundario en el mismo turno
    turnos = ['M', 'T']
    caja_abierta_ambos_niveles_mismo_turno = False
    for turno in turnos:
        hay_primario = CajaDiaria.objects.filter(turno=turno, nivel='P', cerrada=False).exists()
        hay_secundario = CajaDiaria.objects.filter(turno=turno, nivel='S', cerrada=False).exists()
        if hay_primario and hay_secundario:
            caja_abierta_ambos_niveles_mismo_turno = True
            break
    import datetime
    from itertools import groupby
    from operator import attrgetter
    
    today = datetime.date.today()
    
    saldo_general = SaldoGeneral.objects.first()
    if not saldo_general:
        saldo_general = SaldoGeneral.objects.create()
        
    saldo_electronico = SaldoElectronico.objects.first()
    if not saldo_electronico:
        saldo_electronico = SaldoElectronico.objects.create()
    
    # Obtenemos el filtro de fecha si existe
    fecha_filtro = request.GET.get('fecha')
    
    # Obtenemos fechas únicas para el dropdown del filtro
    fechas_disponibles = CajaDiaria.objects.values_list('fecha', flat=True).distinct().order_by('-fecha')
    
    # Obtenemos todas las cajas ordenadas por fecha (descendente)
    cajas_query = CajaDiaria.objects.all()
    cajas_electronicas_query = CajaElectronica.objects.all()
    
    # Aplicamos filtro si existe
    if fecha_filtro:
        try:
            fecha_filtro = datetime.datetime.strptime(fecha_filtro, '%Y-%m-%d').date()
            cajas_query = cajas_query.filter(fecha=fecha_filtro)
            cajas_electronicas_query = cajas_electronicas_query.filter(fecha=fecha_filtro)
        except (ValueError, TypeError):
            # Si hay un error en el formato de fecha, ignoramos el filtro
            pass
    
    cajas = cajas_query.order_by('-fecha', 'turno', 'nivel', 'es_extra')
    cajas_electronicas = cajas_electronicas_query.order_by('-fecha')
    
    # Agrupar cajas por fecha incluyendo electrónicas
    cajas_por_fecha = []
    
    # Combinar fechas de ambos tipos de cajas
    todas_las_fechas = set()
    for caja in cajas:
        todas_las_fechas.add(caja.fecha)
    for caja in cajas_electronicas:
        todas_las_fechas.add(caja.fecha)
    
    # Ordenar fechas descendentemente
    fechas_ordenadas = sorted(todas_las_fechas, reverse=True)
    
    for fecha in fechas_ordenadas:
        cajas_fecha = [caja for caja in cajas if caja.fecha == fecha]
        cajas_electronicas_fecha = [caja for caja in cajas_electronicas if caja.fecha == fecha]
        
        # Calcular totales incluyendo cajas electrónicas
        total_ingresos_dia = sum(caja.get_total_ingresos() for caja in cajas_fecha)
        total_egresos_dia = sum(caja.get_total_egresos() for caja in cajas_fecha)
        
        # Agregar ingresos y egresos de cajas electrónicas
        for caja_elec in cajas_electronicas_fecha:
            total_ingresos_dia += caja_elec.get_total_ingresos()
            total_egresos_dia += caja_elec.get_total_egresos()
        
        cajas_por_fecha.append({
            'fecha': fecha,
            'cajas': cajas_fecha,
            'cajas_electronicas': cajas_electronicas_fecha,
            'es_hoy': fecha == today,
            'total_ingresos': total_ingresos_dia,
            'total_egresos': total_egresos_dia
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
        # Actualizamos su saldo parcial para asegurarnos que esté actualizado
        caja.actualizar_saldo_parcial()
        
        # Sumamos el saldo inicial solo de cajas secundarias (lógica del negocio)
        # Las cajas primarias siempre empiezan con 0
        if caja.nivel == 'S':
            saldo_inicial_total += caja.saldo_inicial
        
        # Sumamos todos los ingresos (recreos + eventos)
        ingresos_total += caja.get_total_ingresos()
        
        # Sumamos todos los egresos
        egresos_total += caja.get_total_egresos()
    
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
    
    # Obtener todas las cajas no cerradas (en proceso)
    cajas_abiertas = CajaDiaria.objects.filter(cerrada=False)
    hay_cajas_abiertas = cajas_abiertas.exists()

    # Verificar si hay cajas del mismo nivel y turno abiertas
    def hay_caja_abierta_mismo_nivel_turno(nivel, turno):
        return CajaDiaria.objects.filter(
            nivel=nivel,
            turno=turno,
            cerrada=False
        ).exists()

    # Preparar el contexto para verificar las restricciones
    # Obtener información de cajas electrónicas
    caja_electronica_abierta = CajaElectronica.objects.filter(cerrada=False).first()
    hay_caja_electronica_abierta = caja_electronica_abierta is not None
    
    context = {
        'cajas_por_fecha': cajas_por_fecha,
        'fechas_disponibles': fechas_disponibles,
        'fecha_filtro': fecha_filtro,
        'saldo_general': saldo_general,
        'saldo_electronico': saldo_electronico,
        'hay_cajas_abiertas': hay_cajas_abiertas,
        'hay_caja_electronica_abierta': hay_caja_electronica_abierta,
        'caja_electronica_abierta': caja_electronica_abierta,
        'saldo_parcial': saldo_parcial if hay_cajas_abiertas else 0,
        'hay_caja_mismo_nivel_turno': hay_caja_abierta_mismo_nivel_turno,
        'hay_cajas_extras_disponibles': hay_cajas_extras_disponibles,
        'caja_abierta_ambos_niveles_mismo_turno': caja_abierta_ambos_niveles_mismo_turno,
        'saldo_total': saldo_general.get_saldo_total(),
        'today': today,  # Agregar la fecha de hoy para el template
    }

    return render(request, 'lista_cajas.html', context)

def iniciar_caja(request):
    if request.method == 'POST':
        nivel = request.POST.get('nivel')
        turno = request.POST.get('turno')
        
        # Verificar si ya existe una caja abierta del mismo nivel y turno
        if CajaDiaria.objects.filter(nivel=nivel, turno=turno, cerrada=False).exists():
            messages.error(request, 'Ya existe una caja abierta para este nivel y turno')
            return redirect('caja:lista_cajas')
        
        # Si no existe, crear la nueva caja
        caja = CajaDiaria.objects.create(
            nivel=nivel,
            turno=turno,
            fecha=timezone.now().date()
        )
        messages.success(request, 'Caja iniciada correctamente')
        return redirect('caja:registrar_movimientos', caja_id=caja.id)

    return render(request, 'iniciar_caja.html')

from usuarios.decorators import admin_encargado_vendedor
@admin_encargado_vendedor
def iniciar_caja(request):
    from django.utils import timezone
    
    if request.method == 'POST':
        form = InicioCajaForm(request.POST)
        if form.is_valid():
            nivel = form.cleaned_data['nivel']
            turno = form.cleaned_data['turno']
            
            # Verificar si hay una caja abierta del mismo nivel y turno
            caja_existente = CajaDiaria.objects.filter(
                nivel=nivel, 
                turno=turno,
                cerrada=False
            ).exists()
            
            if caja_existente:
                messages.error(request, 'Ya existe una caja abierta para este nivel y turno')
                return redirect('caja:lista_cajas')
            
            # Crear la nueva caja sin mostrar el saldo inicial
            caja = form.save(commit=False)
            caja.fecha = timezone.now().date()
            
            # Si es nivel secundario, el saldo inicial siempre es el saldo general
            if caja.nivel == 'S':
                saldo_general = SaldoGeneral.objects.first()
                if saldo_general:
                    caja.saldo_inicial = saldo_general.monto
                else:
                    caja.saldo_inicial = 0
                # Si es turno tarde, no permitir si hay caja secundaria del turno mañana activa
                if caja.turno == 'T':
                    caja_manana_abierta = CajaDiaria.objects.filter(
                        nivel='S',
                        turno='M',
                        cerrada=False
                    ).exists()
                    if caja_manana_abierta:
                        messages.error(request, 'No se puede abrir caja del turno tarde si hay una caja del turno mañana activa.')
                        return redirect('caja:lista_cajas')
            
            caja.save()
            messages.success(request, 'Caja iniciada correctamente')
            return redirect('caja:registrar_movimientos', caja_id=caja.id)
    else:
        form = InicioCajaForm()
    
    return render(request, 'iniciar_caja.html', {
        'form': form,
        'fecha_actual': timezone.now().date()
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
            # Redirigir a la página de confirmación
            return redirect('caja:confirmar_cerrar_caja', caja_id=caja.id)
        
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
        
        # Sumamos el saldo inicial solo de cajas secundarias (lógica del negocio)
        # Las cajas primarias siempre empiezan con 0
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

# ================= VISTAS DE CAJA ELECTRÓNICA =================

@solo_admin
def iniciar_caja_electronica(request):
    """Vista para iniciar una nueva caja electrónica (solo admin)"""
    import datetime
    
    # Verificar si ya existe una caja electrónica abierta
    caja_abierta = CajaElectronica.objects.filter(cerrada=False).first()
    if caja_abierta:
        messages.error(request, f'Ya existe una caja electrónica abierta del {caja_abierta.fecha}')
        return redirect('caja:lista_cajas')
    
    # Verificar si ya existe una caja electrónica para hoy
    hoy = datetime.date.today()
    if CajaElectronica.objects.filter(fecha=hoy).exists():
        messages.error(request, 'Ya existe una caja electrónica para el día de hoy')
        return redirect('caja:lista_cajas')

    if request.method == 'POST':
        form = InicioCajaElectronicaForm(request.POST)
        if form.is_valid():
            try:
                caja = form.save(commit=False)
                caja.fecha = hoy
                caja.save()
                
                # Actualizar saldo inicial
                caja.actualizar_saldo_parcial()
                
                messages.success(request, f'Caja electrónica iniciada correctamente para el {hoy}')
                return redirect('caja:lista_cajas')
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = InicioCajaElectronicaForm()

    return render(request, 'iniciar_caja_electronica.html', {'form': form})

@login_required
def registrar_movimientos_electronicos(request, caja_id):
    """Vista para registrar movimientos en la caja electrónica"""
    caja = get_object_or_404(CajaElectronica, id=caja_id)
    
    # Verificar permisos: solo admin y el usuario responsable
    if not (request.user.perfil.rol == 'admin' or request.user == caja.usuario_responsable):
        messages.error(request, 'No tienes permisos para gestionar esta caja electrónica')
        return redirect('caja:lista_cajas')
    
    if caja.cerrada:
        messages.error(request, 'Esta caja electrónica está cerrada')
        return redirect('caja:lista_cajas')

    ingreso_form = IngresoElectronicoForm()
    pago_form = PagoElectronicoForm()

    if request.method == 'POST':
        if 'ingreso_submit' in request.POST:
            ingreso_form = IngresoElectronicoForm(request.POST)
            if ingreso_form.is_valid():
                ingreso = ingreso_form.save(commit=False)
                ingreso.caja_electronica = caja
                ingreso.usuario_registro = request.user
                ingreso.save()
                caja.actualizar_saldo_parcial()
                messages.success(request, 'Ingreso electrónico registrado correctamente')
                return redirect('caja:registrar_movimientos_electronicos', caja_id=caja.id)

        elif 'pago_submit' in request.POST:
            pago_form = PagoElectronicoForm(request.POST)
            if pago_form.is_valid():
                pago = pago_form.save(commit=False)
                pago.caja_electronica = caja
                pago.usuario_registro = request.user
                pago.save()
                caja.actualizar_saldo_parcial()
                messages.success(request, 'Pago electrónico registrado correctamente')
                return redirect('caja:registrar_movimientos_electronicos', caja_id=caja.id)

    # Obtener movimientos
    ingresos = IngresoElectronico.objects.filter(caja_electronica=caja).order_by('-fecha_registro')
    pagos = PagoElectronico.objects.filter(caja_electronica=caja).order_by('-fecha_registro')

    return render(request, 'registrar_movimientos_electronicos.html', {
        'caja': caja,
        'ingreso_form': ingreso_form,
        'pago_form': pago_form,
        'ingresos': ingresos,
        'pagos': pagos,
    })

@solo_admin
def cerrar_caja_electronica(request, caja_id):
    """Vista para cerrar la caja electrónica y actualizar saldo general"""
    caja = get_object_or_404(CajaElectronica, id=caja_id)
    
    if caja.cerrada:
        messages.error(request, 'Esta caja electrónica ya está cerrada')
        return redirect('caja:lista_cajas')

    if request.method == 'POST':
        # Cerrar la caja
        caja.cerrada = True
        caja.save()
        
        # Actualizar el saldo electrónico general
        saldo_electronico, created = SaldoElectronico.objects.get_or_create(defaults={'monto': 0})
        saldo_electronico.monto += caja.saldo_parcial
        saldo_electronico.save()
        
        messages.success(request, f'Caja electrónica cerrada. Saldo transferido al saldo general electrónico: ${caja.saldo_parcial}')
        return redirect('caja:lista_cajas')

    return render(request, 'confirmar_cerrar_caja_electronica.html', {'caja': caja})

@solo_admin
def gestionar_saldo_electronico(request):
    """Vista para gestionar el saldo electrónico general"""
    saldo_electronico, created = SaldoElectronico.objects.get_or_create(defaults={'monto': 0})
    
    if request.method == 'POST':
        form = SaldoElectronicoForm(request.POST, instance=saldo_electronico)
        if form.is_valid():
            form.save()
            messages.success(request, 'Saldo electrónico actualizado correctamente')
            return redirect('caja:lista_cajas')
    else:
        form = SaldoElectronicoForm(instance=saldo_electronico)

    return render(request, 'gestionar_saldo_electronico.html', {
        'form': form,
        'saldo_electronico': saldo_electronico
    })

@login_required
def ver_movimientos_caja_electronica(request, caja_id):
    """Vista para ver los movimientos de una caja electrónica"""
    caja = get_object_or_404(CajaElectronica, id=caja_id)
    
    # Verificar permisos: admin, encargado o usuario responsable
    if not (request.user.perfil.rol in ['admin', 'encargado'] or request.user == caja.usuario_responsable):
        messages.error(request, 'No tienes permisos para ver esta caja electrónica')
        return redirect('caja:lista_cajas')
    
    ingresos = IngresoElectronico.objects.filter(caja_electronica=caja).order_by('-fecha_registro')
    pagos = PagoElectronico.objects.filter(caja_electronica=caja).order_by('-fecha_registro')
    
    return render(request, 'ver_movimientos_caja_electronica.html', {
        'caja': caja,
        'ingresos': ingresos,
        'pagos': pagos,
    })

@login_required
def confirmar_cerrar_caja(request, caja_id):
    """Vista para confirmar el cierre de una caja diaria"""
    caja = get_object_or_404(CajaDiaria, id=caja_id)
    saldo_general = SaldoGeneral.objects.first()
    if not saldo_general:
        saldo_general = SaldoGeneral.objects.create()
    
    if caja.cerrada:
        messages.error(request, 'Esta caja ya está cerrada')
        return redirect('caja:lista_cajas')

    if request.method == 'POST' and 'confirmar_cierre' in request.POST:
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

    # Actualizar saldo parcial antes de mostrar la confirmación
    caja.actualizar_saldo_parcial()
    
    # Calcular la diferencia de saldo
    diferencia_saldo = caja.saldo_parcial - caja.saldo_inicial
    
    return render(request, 'confirmar_cerrar_caja.html', {
        'caja': caja,
        'diferencia_saldo': diferencia_saldo
    })

@admin_o_encargado
def reabrir_caja(request, caja_id):
    """Vista para reabrir una caja cerrada del día actual"""
    from django.core.exceptions import ValidationError
    from datetime import date
    
    caja = get_object_or_404(CajaDiaria, id=caja_id)
    
    # Verificar que la caja esté cerrada
    if not caja.cerrada:
        messages.error(request, 'Esta caja ya está abierta')
        return redirect('caja:lista_cajas')
    
    # Verificar que sea del día actual
    if caja.fecha != date.today():
        messages.error(request, 'Solo se pueden reabrir cajas del día actual')
        return redirect('caja:lista_cajas')
    
    if request.method == 'POST' and 'confirmar_reapertura' in request.POST:
        try:
            # Actualizar el saldo general restando la diferencia
            saldo_general = SaldoGeneral.objects.first()
            if saldo_general:
                # Usar la diferencia que ya está almacenada en la BD
                # para evitar problemas con cambios en la lógica de cálculo
                saldo_diferencia = caja.saldo_parcial - caja.saldo_inicial
                saldo_general.monto -= saldo_diferencia
                saldo_general.save()
                
                print(f"DEBUG: Reapertura - Diferencia restada: {saldo_diferencia}")
            
            # Reabrir la caja
            caja.reabrir_caja(request.user)
            
            mensaje = f'Caja {"extra" if caja.es_extra else ""} reabierta correctamente'
            messages.success(request, mensaje)
            return redirect('caja:registrar_movimientos', caja_id=caja.id)
            
        except ValidationError as e:
            messages.error(request, str(e))
            return redirect('caja:lista_cajas')
    
    # Calcular la diferencia de saldo que se restará del saldo general
    diferencia_saldo = caja.saldo_parcial - caja.saldo_inicial
    
    return render(request, 'confirmar_reabrir_caja.html', {
        'caja': caja,
        'diferencia_saldo': diferencia_saldo
    })