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
from apps.core.utils import normalize_text
from apps.users.interfaces.middlewares import require_permission


MAX_MATERIAL_IMAGES = 6


def _uploaded_material_images(request):
    """Reúne selección múltiple, captura móvil y el campo legado."""
    return [
        *request.FILES.getlist('images'),
        *request.FILES.getlist('camera_image'),
        *request.FILES.getlist('image'),
    ]


def _validate_material_images(files, existing_count=0):
    if existing_count + len(files) > MAX_MATERIAL_IMAGES:
        raise UploadValidationError(
            f'Cada material admite un máximo de {MAX_MATERIAL_IMAGES} imágenes.'
        )
    for uploaded_file in files:
        validate_image_upload(uploaded_file)


def _store_material_images(files):
    return [
        default_storage.save(f'materials/{uploaded_file.name}', uploaded_file)
        for uploaded_file in files
    ]


@login_required(login_url='/auth/login/')
@require_permission('warehouse.manage')
def inventory_panel_view(request):
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
            
            uploaded_images = _uploaded_material_images(request)
            try:
                _validate_material_images(uploaded_images)
            except UploadValidationError as e:
                messages.error(request, str(e))
                return redirect('warehouse:inventory_panel')

            image_paths = []
            
            try:
                image_paths = _store_material_images(uploaded_images)
                SaveMaterialUseCase(repo).execute(
                    None, name, category, stock, unit, state, location, cycle,
                    pedagogical_use, image_paths,
                )
                messages.success(request, 'Material registrado correctamente.')
            except Exception as e:
                for image_path in image_paths:
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
    raw_query = request.GET.get('q', '').strip()
    query = normalize_text(raw_query)
    if query:
        materials = [
            material for material in materials
            if query in normalize_text(material.name)
            or query in normalize_text(material.category)
            or query in normalize_text(material.location)
        ]
    return render(
        request,
        'warehouse/inventory_panel.html',
        {'materials': materials, 'initial_query': raw_query},
    )

@login_required(login_url='/auth/login/')
@require_permission('warehouse.manage')
def edit_material_view(request, material_id):
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
        
        existing_image_ids = {str(image['id']) for image in material.image_items}
        remove_image_ids = {
            image_id for image_id in request.POST.getlist('remove_image_ids')
            if image_id in existing_image_ids
        }
        uploaded_images = _uploaded_material_images(request)
        try:
            _validate_material_images(
                uploaded_images,
                len(material.image_urls) - len(remove_image_ids),
            )
        except UploadValidationError as e:
            messages.error(request, str(e))
            return redirect('warehouse:edit_material', material_id=material_id)

        image_paths = []
        
        try:
            image_paths = _store_material_images(uploaded_images)
            with transaction.atomic():
                for image_id in remove_image_ids:
                    repo.delete_image(material_id, int(image_id))
                SaveMaterialUseCase(repo).execute(
                    material_id, name, category, stock, unit, state, location, cycle,
                    pedagogical_use, image_paths,
                )
            messages.success(request, 'Material actualizado correctamente.')
            return redirect('warehouse:inventory_panel')
        except Exception as e:
            for image_path in image_paths:
                default_storage.delete(image_path)
            messages.error(request, f'Error al actualizar: {str(e)}')

    return render(request, 'warehouse/edit_material.html', {'material': material})

@login_required(login_url='/auth/login/')
@require_permission('warehouse.manage')
def delete_material_view(request, material_id):
    if request.method == 'POST':
        repo = DjangoMaterialRepository()
        DeleteMaterialUseCase(repo).execute(material_id)
        return HttpResponse("") 
    return HttpResponse("Método no permitido", status=405)
