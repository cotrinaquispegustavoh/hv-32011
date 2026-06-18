from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from apps.users.infrastructure.repositories.user_repository import DjangoUserRepository
from apps.users.core.use_cases.manage_users import GetStaffListUseCase, ToggleUserStatusUseCase, BulkUpdatePermissionsUseCase

@login_required(login_url='/auth/login/')
def staff_list_view(request):
    if request.user.role not in ['DIRECTOR', 'SUPERUSER']: return redirect('core:dashboard')
    repo = DjangoUserRepository()
    staff = GetStaffListUseCase(repo).execute()
    return render(request, 'users/staff_list.html', {'staff': staff})

@login_required(login_url='/auth/login/')
def toggle_status_view(request, user_id):
    if request.method == 'POST' and request.user.role in ['DIRECTOR', 'SUPERUSER']:
        repo = DjangoUserRepository()
        try:
            is_active = ToggleUserStatusUseCase(repo).execute(user_id, request.user.id)
            csrf_token = request.META.get('CSRF_COOKIE', '')
            
            if is_active:
                return HttpResponse(f'<button hx-post="/auth/personal/estado/{user_id}/" hx-headers=\'{{"X-CSRFToken": "{csrf_token}"}}\' hx-swap="outerHTML" class="bg-emerald-100 text-emerald-700 border border-emerald-200 px-3 py-1 rounded-lg text-[10px] font-black uppercase tracking-wider hover:bg-rose-100 hover:text-rose-700 transition-colors"><i class="fa-solid fa-check mr-1"></i> Activo</button>')
            else:
                return HttpResponse(f'<button hx-post="/auth/personal/estado/{user_id}/" hx-headers=\'{{"X-CSRFToken": "{csrf_token}"}}\' hx-swap="outerHTML" class="bg-rose-100 text-rose-700 border border-rose-200 px-3 py-1 rounded-lg text-[10px] font-black uppercase tracking-wider hover:bg-emerald-100 hover:text-emerald-700 transition-colors"><i class="fa-solid fa-ban mr-1"></i> Suspendido</button>')
        except ValueError as e:
            return HttpResponse(f'<span class="text-rose-600 text-[10px] font-black uppercase">{str(e)}</span>')
    return HttpResponse("No autorizado", status=403)

@login_required(login_url='/auth/login/')
def search_staff_view(request):
    if request.user.role not in ['DIRECTOR', 'SUPERUSER']: return HttpResponse("No autorizado", status=403)
    query = request.GET.get('q', '').lower()
    role_filter = request.GET.get('role', '')
    staff = GetStaffListUseCase(DjangoUserRepository()).execute()
    if query: staff = [u for u in staff if query in u.first_name.lower() or query in u.last_name.lower() or query in u.dni]
    if role_filter: staff = [u for u in staff if u.role == role_filter]
    return render(request, 'users/partials/staff_table_rows.html', {'staff': staff})

@login_required(login_url='/auth/login/')
def bulk_permissions_view(request):
    if request.method == 'POST' and request.user.role in ['DIRECTOR', 'SUPERUSER']:
        user_ids = request.POST.getlist('user_ids')
        modules = request.POST.getlist('modules') # Si no marcan nada, esto llega como lista vacía []
        
        user_ids = [int(id) for id in user_ids if id.isdigit()]
        
        repo = DjangoUserRepository()
        try:
            # 1. Guardamos en la base de datos
            BulkUpdatePermissionsUseCase(repo).execute(user_ids, modules)
            
            # 2. CORRECCIÓN: Volvemos a consultar la base de datos para obtener la lista fresca
            # Si hay un filtro activo en la pantalla, lo respetamos
            query = request.GET.get('q', '').lower()
            role_filter = request.GET.get('role', '')
            
            staff = GetStaffListUseCase(repo).execute()
            if query: staff = [u for u in staff if query in u.first_name.lower() or query in u.last_name.lower() or query in u.dni]
            if role_filter: staff = [u for u in staff if u.role == role_filter]
            
            # 3. Devolvemos el HTML con los datos frescos
            return render(request, 'users/partials/staff_table_rows.html', {'staff': staff})
        except ValueError as e:
            return HttpResponse(f"<tr><td colspan='5' class='p-5 text-rose-600 font-bold text-center'>Error: {str(e)}</td></tr>", status=400)
    return HttpResponse("No autorizado", status=403)