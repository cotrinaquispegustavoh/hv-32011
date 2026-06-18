from django.shortcuts import redirect
from django.urls import reverse
from django.utils.cache import add_never_cache_headers
from django.http import HttpResponseForbidden
from functools import wraps

class ForcePasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.password_changed:
            allowed_paths = [reverse('users:password_change'), reverse('users:logout')]
            if request.path not in allowed_paths:
                return redirect('users:password_change')
        return self.get_response(request)

class RoleGuardMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

class NoCacheAuthenticatedMiddleware:
    """
    Evita que el navegador guarde en caché (historial) las páginas 
    cuando el usuario está logueado. Soluciona el bug del botón 'Atrás'.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.user.is_authenticated:
            add_never_cache_headers(response)
        return response
    
def require_module_permission(module_name):
    """
    Decorador que bloquea el acceso a una vista si el usuario no tiene 
    el permiso específico en su lista de module_permissions.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Directivos y Superusers tienen acceso total por defecto
            if request.user.role in ['DIRECTOR', 'SUBDIRECTOR', 'SUPERUSER']:
                return view_func(request, *args, **kwargs)
            
            # Verificamos si el módulo está en la lista de permisos del usuario
            if module_name in request.user.module_permissions:
                return view_func(request, *args, **kwargs)
                
            return HttpResponseForbidden("No tienes permiso para acceder a este módulo.")
        return _wrapped_view
    return decorator