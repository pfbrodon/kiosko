from django.contrib import admin
from .models import Perfil

@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ['user', 'rol', 'fecha_creacion']
    list_filter = ['rol', 'fecha_creacion']
    search_fields = ['user__username', 'user__email']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
