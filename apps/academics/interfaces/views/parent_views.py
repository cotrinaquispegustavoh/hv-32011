from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from apps.academics.infrastructure.models import Parent, Student
from apps.discipline.infrastructure.repositories.discipline_repository import DjangoIncidentRepository
from apps.portfolio.infrastructure.repositories.portfolio_repository import DjangoPortfolioRepository
from apps.core.infrastructure.models import InstitutionalEvent

@login_required(login_url='/auth/login/')
def parent_dashboard_view(request):
    if request.user.role != 'APODERADO':
        return redirect('core:dashboard')
    
    try:
        parent = Parent.objects.get(user=request.user)
        children = Student.objects.filter(parent=parent).select_related('section')
    except Parent.DoesNotExist:
        children = []

    # Añadimos los próximos eventos para que el padre esté informado
    upcoming_events = InstitutionalEvent.objects.filter(event_date__gte=timezone.now().date()).order_by('event_date')[:4]

    return render(request, 'academics/parent_dashboard.html', {
        'children': children,
        'upcoming_events': upcoming_events
    })

@login_required(login_url='/auth/login/')
def child_detail_view(request, student_id):
    if request.user.role != 'APODERADO':
        return redirect('core:dashboard')
    
    try:
        parent = Parent.objects.get(user=request.user)
        child = Student.objects.select_related('section').get(id=student_id, parent=parent)
    except (Parent.DoesNotExist, Student.DoesNotExist):
        return redirect('academics:parent_dashboard')

    incident_repo = DjangoIncidentRepository()
    incidents = incident_repo.get_by_student(child.id)

    portfolio_repo = DjangoPortfolioRepository()
    portfolio_items = portfolio_repo.get_by_section(child.section_id)

    context = {
        'child': child,
        'incidents': incidents,
        'portfolio_items': portfolio_items
    }
    return render(request, 'academics/child_detail.html', context)