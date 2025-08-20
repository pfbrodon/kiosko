from django.urls import path
from . import views

app_name = 'caja'

urlpatterns = [
    path('', views.lista_cajas, name='lista_cajas'),
    path('iniciar/', views.iniciar_caja, name='iniciar_caja'),
    path('<int:caja_id>/movimientos/', views.registrar_movimientos, name='registrar_movimientos'),
    path('limpiar/', views.limpiar_cajas, name='limpiar_cajas'),
    path('saldo-general/', views.gestionar_saldo_general, name='gestionar_saldo'),  # Nueva URL
    path('pago/<int:pago_id>/editar/', views.editar_pago, name='editar_pago'),
    path('pago/<int:pago_id>/eliminar/', views.eliminar_pago, name='eliminar_pago'),
    path('<int:caja_id>/ver-movimientos/', views.ver_movimientos_caja, name='ver_movimientos_caja'),
    path('recreo/<int:recreo_id>/editar/', views.editar_recreo, name='editar_recreo'),
]