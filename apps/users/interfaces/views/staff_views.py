import csv
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from apps.users.infrastructure.repositories.user_repository import DjangoUserRepository
from apps.users.core.use_cases.manage_users import GetStaffListUseCase, ToggleUserStatusUseCase, BulkUpdatePermissionsUseCase
from apps.users.core.use_cases.import_staff import ImportStaffUseCase
from apps.core.utils import normalize_text

@login_required(login_url='/auth/login/')
def staff_list_view(request):
    if request.user.role not in ['DIRECTOR', 'SUPERUSER']: return redirect('core:dashboard')
    repo = DjangoUserRepository()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'csv_upload':
            if 'csv_file' not in request.FILES:
                messages.error(request, 'Debes adjuntar un archivo CSV.')
                return redirect('users:staff_list')
                
            csv_file = request.FILES['csv_file']
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'El archivo debe tener extensión .csv')
                return redirect('users:staff_list')

            use_case = ImportStaffUseCase(repo)
            creados, actualizados = 0, 0
            errores = []

            try:
                decoded_file = csv_file.read().decode('utf-8-sig').splitlines()
                reader = csv.DictReader(decoded_file, delimiter=';')
                
                if reader.fieldnames:
                    reader.fieldnames = [str(c).strip().lower().replace(' ', '_') for c in reader.fieldnames if c]

                with transaction.atomic():
                    for idx, row in enumerate(reader, start=2):
                        try:
                            created, name = use_case.execute(row)
                            if created: creados += 1
                            else: actualizados += 1
                        except ValueError as ve:
                            errores.append(f"Fila {idx}: {str(ve)}")
                            
                messages.success(request, f'Importación exitosa: {creados} usuarios nuevos, {actualizados} actualizados.')
                if errores:
                    for err in errores[:5]:
                        messages.error(request, err)
            except Exception as e:
                messages.error(request, f'Error al procesar el archivo: {str(e)}')
                
            return redirect('users:staff_list')

    staff = GetStaffListUseCase(repo).execute()
    return render(request, 'users/staff_list.html', {'staff': staff})

@login_required(login_url='/auth/login/')
def search_staff_view(request):
    if request.user.role not in ['DIRECTOR', 'SUPERUSER']: return HttpResponse("No autorizado", status=403)
    query = normalize_text(request.GET.get('q', ''))
    role_filter = request.GET.get('role', '')
    
    staff = GetStaffListUseCase(DjangoUserRepository()).execute()
    if query: staff = [u for u in staff if query in normalize_text(u.first_name) or query in normalize_text(u.last_name) or query in normalize_text(u.dni)]
    if role_filter: staff = [u for u in staff if u.role == role_filter]
    
    # CORRECCIÓN: Devolvemos las filas de la tabla (<tr>) y no los divs
    return render(request, 'users/partials/staff_table_rows.html', {'staff': staff})

@login_required(login_url='/auth/login/')
def toggle_status_view(request, user_id):
    if request.method == 'POST' and request.user.role in ['DIRECTOR', 'SUPERUSER']:
        repo = DjangoUserRepository()
        try:
            is_active = ToggleUserStatusUseCase(repo).execute(user_id, request.user.id)
            csrf_token = request.META.get('CSRF_COOKIE', '')
            if is_active:
                return HttpResponse(f'<button hx-post="/auth/personal/estado/{user_id}/" hx-headers=\'{{"X-CSRFToken": "{csrf_token}"}}\' hx-swap="outerHTML" class="bg-emerald-50 text-emerald-600 border border-emerald-200 px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-wider hover:bg-red-50 hover:text-red-600 hover:border-red-200 transition-colors shadow-sm"><i class="fa-solid fa-check mr-1"></i> Activo</button>')
            else:
                return HttpResponse(f'<button hx-post="/auth/personal/estado/{user_id}/" hx-headers=\'{{"X-CSRFToken": "{csrf_token}"}}\' hx-swap="outerHTML" class="bg-red-50 text-red-600 border border-red-200 px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-wider hover:bg-emerald-50 hover:text-emerald-600 hover:border-emerald-200 transition-colors shadow-sm"><i class="fa-solid fa-ban mr-1"></i> Suspendido</button>')
        except ValueError as e:
            return HttpResponse(f'<span class="text-red-600 text-[10px] font-black uppercase">{str(e)}</span>')
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
            return HttpResponse(f"<tr><td colspan='5' class='p-5 text-red-600 font-bold text-center'>Error: {str(e)}</td></tr>", status=400)
    return HttpResponse("No autorizado", status=403)

# --- Mantenemos estas funciones por si en el futuro queremos usar el diseño Maestro-Detalle ---
@login_required(login_url='/auth/login/')
def staff_detail_view(request, user_id):
    if request.user.role not in ['DIRECTOR', 'SUPERUSER']: return HttpResponse("No autorizado", status=403)
    repo = DjangoUserRepository()
    user_detail = repo.get_by_id(user_id)
    return render(request, 'users/partials/staff_detail.html', {'selected_user': user_detail})

@login_required(login_url='/auth/login/')
def toggle_module_permission_view(request, user_id):
    if request.method == 'POST' and request.user.role in ['DIRECTOR', 'SUPERUSER']:
        module = request.POST.get('module')
        repo = DjangoUserRepository()
        user_entity = repo.get_by_id(user_id)
        if user_entity:
            perms = list(user_entity.module_permissions)
            if module in perms: perms.remove(module)
            else: perms.append(module)
            user_entity.module_permissions = perms
            repo.save(user_entity)
        return staff_detail_view(request, user_id)
    return HttpResponse("No autorizado", status=403)