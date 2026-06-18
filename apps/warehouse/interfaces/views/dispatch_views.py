from django.shortcuts import render
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from apps.warehouse.infrastructure.repositories.warehouse_repository import DjangoMaterialRepository, DjangoLoanRequestRepository
from apps.warehouse.core.use_cases.manage_loans import UpdateLoanStatusUseCase

@login_required(login_url='/auth/login/')
def dispatch_panel_view(request):
    # PARCHE DE SEGURIDAD: Bloqueo estricto por rol
    if request.user.role not in ['DIRECTOR', 'SUBDIRECTOR', 'APOYO', 'SUPERUSER']:
        return HttpResponseForbidden("Acceso denegado. Esta área es exclusiva para gestión operativa.")

    loan_repo = DjangoLoanRequestRepository()
    active_loans = loan_repo.get_all_active()
    
    return render(request, 'warehouse/dispatch_panel.html', {'loans': active_loans})

@login_required(login_url='/auth/login/')
def update_loan_status_view(request, loan_id):
    # PARCHE DE SEGURIDAD
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
            
            if loan.status == 'DISPATCHED':
                return HttpResponse(f'''
                    <form hx-post="/almacen/despacho/actualizar/{loan.id}/" hx-headers='{{"X-CSRFToken": "{csrf_token}"}}' hx-swap="outerHTML">
                        <input type="hidden" name="status" value="RETURNED">
                        <button type="submit" class="bg-green-600 text-white text-xs font-bold px-3 py-2 rounded-lg hover:bg-green-700 transition-colors">
                            MARCAR DEVUELTO
                        </button>
                    </form>
                ''')
            elif loan.status == 'RETURNED':
                return HttpResponse('<span class="bg-gray-100 text-gray-500 text-xs font-bold px-3 py-2 rounded-lg uppercase">Devuelto (Stock Restaurado)</span>')
                
        except ValueError as e:
            return HttpResponse(f'<span class="text-red-600 text-xs font-bold">{str(e)}</span>')

    return HttpResponse("Método no permitido", status=405)