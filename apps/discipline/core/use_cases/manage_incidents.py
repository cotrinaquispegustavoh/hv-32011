from typing import List
from apps.discipline.core.domain.entities import IncidentEntity, EvidenceEntity
from apps.discipline.core.domain.repositories import IIncidentRepository

class ReportIncidentUseCase:
    def __init__(self, incident_repo: IIncidentRepository):
        self.incident_repo = incident_repo

    def execute(self, student_id: int, reported_by_id: int, severity: str, subtype: str, description: str, evidence_paths: List[str]) -> IncidentEntity:
        evidences = [
            EvidenceEntity(id=None, incident_id=0, file_path=path) 
            for path in evidence_paths
        ]
        
        incident = IncidentEntity(
            id=None,
            student_id=student_id,
            reported_by_id=reported_by_id,
            severity=severity,
            subtype=subtype,
            description=description,
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