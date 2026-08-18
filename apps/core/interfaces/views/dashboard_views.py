from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from apps.core.core.use_cases.manage_dashboards import GetDirectorMetricsUseCase, GetTeacherMetricsUseCase
from apps.core.infrastructure.repositories.core_repository import DjangoNotificationRepository
from apps.core.core.use_cases.manage_notifications import MarkNotificationsReadUseCase

@login_required(login_url='/auth/login/')
def dashboard_view(request):
    user = request.user
    
    if user.role == 'APODERADO':
        return redirect('academics:parent_dashboard')
        
    context = {
        'role': user.role,
        'name': user.first_name or 'Usuario'
    }

    if user.role in ['DIRECTOR', 'SUBDIRECTOR', 'SUPERUSER']:
        use_case = GetDirectorMetricsUseCase()
        context['metrics'] = use_case.execute(user.id)
        
    # --- NUEVO: Cargar métricas si es Docente ---
    elif user.role == 'DOCENTE':
        use_case = GetTeacherMetricsUseCase()
        context['metrics'] = use_case.execute(user.id)

    return render(request, 'core/dashboard.html', context)

@login_required(login_url='/auth/login/')
def mark_notifications_read_view(request):
    if request.method == 'POST':
        repo = DjangoNotificationRepository()
        MarkNotificationsReadUseCase(repo).execute(request.user.id)
        return HttpResponse("") # HTMX no necesita recargar la página, Alpine ocultará la campanita
    return HttpResponseForbidden()