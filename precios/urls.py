from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'), 
    path('productos/', views.lista_productos, name='lista_productos'),
    path('productos/<int:pk>/editar/', views.editar_producto, name='editar_producto'),
    path('productos/crear/', views.crear_producto, name='crear_producto'),
    path('productos/<int:pk>/eliminar/', views.eliminar_producto, name='eliminar_producto'),
    path('productos/<int:pk>/movimientos/', views.movimientos_stock, name='movimientos_stock'),
    path('subcategorias/', views.lista_subcategorias, name='lista_subcategorias'),
    path('subcategorias/crear/', views.crear_subcategoria, name='crear_subcategoria'),
    path('categorias/', views.lista_categorias, name='lista_categorias'),
    path('categoria/crear/', views.crear_categoria, name='crear_categoria'),
    path('proveedores/', views.lista_proveedores, name='lista_proveedores'),
    path('proveedor/crear/', views.crear_proveedor, name='crear_proveedor'),
    path('proveedor/<int:pk>/editar/', views.editar_proveedor, name='editar_proveedor'),
    path('proveedor/<int:pk>/eliminar/', views.eliminar_proveedor, name='eliminar_proveedor'),
    path('marcas/', views.lista_marcas, name='lista_marcas'),
    path('marca/crear/', views.crear_marca, name='crear_marca'),
    path('marcas/<int:pk>/editar/', views.editar_marca, name='editar_marca'),
    path('marcas/<int:pk>/eliminar/', views.eliminar_marca, name='eliminar_marca'),
    path('productos/lista-precios-pdf/', views.lista_precios_pdf, name='lista_precios_pdf'),
]
