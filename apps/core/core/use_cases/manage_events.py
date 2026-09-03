from typing import List
from datetime import date
from apps.core.core.domain.entities import EventEntity
from apps.core.core.domain.repositories import IEventRepository

class GetCalendarEventsUseCase:
    def __init__(self, event_repo: IEventRepository):
        self.event_repo = event_repo

    def execute(self, start_date: date, end_date: date) -> List[EventEntity]:
        return self.event_repo.get_events_in_range(start_date, end_date)
