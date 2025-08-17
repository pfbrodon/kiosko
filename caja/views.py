from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum
from django.core.exceptions import ValidationError  # Agregamos esta importación
from decimal import Decimal
from .models import SaldoGeneral, CajaDiaria, Recreo, EventoEspecial, PagoProveedor
from .forms import InicioCajaForm, RecreoForm, EventoEspecialForm, PagoProveedorForm

def lista_cajas(request):
    saldo_general = SaldoGeneral.objects.first()
    if not saldo_general:
        saldo_general = SaldoGeneral.objects.create()
    
    cajas = CajaDiaria.objects.all()
    # Corregida la ruta del template
    return render(request, 'lista_cajas.html', {
        'saldo_general': saldo_general,
        'cajas': cajas
    })

def iniciar_caja(request):
    saldo_general = SaldoGeneral.objects.first()
    if not saldo_general:
        saldo_general = SaldoGeneral.objects.create()
    
    if request.method == 'POST':
        form = InicioCajaForm(request.POST)
        if form.is_valid():
            caja = form.save(commit=False)
            caja.saldo_inicial = saldo_general.monto
            try:
                caja.full_clean()
                caja.save()
                messages.success(request, 'Caja iniciada correctamente')
                return redirect('caja:registrar_movimientos', caja_id=caja.id)
            except ValidationError as e:
                messages.error(request, e.messages[0])
                # Corregida la ruta del template
                return render(request, 'iniciar_caja.html', {
                    'form': form,
                    'saldo_general': saldo_general
                })
    else:
        form = InicioCajaForm()
    
    # Corregida la ruta del template
    return render(request, 'iniciar_caja.html', {
        'form': form,
        'saldo_general': saldo_general
    })

def registrar_movimientos(request, caja_id):
    caja = get_object_or_404(CajaDiaria, id=caja_id)
    saldo_general = SaldoGeneral.objects.first()
    
    if request.method == 'POST':
        if 'agregar_recreo' in request.POST:
            form = RecreoForm(request.POST)
            if form.is_valid():
                recreo = form.save(commit=False)
                recreo.caja = caja
                try:
                    recreo.full_clean()
                    recreo.save()
                    caja.saldo_parcial += recreo.monto
                    caja.save()
                    messages.success(request, 'Recreo registrado correctamente')
                except ValidationError as e:
                    messages.error(request, e.messages[0])
            return redirect('caja:registrar_movimientos', caja_id=caja.id)
        
        elif 'agregar_evento' in request.POST and caja.tiene_evento_especial:
            form = EventoEspecialForm(request.POST)
            if form.is_valid():
                evento = form.save(commit=False)
                evento.caja = caja
                evento.save()
                # Actualizar saldo parcial
                caja.saldo_parcial += evento.monto
                caja.save()
                messages.success(request, 'Evento especial registrado correctamente')
            return redirect('caja:registrar_movimientos', caja_id=caja.id)
        
        elif 'agregar_pago' in request.POST and caja.nivel == 'S':
            form = PagoProveedorForm(request.POST)
            if form.is_valid():
                pago = form.save(commit=False)
                pago.caja = caja
                pago.save()
                # Actualizar saldo parcial
                caja.saldo_parcial -= pago.monto
                caja.save()
                messages.success(request, 'Pago registrado correctamente')
            return redirect('caja:registrar_movimientos', caja_id=caja.id)
        
        elif 'cerrar_caja' in request.POST:
            # Actualizar saldo general
            saldo_general.monto += caja.saldo_parcial
            saldo_general.save()
            # Cerrar caja
            caja.cerrada = True
            caja.save()
            messages.success(request, 'Caja cerrada correctamente')
            return redirect('caja:lista_cajas')
    
    context = {
        'caja': caja,
        'saldo_general': saldo_general,
        'recreo_form': RecreoForm(),
        'evento_form': EventoEspecialForm() if caja.tiene_evento_especial else None,
        'pago_form': PagoProveedorForm() if caja.nivel == 'S' else None,
        'recreos': Recreo.objects.filter(caja=caja),
        'eventos': EventoEspecial.objects.filter(caja=caja),
        'pagos': PagoProveedor.objects.filter(caja=caja) if caja.nivel == 'S' else None,
        'numeros_recreo_disponibles': [i for i in range(1, 4) if not Recreo.objects.filter(caja=caja, numero=i).exists()]
    }
    
    # Corregida la ruta del template
    return render(request, 'registrar_movimientos.html', context)
