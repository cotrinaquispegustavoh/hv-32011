from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from apps.users.interfaces.middlewares import require_module_permission
from apps.warehouse.infrastructure.repositories.warehouse_repository import DjangoMaterialRepository, DjangoLoanRequestRepository
from apps.warehouse.core.use_cases.manage_loans import CreateLoanRequestUseCase, GetTeacherLoansUseCase
from apps.core.infrastructure.repositories.core_repository import DjangoNotificationRepository
from apps.core.core.use_cases.manage_notifications import NotifyAdminsUseCase

@login_required(login_url='/auth/login/')
@require_module_permission('almacen')
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
                teacher_id=teacher_id, items=[(material_id, quantity)], 
                required_for=required_for, expected_return_date=expected_return_date
            )
            
            notif_repo = DjangoNotificationRepository()
            NotifyAdminsUseCase(notif_repo).execute(
                title="Nueva Solicitud de Material",
                message=f"Un docente ha solicitado materiales. Revisa el panel de despacho.",
                link="/almacen/despacho/"
            )

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "directors_group",
                {
                    "type": "send_alert", "alert_type": "new_loan",
                    "message": f"Nueva solicitud de material pendiente de despacho.", "severity": "LEVE" 
                }
            )

            response = HttpResponse('<span class="text-green-600 font-bold text-sm bg-green-50 px-3 py-2 rounded-xl block text-center mt-2">¡Pedido Confirmado!</span>')
            response['HX-Refresh'] = 'true'
            return response
            
        except ValueError as e:
            return HttpResponse(f'<span class="text-red-600 font-bold text-xs">{str(e)}</span>')
            
    return HttpResponse("Método no permitido", status=405)

# --- NUEVA VISTA: Historial de Solicitudes del Docente ---
@login_required(login_url='/auth/login/')
@require_module_permission('almacen')
def teacher_loans_view(request):
    if request.user.role != 'DOCENTE':
        return redirect('core:dashboard')
        
    repo = DjangoLoanRequestRepository()
    use_case = GetTeacherLoansUseCase(repo)
    loans = use_case.execute(request.user.id)
    
    return render(request, 'warehouse/loan_list.html', {'loans': loans})