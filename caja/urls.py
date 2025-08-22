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
    path('limpiar/', views.limpiar_cajas, name='limpiar_cajas'),
    path('caja-extra/<int:caja_id>/eliminar/', views.eliminar_caja_extra, name='eliminar_caja_extra'),
]