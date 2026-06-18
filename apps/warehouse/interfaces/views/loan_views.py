from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from apps.warehouse.infrastructure.repositories.warehouse_repository import DjangoMaterialRepository, DjangoLoanRequestRepository
from apps.warehouse.core.use_cases.manage_loans import CreateLoanRequestUseCase

@login_required(login_url='/auth/login/')
def request_material_view(request, material_id):
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        required_for = request.POST.get('required_for')
        expected_return_date = request.POST.get('expected_return_date')
        teacher_id = request.user.id

        if not required_for or not expected_return_date:
            return HttpResponse('<span class="text-red-600 font-bold text-xs">Faltan fechas.</span>')

        material_repo = DjangoMaterialRepository()
        loan_repo = DjangoLoanRequestRepository()
        use_case = CreateLoanRequestUseCase(material_repo, loan_repo)

        try:
            use_case.execute(
                teacher_id=teacher_id, 
                items=[(material_id, quantity)], 
                required_for=required_for,
                expected_return_date=expected_return_date
            )
            
            # CORRECCIÓN: Enviamos el mensaje de éxito Y disparamos el evento para recargar el catálogo
            response = HttpResponse('<span class="text-green-600 font-bold text-sm bg-green-50 px-3 py-2 rounded-xl block text-center mt-2">¡Pedido Confirmado!</span>')
            response['HX-Trigger'] = 'actualizarCatalogo'
            return response
            
        except ValueError as e:
            return HttpResponse(f'<span class="text-red-600 font-bold text-xs">{str(e)}</span>')
            
    return HttpResponse("Método no permitido", status=405)