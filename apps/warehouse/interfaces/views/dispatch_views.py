from django.shortcuts import render
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.utils.html import escape
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from apps.warehouse.infrastructure.repositories.warehouse_repository import DjangoMaterialRepository, DjangoLoanRequestRepository
from apps.warehouse.core.use_cases.manage_loans import UpdateLoanStatusUseCase
from apps.users.interfaces.middlewares import require_permission

@login_required(login_url='/auth/login/')
@require_permission('warehouse.dispatch')
def dispatch_panel_view(request):
    loan_repo = DjangoLoanRequestRepository()
    active_loans = loan_repo.get_all_active()
    return render(request, 'warehouse/dispatch_panel.html', {'loans': active_loans})

@login_required(login_url='/auth/login/')
@require_permission('warehouse.dispatch')
def update_loan_status_view(request, loan_id):
    if request.method == 'POST':
        new_status = request.POST.get('status')
        material_repo = DjangoMaterialRepository()
        loan_repo = DjangoLoanRequestRepository()
        use_case = UpdateLoanStatusUseCase(material_repo, loan_repo)
        
        try:
            loan = use_case.execute(loan_id, new_status)
            csrf_token = request.META.get('CSRF_COOKIE', '')
            
            # --- MAGIA EN TIEMPO REAL: Avisar a los docentes que el stock cambió ---
            if loan.status in ['RETURNED', 'CANCELLED']:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    "teachers_group",
                    {"type": "send_alert", "alert_type": "stock_update"}
                )
            # -----------------------------------------------------------------------
            
            if loan.status == 'DISPATCHED':
                return HttpResponse(f'''
                    <form hx-post="/almacen/despacho/actualizar/{loan.id}/" hx-target="#action-cell-{loan.id}" hx-swap="innerHTML" hx-headers='{{"X-CSRFToken": "{csrf_token}"}}'>
                        <input type="hidden" name="status" value="RETURNED">
                        <button type="submit" class="ui-button w-full bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-600 hover:text-white text-xs">
                            <i class="fa-solid fa-box-open mr-1" aria-hidden="true"></i> Recibir devolución
                        </button>
                    </form>
                ''')
            elif loan.status == 'RETURNED':
                return HttpResponse('<span class="ui-badge bg-gray-100 text-gray-600 border-gray-200"><i class="fa-solid fa-check-double" aria-hidden="true"></i> Devuelto</span>')
            elif loan.status == 'CANCELLED':
                return HttpResponse('<span class="ui-badge bg-red-50 text-red-700 border-red-200"><i class="fa-solid fa-ban" aria-hidden="true"></i> Rechazado</span>')
                
        except ValueError as e:
            return HttpResponse(f'<span class="text-red-600 text-xs font-bold">{escape(str(e))}</span>')

    return HttpResponse("Método no permitido", status=405)
