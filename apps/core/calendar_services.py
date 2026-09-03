from dataclasses import dataclass
from datetime import date
from typing import Optional

from django.urls import reverse
from django.utils import timezone

from apps.core.infrastructure.models import InstitutionalAnnouncement, InstitutionalEvent


@dataclass(frozen=True)
class CalendarItem:
    title: str
    event_date: date
    description: str
    kind: str
    detail_url: Optional[str] = None

    @property
    def is_holiday(self):
        return self.kind == 'holiday'

    @property
    def is_announcement(self):
        return self.kind == 'announcement'


def announcements_visible_to(user):
    announcements = InstitutionalAnnouncement.objects.filter(is_active=True)
    if user.role in ['DIRECTOR', 'SUPERUSER'] or user.is_superuser:
        return announcements
    if user.role == 'DOCENTE':
        return announcements.filter(audience__in=['ALL', 'TEACHERS'])
    if user.role == 'APODERADO':
        return announcements.filter(audience__in=['ALL', 'PARENTS'])
    return announcements.none()


def dated_announcements_for_range(user, start_date, end_date):
    return (
        announcements_visible_to(user)
        .filter(event_date__gte=start_date, event_date__lt=end_date)
        .select_related('created_by')
    )


def get_upcoming_calendar_items(user, limit=4):
    today = timezone.localdate()
    items = [
        CalendarItem(
            title=event.title,
            event_date=event.event_date,
            description=event.description,
            kind='holiday' if event.is_holiday else 'event',
            detail_url=reverse('core:calendar'),
        )
        for event in InstitutionalEvent.objects.filter(event_date__gte=today)[:limit]
    ]
    items.extend(
        CalendarItem(
            title=announcement.title,
            event_date=announcement.event_date,
            description=announcement.message,
            kind='announcement',
            detail_url=reverse(
                'core:announcement_detail',
                args=[announcement.pk],
            ),
        )
        for announcement in announcements_visible_to(user).filter(
            event_date__gte=today,
        ).order_by('event_date', 'title')[:limit]
    )
    return sorted(items, key=lambda item: (item.event_date, item.title.lower()))[:limit]
