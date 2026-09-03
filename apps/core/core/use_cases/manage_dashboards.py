from typing import Dict, Any
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from apps.users.infrastructure.models import User
from apps.academics.infrastructure.models import Student
from apps.discipline.infrastructure.models import Incident
from apps.warehouse.infrastructure.models import Material, LoanRequest
from apps.portfolio.infrastructure.models import PortfolioItem
from apps.core.infrastructure.models import InternalNotification
from apps.assignments.infrastructure.models import TeacherAssignment

class GetDirectorMetricsUseCase:
    def execute(self, user_id: int) -> Dict[str, Any]:
        today = timezone.now().date()
        seven_days_ago = today - timedelta(days=6)
        thirty_days_ago = today - timedelta(days=29)
        
        total_students = Student.objects.count()
        active_teachers = User.objects.filter(role='DOCENTE', is_active=True).count()
        pending_loans = LoanRequest.objects.filter(status='PENDING').count()
        incidents_today = Incident.objects.filter(date_reported__date=today).count()
        available_materials = Material.objects.aggregate(total=Sum('stock'))['total'] or 0

        loans_qs = LoanRequest.objects.filter(request_date__date__gte=thirty_days_ago) \
            .annotate(date=TruncDate('request_date')) \
            .values('date') \
            .annotate(count=Count('id')) \
            .order_by('date')
        
        chart_labels = []
        chart_data = []
        loans_dict = {item['date']: item['count'] for item in loans_qs}
        
        for i in range(29, -1, -1):
            d = today - timedelta(days=i)
            chart_labels.append(d.strftime('%d %b'))
            chart_data.append(loans_dict.get(d, 0))

        def get_incident_counts(start_date):
            qs = Incident.objects.filter(date_reported__date__gte=start_date).values('severity').annotate(count=Count('id'))
            counts = {'LEVE': 0, 'MODERADA': 0, 'GRAVE': 0}
            total = 0
            for item in qs:
                if item['severity'] in counts:
                    counts[item['severity']] = item['count']
                    total += item['count']
            return {'counts': counts, 'total': total}

        incidents_data = {
            '1': get_incident_counts(today),
            '7': get_incident_counts(seven_days_ago),
            '30': get_incident_counts(thirty_days_ago),
        }

        alerts = InternalNotification.objects.filter(user_id=user_id).order_by('-created_at')[:5]
        upcoming_birthdays = User.objects.filter(is_active=True, birth_date__month=today.month, birth_date__day__gte=today.day).order_by('birth_date__day')[:3]

        return {
            'top_cards': {
                'students': total_students,
                'teachers': active_teachers,
                'pending_loans': pending_loans,
                'incidents_today': incidents_today,
                'available_materials': available_materials
            },
            'chart_loans': {
                'labels': chart_labels,
                'data': chart_data
            },
            'chart_incidents': incidents_data,
            'alerts': alerts,
            'upcoming_birthdays': upcoming_birthdays
        }

class GetTeacherMetricsUseCase:
    def execute(self, user_id: int) -> Dict[str, Any]:
        today = timezone.now().date()
        current_year = today.year 
        
        my_sections = TeacherAssignment.objects.filter(teacher_id=user_id, academic_year=current_year).count()
        pending_loans = LoanRequest.objects.filter(teacher_id=user_id, status='PENDING').count()
        my_incidents = Incident.objects.filter(reported_by_id=user_id).count()
        my_portfolio = PortfolioItem.objects.filter(teacher_id=user_id).count()
        
        latest_loan = LoanRequest.objects.filter(teacher_id=user_id).prefetch_related('details__material').order_by('-request_date').first()
        
        return {
            'top_cards': {
                'sections': my_sections,
                'pending_loans': pending_loans,
                'incidents': my_incidents,
                'portfolio': my_portfolio
            },
            'latest_loan': latest_loan,
        }
