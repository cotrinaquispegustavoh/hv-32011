import json
from channels.generic.websocket import AsyncWebsocketConsumer
from apps.core.realtime import user_notification_group

class DirectorNotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if user.is_authenticated:
            await self.channel_layer.group_add(
                user_notification_group(user.pk),
                self.channel_name,
            )
            if user.role in ['DIRECTOR', 'SUBDIRECTOR', 'SUPERUSER', 'APOYO']:
                await self.channel_layer.group_add("directors_group", self.channel_name)
            if user.is_superuser or user.role in ['DIRECTOR', 'SUPERUSER']:
                await self.channel_layer.group_add(
                    "announcement_read_receipts",
                    self.channel_name,
                )
            if user.role == 'DOCENTE':
                await self.channel_layer.group_add("teachers_group", self.channel_name)
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        user = self.scope["user"]
        if user.is_authenticated:
            await self.channel_layer.group_discard(
                user_notification_group(user.pk),
                self.channel_name,
            )
            if user.role in ['DIRECTOR', 'SUBDIRECTOR', 'SUPERUSER', 'APOYO']:
                await self.channel_layer.group_discard("directors_group", self.channel_name)
            if user.is_superuser or user.role in ['DIRECTOR', 'SUPERUSER']:
                await self.channel_layer.group_discard(
                    "announcement_read_receipts",
                    self.channel_name,
                )
            if user.role == 'DOCENTE':
                await self.channel_layer.group_discard("teachers_group", self.channel_name)

    async def send_alert(self, event):
        allowed_fields = (
            'notification_id', 'title', 'message', 'severity', 'link',
            'announcement_id', 'user_id', 'user_name', 'user_dni',
            'acknowledged_at', 'recipient_count', 'confirmed_count',
            'pending_count',
        )
        payload = {'type': event.get('alert_type', '')}
        payload.update({key: event.get(key) for key in allowed_fields if key in event})
        await self.send(text_data=json.dumps(payload))
