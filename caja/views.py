from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum
from django.core.exceptions import ValidationError  # Agregamos esta importación
from decimal import Decimal
from .models import SaldoGeneral, CajaDiaria, Recreo, EventoEspecial, PagoProveedor
from .forms import InicioCajaForm, RecreoForm, EventoEspecialForm, PagoProveedorForm
from django import forms

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
    if not saldo_general:
        saldo_general = SaldoGeneral.objects.create()
    
    # Obtener el próximo recreo disponible
    recreos = Recreo.objects.filter(caja=caja).order_by('numero')
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
                try:
                    recreo.full_clean()
                    recreo.save()
                    caja.saldo_parcial += recreo.monto
                    caja.save()
                    messages.success(request, 'Recreo registrado correctamente')
                except ValidationError as e:
                    messages.error(request, e.messages[0])
            return redirect('caja:registrar_movimientos', caja_id=caja.id)
        
        elif 'agregar_evento' in request.POST:
            descripcion = request.POST.get('descripcion_evento')
            monto = Decimal(request.POST.get('monto_evento', '0'))
            
            evento = EventoEspecial.objects.create(
                caja=caja,
                descripcion=descripcion,
                monto=monto
            )
            
            caja.saldo_parcial += monto
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
        'eventos': EventoEspecial.objects.filter(caja=caja),
        'pagos': PagoProveedor.objects.filter(caja=caja) if caja.nivel == 'S' else None,
        'recreos': recreos,
        'proximo_recreo': proximo_recreo,
    }
    
    return render(request, 'registrar_movimientos.html', context)

def limpiar_cajas(request):
    if request.method == 'POST':
        try:
            # Eliminamos primero las tablas relacionadas
            EventoEspecial.objects.all().delete()
            PagoProveedor.objects.all().delete()
            Recreo.objects.all().delete()
            CajaDiaria.objects.all().delete()
            
            # Reiniciamos el saldo general
            saldo_general = SaldoGeneral.objects.first()
            if saldo_general:
                saldo_general.monto = 0
                saldo_general.save()
            
            messages.success(request, 'Datos de caja limpiados correctamente')
        except Exception as e:
            messages.error(request, f'Error al limpiar datos: {str(e)}')
    
    return redirect('caja:lista_cajas')

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
            else:  # restar
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
