from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from datetime import datetime
from apps.core.infrastructure.repositories.core_repository import DjangoEventRepository
from apps.core.core.use_cases.manage_events import GetCalendarEventsUseCase

@login_required(login_url='/auth/login/')
def calendar_view(request):
    """Renderiza la pantalla del calendario."""
    return render(request, 'core/calendar.html')

@login_required(login_url='/auth/login/')
def api_calendar_events(request):
    """API que FullCalendar llama automáticamente para obtener los eventos del mes."""
    start_str = request.GET.get('start')
    end_str = request.GET.get('end')
    
    if start_str and end_str:
        # FullCalendar envía fechas ISO (ej. 2026-08-01T00:00:00Z)
        start_date = datetime.fromisoformat(start_str.replace('Z', '')).date()
        end_date = datetime.fromisoformat(end_str.replace('Z', '')).date()
    else:
        start_date = datetime.now().date()
        end_date = datetime.now().date()

    repo = DjangoEventRepository()
    events = GetCalendarEventsUseCase(repo).execute(start_date, end_date)
    
    # Formateamos los datos exactamente como FullCalendar los exige
    events_data = []
    for ev in events:
        events_data.append({
            'id': ev.id,
            'title': ev.title,
            'start': ev.event_date.isoformat(),
            'allDay': True,
            # Estética: Rojo para feriados, Azul para eventos normales
            'backgroundColor': '#EF4444' if ev.is_holiday else '#2563EB',
            'borderColor': '#EF4444' if ev.is_holiday else '#2563EB',
            'extendedProps': {
                'description': ev.description,
                'is_holiday': ev.is_holiday
            }
        })
        
    return JsonResponse(events_data, safe=False)