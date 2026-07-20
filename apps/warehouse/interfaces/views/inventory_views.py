import csv
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from apps.warehouse.infrastructure.repositories.warehouse_repository import DjangoMaterialRepository
from apps.warehouse.core.use_cases.manage_materials import SaveMaterialUseCase, DeleteMaterialUseCase
from apps.warehouse.core.use_cases.import_materials import ImportMaterialUseCase

@login_required(login_url='/auth/login/')
def inventory_panel_view(request):
    if request.user.role not in ['DIRECTOR', 'SUBDIRECTOR', 'APOYO', 'SUPERUSER']:
        return redirect('core:dashboard')

    repo = DjangoMaterialRepository()

    if request.method == 'POST':
        action = request.POST.get('action')

        # --- CREACIÓN MANUAL ---
        if action == 'manual':
            name = request.POST.get('name')
            stock = int(request.POST.get('stock', 0))
            unit = request.POST.get('unit')
            state = request.POST.get('state')
            location = request.POST.get('location')
            cycle = request.POST.get('cycle')
            
            try:
                SaveMaterialUseCase(repo).execute(None, name, stock, unit, state, location, cycle, "")
                messages.success(request, 'Material registrado correctamente.')
            except Exception as e:
                messages.error(request, f'Error al registrar: {str(e)}')
            return redirect('warehouse:inventory_panel')

        # --- CARGA MASIVA (CSV) ---
        elif action == 'csv_upload':
            if 'csv_file' not in request.FILES:
                messages.error(request, 'Debes adjuntar un archivo CSV.')
                return redirect('warehouse:inventory_panel')
                
            csv_file = request.FILES['csv_file']
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'El archivo debe tener extensión .csv')
                return redirect('warehouse:inventory_panel')

            use_case = ImportMaterialUseCase(repo)
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
                            created, _ = use_case.execute(row)
                            if created: creados += 1
                            else: actualizados += 1
                        except ValueError as ve:
                            errores.append(f"Fila {idx}: {str(ve)}")
                            
                messages.success(request, f'Importación exitosa: {creados} creados, {actualizados} actualizados.')
                if errores:
                    for err in errores[:5]:
                        messages.error(request, err)
                        
            except Exception as e:
                messages.error(request, f'Error al procesar el archivo: {str(e)}')
                
            return redirect('warehouse:inventory_panel')

    materials = repo.get_all()
    return render(request, 'warehouse/inventory_panel.html', {'materials': materials})

@login_required(login_url='/auth/login/')
def edit_material_view(request, material_id):
    if request.user.role not in ['DIRECTOR', 'SUBDIRECTOR', 'APOYO', 'SUPERUSER']:
        return redirect('core:dashboard')

    repo = DjangoMaterialRepository()
    material = repo.get_by_id(material_id)

    if not material:
        messages.error(request, "Material no encontrado.")
        return redirect('warehouse:inventory_panel')

    if request.method == 'POST':
        name = request.POST.get('name')
        stock = int(request.POST.get('stock', 0))
        unit = request.POST.get('unit')
        state = request.POST.get('state')
        location = request.POST.get('location')
        cycle = request.POST.get('cycle')
        
        try:
            SaveMaterialUseCase(repo).execute(material_id, name, stock, unit, state, location, cycle, material.pedagogical_use)
            messages.success(request, 'Material actualizado correctamente.')
            return redirect('warehouse:inventory_panel')
        except Exception as e:
            messages.error(request, f'Error al actualizar: {str(e)}')

    return render(request, 'warehouse/edit_material.html', {'material': material})

@login_required(login_url='/auth/login/')
def delete_material_view(request, material_id):
    if request.method == 'POST' and request.user.role in ['DIRECTOR', 'SUBDIRECTOR', 'APOYO', 'SUPERUSER']:
        repo = DjangoMaterialRepository()
        DeleteMaterialUseCase(repo).execute(material_id)
        return HttpResponse("") # HTMX borrará la fila
    return HttpResponse("No autorizado", status=403)