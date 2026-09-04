from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.users.interfaces.middlewares import require_permission
from apps.users.permissions import has_permission
from apps.warehouse.infrastructure.repositories.warehouse_repository import DjangoMaterialRepository
from apps.core.utils import normalize_text # <-- IMPORTAR

@login_required(login_url='/auth/login/')
@require_permission('warehouse.view')
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

    permissions_context = {
        'can_manage_inventory': has_permission(request.user, 'warehouse.manage'),
        'can_request_material': has_permission(request.user, 'warehouse.request'),
    }

    if 'HX-Request' in request.headers:
        return render(
            request,
            'warehouse/partials/catalog_cards.html',
            {'materials': materials, **permissions_context},
        )

    return render(
        request,
        'warehouse/catalog.html',
        {'materials': materials, 'categories': categories, **permissions_context},
    )
