import csv
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.core.files.storage import default_storage # <-- IMPORTACIÓN CORREGIDA
from apps.warehouse.infrastructure.repositories.warehouse_repository import DjangoMaterialRepository
from apps.warehouse.core.use_cases.manage_materials import SaveMaterialUseCase, DeleteMaterialUseCase
from apps.warehouse.core.use_cases.import_materials import ImportMaterialUseCase
from apps.core.file_validation import UploadValidationError, validate_csv_upload, validate_image_upload

@login_required(login_url='/auth/login/')
def inventory_panel_view(request):
    if request.user.role not in ['DIRECTOR', 'SUBDIRECTOR', 'APOYO', 'SUPERUSER']:
        return redirect('core:dashboard')

    repo = DjangoMaterialRepository()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'manual':
            name = request.POST.get('name')
            category = request.POST.get('category', 'General')
            stock = int(request.POST.get('stock', 0))
            unit = request.POST.get('unit')
            state = request.POST.get('state')
            location = request.POST.get('location')
            cycle = request.POST.get('cycle')
            pedagogical_use = request.POST.get('pedagogical_use', '')
            
            image_path = None
            if 'image' in request.FILES:
                file = request.FILES['image']
                try:
                    validate_image_upload(file)
                except UploadValidationError as e:
                    messages.error(request, str(e))
                    return redirect('warehouse:inventory_panel')
                filename = default_storage.save(f'materials/{file.name}', file)
                image_path = filename
            
            try:
                SaveMaterialUseCase(repo).execute(None, name, category, stock, unit, state, location, cycle, pedagogical_use, image_path)
                messages.success(request, 'Material registrado correctamente.')
            except Exception as e:
                if image_path:
                    default_storage.delete(image_path)
                messages.error(request, f'Error al registrar: {str(e)}')
            return redirect('warehouse:inventory_panel')

        elif action == 'csv_upload':
            if 'csv_file' not in request.FILES:
                messages.error(request, 'Debes adjuntar un archivo CSV.')
                return redirect('warehouse:inventory_panel')
                
            csv_file = request.FILES['csv_file']
            try:
                validate_csv_upload(csv_file)
            except UploadValidationError as e:
                messages.error(request, str(e))
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
                    for err in errores[:5]: messages.error(request, err)
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
        category = request.POST.get('category', 'General')
        stock = int(request.POST.get('stock', 0))
        unit = request.POST.get('unit')
        state = request.POST.get('state')
        location = request.POST.get('location')
        cycle = request.POST.get('cycle')
        pedagogical_use = request.POST.get('pedagogical_use', '')
        
        image_path = None
        if 'image' in request.FILES:
            file = request.FILES['image']
            try:
                validate_image_upload(file)
            except UploadValidationError as e:
                messages.error(request, str(e))
                return redirect('warehouse:edit_material', material_id=material_id)
            filename = default_storage.save(f'materials/{file.name}', file)
            image_path = filename
        
        try:
            SaveMaterialUseCase(repo).execute(material_id, name, category, stock, unit, state, location, cycle, pedagogical_use, image_path)
            messages.success(request, 'Material actualizado correctamente.')
            return redirect('warehouse:inventory_panel')
        except Exception as e:
            if image_path:
                default_storage.delete(image_path)
            messages.error(request, f'Error al actualizar: {str(e)}')

    return render(request, 'warehouse/edit_material.html', {'material': material})

@login_required(login_url='/auth/login/')
def delete_material_view(request, material_id):
    if request.method == 'POST' and request.user.role in ['DIRECTOR', 'SUBDIRECTOR', 'APOYO', 'SUPERUSER']:
        repo = DjangoMaterialRepository()
        DeleteMaterialUseCase(repo).execute(material_id)
        return HttpResponse("") 
    return HttpResponse("No autorizado", status=403)
