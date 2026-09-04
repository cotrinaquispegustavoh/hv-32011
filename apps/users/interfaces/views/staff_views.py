import csv
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from apps.users.infrastructure.repositories.user_repository import DjangoUserRepository
from apps.users.core.use_cases.manage_users import GetStaffListUseCase, ToggleUserStatusUseCase, BulkUpdatePermissionsUseCase
from apps.users.core.use_cases.import_staff import ImportStaffUseCase
from apps.core.file_validation import UploadValidationError, validate_csv_upload
from apps.core.utils import normalize_text
from apps.users.permissions import (
    ALL_PERMISSION_CODES,
    permission_groups_for,
    permissions_for_edit,
    sanitize_explicit_permissions,
)


def _staff_detail_context(user_detail):
    return {
        'selected_user': user_detail,
        'permission_groups': permission_groups_for(user_detail) if user_detail else [],
    }

@login_required(login_url='/auth/login/')
def staff_list_view(request):
    if request.user.role not in ['DIRECTOR', 'SUPERUSER']: return redirect('core:dashboard')
    repo = DjangoUserRepository()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'manual_create':
            dni = request.POST.get('dni')
            nombres = request.POST.get('nombres')
            apellidos = request.POST.get('apellidos')
            correo = request.POST.get('correo')
            rol = request.POST.get('rol')
            cargo = request.POST.get('cargo_especifico')
            
            row_data = {'dni': dni, 'nombres': nombres, 'apellidos': apellidos, 'correo': correo, 'rol': rol, 'cargo_especifico': cargo}
            try:
                created, name = ImportStaffUseCase(repo).execute(row_data)
                if created: messages.success(request, f'Usuario {name} creado con éxito.')
                else: messages.success(request, f'Usuario {name} actualizado.')
            except ValueError as e:
                messages.error(request, str(e))
            return redirect('users:staff_list')

        elif action == 'csv_upload':
            if 'csv_file' not in request.FILES:
                messages.error(request, 'Debes adjuntar un archivo CSV.')
                return redirect('users:staff_list')
                
            csv_file = request.FILES['csv_file']
            try:
                validate_csv_upload(csv_file)
            except UploadValidationError as e:
                messages.error(request, str(e))
                return redirect('users:staff_list')

            use_case = ImportStaffUseCase(repo)
            creados, actualizados = 0, 0
            errores = []

            try:
                decoded_file = csv_file.read().decode('utf-8-sig').splitlines()
                delimiter = ';'
                if decoded_file and '\t' in decoded_file[0]: delimiter = '\t'
                elif decoded_file and ';' not in decoded_file[0] and ',' in decoded_file[0]: delimiter = ','

                reader = csv.DictReader(decoded_file, delimiter=delimiter)
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
                    for err in errores[:5]: messages.error(request, err)
            except Exception as e:
                messages.error(request, f'Error al procesar el archivo: {str(e)}')
                
            return redirect('users:staff_list')

    staff = GetStaffListUseCase(repo).execute()
    first_user = staff[0] if staff else None
    return render(
        request,
        'users/staff_list.html',
        {
            'staff': staff,
            **_staff_detail_context(first_user),
            'bulk_permission_groups': permission_groups_for(first_user) if first_user else [],
        },
    )

@login_required(login_url='/auth/login/')
def search_staff_view(request):
    if request.user.role not in ['DIRECTOR', 'SUPERUSER']: return HttpResponse("No autorizado", status=403)
    query = normalize_text(request.GET.get('q', ''))
    role_filter = request.GET.get('role', '')
    staff = GetStaffListUseCase(DjangoUserRepository()).execute()
    if query: staff = [u for u in staff if query in normalize_text(u.first_name) or query in normalize_text(u.last_name) or query in normalize_text(u.dni)]
    if role_filter: staff = [u for u in staff if u.role == role_filter]
    
    # CORRECCIÓN: Aseguramos que devuelva staff_list_items.html (DIVs) y no staff_table_rows (TRs)
    return render(request, 'users/partials/staff_list_items.html', {'staff': staff})

@login_required(login_url='/auth/login/')
def staff_detail_view(request, user_id):
    if request.user.role not in ['DIRECTOR', 'SUPERUSER']: return HttpResponse("No autorizado", status=403)
    repo = DjangoUserRepository()
    user_detail = repo.get_by_id(user_id)
    return render(request, 'users/partials/staff_detail.html', _staff_detail_context(user_detail))

@login_required(login_url='/auth/login/')
def toggle_module_permission_view(request, user_id):
    if request.method == 'POST' and request.user.role in ['DIRECTOR', 'SUPERUSER']:
        permission = request.POST.get('permission')
        if permission not in ALL_PERMISSION_CODES:
            return HttpResponse("Permiso no válido", status=400)
        repo = DjangoUserRepository()
        user_entity = repo.get_by_id(user_id)
        if user_entity:
            if user_entity.role == 'SUPERUSER':
                return HttpResponse("Los permisos técnicos no se pueden modificar.", status=400)
            perms = permissions_for_edit(user_entity)
            if permission in perms:
                perms.remove(permission)
            else:
                perms.append(permission)
            user_entity.module_permissions = perms
            repo.save(user_entity)
        return staff_detail_view(request, user_id)
    return HttpResponse("No autorizado", status=403)

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
        permissions = sanitize_explicit_permissions(request.POST.getlist('permissions'))
        user_ids = [int(id) for id in user_ids if id.isdigit()]
        repo = DjangoUserRepository()
        try:
            BulkUpdatePermissionsUseCase(repo).execute(user_ids, permissions)
            query = normalize_text(request.POST.get('q', ''))
            role_filter = request.POST.get('role', '')
            staff = GetStaffListUseCase(repo).execute()
            if query: staff = [u for u in staff if query in normalize_text(u.first_name) or query in normalize_text(u.last_name) or query in normalize_text(u.dni)]
            if role_filter: staff = [u for u in staff if u.role == role_filter]
            
            # CORRECCIÓN: Aseguramos que devuelva staff_list_items.html
            return render(request, 'users/partials/staff_list_items.html', {'staff': staff})
        except ValueError as e:
            return HttpResponse(f"<div class='p-5 text-red-600 font-bold text-center'>Error: {str(e)}</div>", status=400)
    return HttpResponse("No autorizado", status=403)
