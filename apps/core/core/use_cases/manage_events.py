from typing import List
from apps.core.core.domain.entities import EventEntity
from apps.core.core.domain.repositories import IEventRepository

class GetPublicEventsUseCase:
    def __init__(self, event_repo: IEventRepository):
        self.event_repo = event_repo

    def execute(self) -> List[EventEntity]:
        return self.event_repo.get_upcoming_events(limit=4)