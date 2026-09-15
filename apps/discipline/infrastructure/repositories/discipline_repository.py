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
            occurred_at=model.occurred_at,
            location=model.location,
            other_location=model.other_location,
            category=model.category,
            severity=model.severity,
            subtype=model.subtype,
            description=model.description,
            additional_people=model.additional_people,
            immediate_action=model.immediate_action,
            requires_follow_up=model.requires_follow_up,
            referred_to=model.referred_to,
            additional_observations=model.additional_observations,
            academic_year=model.academic_year,
            additional_student_ids=list(model.additional_students.values_list('id', flat=True)),
            date_reported=model.date_reported,
            evidences=evidences,
            code=model.code,
            status=model.status,
            student_name=f"{model.student.last_name}, {model.student.first_name}",
            section_name=model.student.section.display_name,
            reporter_name=f"{model.reported_by.first_name} {model.reported_by.last_name}",
            category_label=model.get_category_display(),
            subtype_label=model.get_subtype_display(),
            location_label=(model.other_location if model.location == 'OTRO' else model.get_location_display()),
            status_label=model.get_status_display(),
            referred_to_label=model.get_referred_to_display() if model.referred_to else '',
            additional_student_names=[
                f'{student.first_name} {student.last_name}'.strip()
                for student in model.additional_students.all()
            ],
        )

    @transaction.atomic
    def save(self, incident: IncidentEntity) -> IncidentEntity:
        model, _ = Incident.objects.update_or_create(
            id=incident.id,
            defaults={
                'student_id': incident.student_id,
                'reported_by_id': incident.reported_by_id,
                'occurred_at': incident.occurred_at,
                'location': incident.location,
                'other_location': incident.other_location,
                'category': incident.category,
                'severity': incident.severity,
                'subtype': incident.subtype,
                'description': incident.description,
                'additional_people': incident.additional_people,
                'immediate_action': incident.immediate_action,
                'requires_follow_up': incident.requires_follow_up,
                'referred_to': incident.referred_to,
                'additional_observations': incident.additional_observations,
                'academic_year': incident.academic_year,
                'status': 'REGISTRADA' if incident.id is None else incident.status,
            }
        )
        model.additional_students.set(incident.additional_student_ids)
        incident.id = model.id
        incident.code = model.code
        incident.status = model.status
        incident.date_reported = model.date_reported

        for ev in incident.evidences:
            Evidence.objects.update_or_create(
                id=ev.id,
                incident=model,
                defaults={'file': ev.file_path}
            )
        return self._to_entity(model)

    def get_by_student(self, student_id: int) -> List[IncidentEntity]:
        models = Incident.objects.filter(student_id=student_id).select_related(
            'student__section', 'reported_by'
        ).prefetch_related('evidences', 'additional_students').order_by('-occurred_at')
        return [self._to_entity(m) for m in models]

    def get_all(self) -> List[IncidentEntity]:
        models = Incident.objects.all().select_related(
            'student__section', 'reported_by'
        ).prefetch_related('evidences', 'additional_students').order_by('-occurred_at')
        return [self._to_entity(m) for m in models]

    def get_by_reporter(self, reporter_id: int) -> List[IncidentEntity]:
        models = Incident.objects.filter(reported_by_id=reporter_id).select_related(
            'student__section', 'reported_by'
        ).prefetch_related('evidences', 'additional_students').order_by('-occurred_at')
        return [self._to_entity(m) for m in models]
