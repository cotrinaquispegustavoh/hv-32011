from typing import Dict, Any
from django.utils import timezone
from apps.users.infrastructure.models import User
from apps.academics.infrastructure.models import Student
from apps.discipline.infrastructure.models import Incident
from apps.warehouse.infrastructure.models import Material

class GetDirectorMetricsUseCase:
    def execute(self) -> Dict[str, Any]:
        today = timezone.now().date()
        
        # 1. Total de Alumnos
        total_students = Student.objects.count()
        
        # 2. Incidencias de hoy
        incidents_today = Incident.objects.filter(date_reported__date=today).count()
        
        # 3. Materiales en stock crítico (menor o igual a 5)
        critical_materials = Material.objects.filter(stock__lte=5).count()
        
        # 4. Total de Docentes activos
        active_teachers = User.objects.filter(role='DOCENTE', is_active=True).count()

        return {
            'total_students': total_students,
            'incidents_today': incidents_today,
            'critical_materials': critical_materials,
            'active_teachers': active_teachers
        }