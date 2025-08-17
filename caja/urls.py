from django.urls import path
from . import views

app_name = 'caja'

urlpatterns = [
    path('', views.lista_cajas, name='lista_cajas'),
    path('iniciar/', views.iniciar_caja, name='iniciar_caja'),
    path('<int:caja_id>/movimientos/', views.registrar_movimientos, name='registrar_movimientos'),
]