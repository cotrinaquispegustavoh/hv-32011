from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from apps.users.infrastructure.repositories.user_repository import DjangoUserRepository
from apps.users.core.use_cases.manage_users import GetStaffListUseCase, ToggleUserStatusUseCase, BulkUpdatePermissionsUseCase
from apps.core.utils import normalize_text

@login_required(login_url='/auth/login/')
def staff_list_view(request):
    if request.user.role not in ['DIRECTOR', 'SUPERUSER']: return redirect('core:dashboard')
    repo = DjangoUserRepository()
    staff = GetStaffListUseCase(repo).execute()
    
    # Seleccionamos al primer usuario por defecto para mostrar en el panel derecho
    first_user = staff[0] if staff else None
    
    return render(request, 'users/staff_list.html', {
        'staff': staff,
        'selected_user': first_user
    })

@login_required(login_url='/auth/login/')
def search_staff_view(request):
    if request.user.role not in ['DIRECTOR', 'SUPERUSER']: return HttpResponse("No autorizado", status=403)
    query = normalize_text(request.GET.get('q', ''))
    role_filter = request.GET.get('role', '')
    
    staff = GetStaffListUseCase(DjangoUserRepository()).execute()
    if query: staff = [u for u in staff if query in normalize_text(u.first_name) or query in normalize_text(u.last_name) or query in normalize_text(u.dni)]
    if role_filter: staff = [u for u in staff if u.role == role_filter]
    
    return render(request, 'users/partials/staff_list_items.html', {'staff': staff})

# --- ESTAS SON LAS FUNCIONES QUE FALTABAN ---
@login_required(login_url='/auth/login/')
def staff_detail_view(request, user_id):
    """Carga el panel derecho con los detalles del usuario seleccionado."""
    if request.user.role not in ['DIRECTOR', 'SUPERUSER']: return HttpResponse("No autorizado", status=403)
    
    repo = DjangoUserRepository()
    user_detail = repo.get_by_id(user_id)
    
    return render(request, 'users/partials/staff_detail.html', {'selected_user': user_detail})

@login_required(login_url='/auth/login/')
def toggle_module_permission_view(request, user_id):
    """Enciende o apaga un permiso específico al hacer clic en el interruptor (toggle)."""
    if request.method == 'POST' and request.user.role in ['DIRECTOR', 'SUPERUSER']:
        module = request.POST.get('module')
        repo = DjangoUserRepository()
        user_entity = repo.get_by_id(user_id)
        
        if user_entity:
            perms = list(user_entity.module_permissions)
            if module in perms:
                perms.remove(module) # Si lo tiene, se lo quitamos
            else:
                perms.append(module) # Si no lo tiene, se lo damos
            
            user_entity.module_permissions = perms
            repo.save(user_entity)
            
        # Recargamos el panel derecho para reflejar el cambio
        return staff_detail_view(request, user_id)
        
    return HttpResponse("No autorizado", status=403)
# --------------------------------------------

@login_required(login_url='/auth/login/')
def toggle_status_view(request, user_id):
    if request.method == 'POST' and request.user.role in ['DIRECTOR', 'SUPERUSER']:
        repo = DjangoUserRepository()
        try:
            ToggleUserStatusUseCase(repo).execute(user_id, request.user.id)
            return staff_detail_view(request, user_id)
        except ValueError as e:
            return HttpResponse(f'<span class="text-red-600 text-xs font-bold">{str(e)}</span>')
    return HttpResponse("No autorizado", status=403)

@login_required(login_url='/auth/login/')
def bulk_permissions_view(request):
    if request.method == 'POST' and request.user.role in ['DIRECTOR', 'SUPERUSER']:
        user_ids = request.POST.getlist('user_ids')
        modules = request.POST.getlist('modules')
        user_ids = [int(id) for id in user_ids if id.isdigit()]
        repo = DjangoUserRepository()
        try:
            BulkUpdatePermissionsUseCase(repo).execute(user_ids, modules)
            query = normalize_text(request.GET.get('q', ''))
            role_filter = request.GET.get('role', '')
            staff = GetStaffListUseCase(repo).execute()
            if query: staff = [u for u in staff if query in normalize_text(u.first_name) or query in normalize_text(u.last_name) or query in normalize_text(u.dni)]
            if role_filter: staff = [u for u in staff if u.role == role_filter]
            return render(request, 'users/partials/staff_table_rows.html', {'staff': staff})
        except ValueError as e:
            return HttpResponse(f"<tr><td colspan='5' class='p-5 text-rose-600 font-bold text-center'>Error: {str(e)}</td></tr>", status=400)
    return HttpResponse("No autorizado", status=403)