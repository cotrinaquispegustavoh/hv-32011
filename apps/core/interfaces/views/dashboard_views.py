from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from apps.core.core.use_cases.manage_dashboards import GetDirectorMetricsUseCase

@login_required(login_url='/auth/login/')
def dashboard_view(request):
    user = request.user
    
    # CORRECCIÓN: Si es apoderado, lo mandamos a su propio panel
    if user.role == 'APODERADO':
        return redirect('academics:parent_dashboard')
        
    context = {
        'role': user.role,
        'name': user.first_name or 'Usuario'
    }

    if user.role in ['DIRECTOR', 'SUBDIRECTOR', 'SUPERUSER']:
        use_case = GetDirectorMetricsUseCase()
        context['metrics'] = use_case.execute()

    return render(request, 'core/dashboard.html', context)