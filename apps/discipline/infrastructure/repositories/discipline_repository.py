from typing import List
from django.db import transaction
from apps.discipline.core.domain.entities import IncidentEntity, EvidenceEntity
from apps.discipline.core.domain.repositories import IIncidentRepository
from apps.discipline.infrastructure.models import Incident, Evidence

class DjangoIncidentRepository(IIncidentRepository):
    
    def _to_entity(self, model: Incident) -> IncidentEntity:
        evidences = [
            EvidenceEntity(id=e.id, incident_id=e.incident_id, file_path=e.file.name) 
            for e in model.evidences.all()
        ]
        return IncidentEntity(
            id=model.id,
            student_id=model.student_id,
            reported_by_id=model.reported_by_id,
            severity=model.severity,
            subtype=model.subtype,
            description=model.description,
            date_reported=model.date_reported,
            evidences=evidences,
            student_name=f"{model.student.last_name}, {model.student.first_name}",
            reporter_name=f"{model.reported_by.first_name} {model.reported_by.last_name}"
        )

    @transaction.atomic
    def save(self, incident: IncidentEntity) -> IncidentEntity:
        model, _ = Incident.objects.update_or_create(
            id=incident.id,
            defaults={
                'student_id': incident.student_id,
                'reported_by_id': incident.reported_by_id,
                'severity': incident.severity,
                'subtype': incident.subtype,
                'description': incident.description
            }
        )
        incident.id = model.id
        incident.date_reported = model.date_reported

        for ev in incident.evidences:
            Evidence.objects.update_or_create(
                id=ev.id,
                incident=model,
                defaults={'file': ev.file_path}
            )
        return self._to_entity(model)

    def get_by_student(self, student_id: int) -> List[IncidentEntity]:
        # CORRECCIÓN: Añadido order_by('-date_reported') para orden cronológico inverso
        models = Incident.objects.filter(student_id=student_id).prefetch_related('evidences', 'student', 'reported_by').order_by('-date_reported')
        return [self._to_entity(m) for m in models]

    def get_all(self) -> List[IncidentEntity]:
        models = Incident.objects.all().prefetch_related('evidences', 'student', 'reported_by').order_by('-date_reported')
        return [self._to_entity(m) for m in models]

    def get_by_reporter(self, reporter_id: int) -> List[IncidentEntity]:
        models = Incident.objects.filter(reported_by_id=reporter_id).prefetch_related('evidences', 'student', 'reported_by').order_by('-date_reported')
        return [self._to_entity(m) for m in models]