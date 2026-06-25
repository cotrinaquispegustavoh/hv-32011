import threading

# Espacio de memoria aislado para cada hilo/petición del servidor
_thread_locals = threading.local()

def get_current_user():
    """Devuelve el usuario que está haciendo la petición actual."""
    return getattr(_thread_locals, 'user', None)

class CurrentUserMiddleware:
    """
    Atrapa al usuario de la petición web y lo guarda en la memoria del hilo.
    Esto permite que los Modelos y Señales (que no tienen acceso al request) 
    sepan quién está modificando la base de datos para la Auditoría.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.user = getattr(request, 'user', None)
        response = self.get_response(request)
        _thread_locals.user = None # Limpiamos la memoria al terminar
        return response