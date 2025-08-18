from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied

def rol_requerido(*roles):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('usuarios:login')
            
            if not hasattr(request.user, 'perfil'):
                raise PermissionDenied("Usuario sin perfil asignado")
            
            if request.user.perfil.rol not in roles:
                raise PermissionDenied("No tienes permisos para acceder a esta página")
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

# Decoradores específicos
def solo_admin(view_func):
    return rol_requerido('admin')(view_func)

def admin_o_encargado(view_func):
    return rol_requerido('admin', 'encargado')(view_func)