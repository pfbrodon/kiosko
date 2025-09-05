from django.urls import path
from . import views

app_name = 'caja'

urlpatterns = [
    path('', views.lista_cajas, name='lista_cajas'),
    path('iniciar/', views.iniciar_caja, name='iniciar_caja'),
    path('iniciar-extra/', views.iniciar_caja_extra, name='iniciar_caja_extra'),
    path('<int:caja_id>/movimientos/', views.registrar_movimientos, name='registrar_movimientos'),
    path('gestionar-saldo/', views.gestionar_saldo_general, name='gestionar_saldo'),
    path('pago/<int:pago_id>/editar/', views.editar_pago, name='editar_pago'),
    path('pago/<int:pago_id>/eliminar/', views.eliminar_pago, name='eliminar_pago'),
    path('recreo/<int:recreo_id>/editar/', views.editar_recreo, name='editar_recreo'),
    path('caja/<int:caja_id>/ver/', views.ver_movimientos_caja, name='ver_movimientos_caja'),
    path('caja/<int:caja_id>/confirmar-cerrar/', views.confirmar_cerrar_caja, name='confirmar_cerrar_caja'),
    path('caja/<int:caja_id>/reabrir/', views.reabrir_caja, name='reabrir_caja'),
    path('limpiar/', views.limpiar_cajas, name='limpiar_cajas'),
    path('caja-extra/<int:caja_id>/eliminar/', views.eliminar_caja_extra, name='eliminar_caja_extra'),
    path('egresos-proveedor/', views.egresos_por_proveedor, name='egresos_por_proveedor'),
    
    # URLs para Caja Electrónica
    path('electronica/iniciar/', views.iniciar_caja_electronica, name='iniciar_caja_electronica'),
    path('electronica/<int:caja_id>/movimientos/', views.registrar_movimientos_electronicos, name='registrar_movimientos_electronicos'),
    path('electronica/<int:caja_id>/cerrar/', views.cerrar_caja_electronica, name='cerrar_caja_electronica'),
    path('electronica/<int:caja_id>/ver/', views.ver_movimientos_caja_electronica, name='ver_movimientos_caja_electronica'),
    path('gestionar-saldo-electronico/', views.gestionar_saldo_electronico, name='gestionar_saldo_electronico'),
]