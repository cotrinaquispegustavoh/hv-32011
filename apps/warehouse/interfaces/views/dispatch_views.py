from django.shortcuts import render
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.utils.html import escape
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from apps.warehouse.infrastructure.repositories.warehouse_repository import DjangoMaterialRepository, DjangoLoanRequestRepository
from apps.warehouse.core.use_cases.manage_loans import UpdateLoanStatusUseCase

@login_required(login_url='/auth/login/')
def dispatch_panel_view(request):
    if request.user.role not in ['DIRECTOR', 'SUBDIRECTOR', 'APOYO', 'SUPERUSER']:
        return HttpResponseForbidden("Acceso denegado.")
    loan_repo = DjangoLoanRequestRepository()
    active_loans = loan_repo.get_all_active()
    return render(request, 'warehouse/dispatch_panel.html', {'loans': active_loans})

@login_required(login_url='/auth/login/')
def update_loan_status_view(request, loan_id):
    if request.user.role not in ['DIRECTOR', 'SUBDIRECTOR', 'APOYO', 'SUPERUSER']:
        return HttpResponseForbidden("Acceso denegado.")

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
                        <button type="submit" class="w-full bg-emerald-100 text-emerald-700 border border-emerald-200 text-xs font-black px-4 py-2.5 rounded-xl hover:bg-emerald-600 hover:text-white transition-colors shadow-sm uppercase tracking-wider">
                            <i class="fa-solid fa-box-open mr-1"></i> Recibir Devolución
                        </button>
                    </form>
                ''')
            elif loan.status == 'RETURNED':
                return HttpResponse('<span class="bg-gray-100 text-gray-500 border border-gray-200 text-[10px] font-black px-3 py-2 rounded-lg uppercase block text-center"><i class="fa-solid fa-check-double mr-1"></i> Devuelto</span>')
            elif loan.status == 'CANCELLED':
                return HttpResponse('<span class="bg-red-50 text-red-600 border border-red-100 text-[10px] font-black px-3 py-2 rounded-lg uppercase block text-center"><i class="fa-solid fa-ban mr-1"></i> Rechazado</span>')
                
        except ValueError as e:
            return HttpResponse(f'<span class="text-red-600 text-xs font-bold">{escape(str(e))}</span>')

    return HttpResponse("Método no permitido", status=405)
