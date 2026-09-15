from typing import List
from apps.discipline.core.domain.entities import IncidentEntity, EvidenceEntity
from apps.discipline.core.domain.repositories import IIncidentRepository

class ReportIncidentUseCase:
    def __init__(self, incident_repo: IIncidentRepository):
        self.incident_repo = incident_repo

    def execute(
        self,
        *,
        student_id: int,
        reported_by_id: int,
        occurred_at,
        location: str,
        other_location: str,
        category: str,
        severity: str,
        subtype: str,
        description: str,
        additional_people: str,
        immediate_action: str,
        requires_follow_up: bool,
        referred_to: str,
        additional_observations: str,
        academic_year: int,
        additional_student_ids: List[int],
        evidence_paths: List[str],
    ) -> IncidentEntity:
        evidences = [
            EvidenceEntity(id=None, incident_id=0, file_path=path) 
            for path in evidence_paths
        ]
        
        incident = IncidentEntity(
            id=None,
            student_id=student_id,
            reported_by_id=reported_by_id,
            occurred_at=occurred_at,
            location=location,
            other_location=other_location,
            category=category,
            severity=severity,
            subtype=subtype,
            description=description,
            additional_people=additional_people,
            immediate_action=immediate_action,
            requires_follow_up=requires_follow_up,
            referred_to=referred_to,
            additional_observations=additional_observations,
            academic_year=academic_year,
            additional_student_ids=additional_student_ids,
            evidences=evidences
        )
        
        return self.incident_repo.save(incident)

class GetAllIncidentsUseCase:
    def __init__(self, incident_repo: IIncidentRepository):
        self.incident_repo = incident_repo

    def execute(self) -> List[IncidentEntity]:
        return self.incident_repo.get_all()
    
class GetTeacherIncidentsUseCase:
    def __init__(self, incident_repo: IIncidentRepository):
        self.incident_repo = incident_repo

    def execute(self, reporter_id: int) -> List[IncidentEntity]:
        return self.incident_repo.get_by_reporter(reporter_id)
