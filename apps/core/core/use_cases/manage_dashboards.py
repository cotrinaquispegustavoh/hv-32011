from typing import Dict, Any
from django.utils import timezone
from datetime import timedelta
from apps.users.infrastructure.models import User
from apps.academics.infrastructure.models import Student
from apps.discipline.infrastructure.models import Incident
from apps.warehouse.infrastructure.models import Material, LoanRequest
from apps.portfolio.infrastructure.models import PortfolioItem
from apps.core.infrastructure.models import InstitutionalEvent

class GetDirectorMetricsUseCase:
    def execute(self) -> Dict[str, Any]:
        today = timezone.now().date()
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        # 1. Métricas Base
        total_students = Student.objects.count()
        incidents_today = Incident.objects.filter(date_reported__date=today).count()
        critical_materials = Material.objects.filter(stock__lte=5).count()
        active_teachers = User.objects.filter(role='DOCENTE', is_active=True).count()

        # 2. NUEVO: Materiales en circulación (Despachados pero no devueltos)
        active_loans = LoanRequest.objects.filter(status='DISPATCHED').count()

        # 3. NUEVO: Fichas de Portafolio recientes (últimos 30 días)
        recent_portfolios = PortfolioItem.objects.filter(created_at__gte=thirty_days_ago).count()

        # 4. NUEVO: Próximos Eventos (Agenda)
        upcoming_events = InstitutionalEvent.objects.filter(event_date__gte=today).order_by('event_date')[:3]

        return {
            'total_students': total_students,
            'incidents_today': incidents_today,
            'critical_materials': critical_materials,
            'active_teachers': active_teachers,
            'active_loans': active_loans,
            'recent_portfolios': recent_portfolios,
            'upcoming_events': upcoming_events
        }