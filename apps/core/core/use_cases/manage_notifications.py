from apps.core.core.domain.entities import NotificationEntity
from apps.core.core.domain.repositories import INotificationRepository
from apps.users.infrastructure.models import User

class NotifyAdminsUseCase:
    def __init__(self, notif_repo: INotificationRepository):
        self.notif_repo = notif_repo

    def execute(self, title: str, message: str, link: str = None):
        admins = User.objects.filter(role__in=['DIRECTOR', 'SUBDIRECTOR', 'SUPERUSER'], is_active=True)
        for admin in admins:
            notif = NotificationEntity(id=None, user_id=admin.id, title=title, message=message, is_read=False, link=link)
            self.notif_repo.save(notif)

class NotifyUserUseCase:
    def __init__(self, notif_repo: INotificationRepository):
        self.notif_repo = notif_repo

    def execute(self, user_id: int, title: str, message: str, link: str = None):
        notif = NotificationEntity(id=None, user_id=user_id, title=title, message=message, is_read=False, link=link)
        self.notif_repo.save(notif)

class MarkNotificationsReadUseCase:
    def __init__(self, notif_repo: INotificationRepository):
        self.notif_repo = notif_repo

    def execute(self, user_id: int) -> bool:
        return self.notif_repo.mark_all_as_read(user_id)