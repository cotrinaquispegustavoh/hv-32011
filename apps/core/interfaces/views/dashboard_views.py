from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.core.core.use_cases.manage_dashboards import GetDirectorMetricsUseCase

@login_required(login_url='/auth/login/')
def dashboard_view(request):
    user = request.user
    context = {
        'role': user.role,
        'name': user.first_name or 'Usuario'
    }

    # Si es directivo, cargamos las métricas
    if user.role in ['DIRECTOR', 'SUBDIRECTOR', 'SUPERUSER']:
        use_case = GetDirectorMetricsUseCase()
        context['metrics'] = use_case.execute()

    return render(request, 'core/dashboard.html', context)