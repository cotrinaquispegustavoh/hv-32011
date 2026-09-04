from django.shortcuts import redirect
from django.urls import reverse
from django.utils.cache import add_never_cache_headers
from django.http import HttpResponseForbidden, HttpResponse
from functools import wraps
from apps.users.permissions import has_permission

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
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.user.is_authenticated:
            add_never_cache_headers(response)
        return response

# --- NUEVO: Solución al Bug del Login dentro de HTMX ---
class HtmxLoginRedirectMiddleware:
    """
    Si la sesión expira y el usuario hace una petición HTMX, 
    fuerza una redirección de página completa al Login.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Si es una petición HTMX y Django intenta redirigir (302) al login
        if request.headers.get('HX-Request') == 'true' and response.status_code == 302:
            if '/auth/login/' in response.url:
                htmx_response = HttpResponse()
                htmx_response['HX-Redirect'] = response.url # Ordena a HTMX redirigir toda la ventana
                return htmx_response
                
        return response

def require_module_permission(module_name):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.role in ['DIRECTOR', 'SUBDIRECTOR', 'SUPERUSER']:
                return view_func(request, *args, **kwargs)
            if module_name in request.user.module_permissions:
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden("No tienes permiso para acceder a este módulo.")
        return _wrapped_view
    return decorator


def require_permission(permission_code):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if has_permission(request.user, permission_code):
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden("No tienes permiso para realizar esta acción.")
        return _wrapped_view
    return decorator
