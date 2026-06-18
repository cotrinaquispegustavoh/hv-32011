from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.users.interfaces.middlewares import require_module_permission
from apps.warehouse.infrastructure.repositories.warehouse_repository import DjangoMaterialRepository

@login_required(login_url='/auth/login/')
@require_module_permission('almacen')
def catalog_view(request):
    material_repo = DjangoMaterialRepository()
    materials = material_repo.get_all()
    
    # Lógica del buscador
    query = request.GET.get('q', '').lower()
    if query:
        materials = [m for m in materials if query in m.name.lower() or query in m.location.lower()]

    # Si es una petición HTMX (búsqueda en tiempo real), devolvemos solo las tarjetas
    if 'HX-Request' in request.headers:
        return render(request, 'warehouse/partials/catalog_cards.html', {'materials': materials})

    return render(request, 'warehouse/catalog.html', {'materials': materials})