from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.users.interfaces.middlewares import require_module_permission
from apps.warehouse.infrastructure.repositories.warehouse_repository import DjangoMaterialRepository
from apps.core.utils import normalize_text # <-- IMPORTAR

@login_required(login_url='/auth/login/')
@require_module_permission('almacen')
def catalog_view(request):
    material_repo = DjangoMaterialRepository()
    materials = material_repo.get_all()
    categories = sorted(list(set(m.category for m in materials if m.category)))
    
    # Normalizamos
    query = normalize_text(request.GET.get('q', ''))
    cycle = request.GET.get('cycle', '')
    category = request.GET.get('category', '')
    
    if query:
        materials = [m for m in materials if query in normalize_text(m.name) or query in normalize_text(m.location)]
    if cycle:
        materials = [m for m in materials if m.cycle == cycle]
    if category:
        materials = [m for m in materials if m.category == category]

    if 'HX-Request' in request.headers:
        return render(request, 'warehouse/partials/catalog_cards.html', {'materials': materials})

    return render(request, 'warehouse/catalog.html', {'materials': materials, 'categories': categories})