import json
from channels.generic.websocket import AsyncWebsocketConsumer

class DirectorNotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if user.is_authenticated:
            if user.role in ['DIRECTOR', 'SUBDIRECTOR', 'SUPERUSER', 'APOYO']:
                await self.channel_layer.group_add("directors_group", self.channel_name)
            if user.role == 'DOCENTE':
                await self.channel_layer.group_add("teachers_group", self.channel_name)
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        user = self.scope["user"]
        if user.is_authenticated:
            if user.role in ['DIRECTOR', 'SUBDIRECTOR', 'SUPERUSER', 'APOYO']:
                await self.channel_layer.group_discard("directors_group", self.channel_name)
            if user.role == 'DOCENTE':
                await self.channel_layer.group_discard("teachers_group", self.channel_name)

    async def send_alert(self, event):
        # CORRECCIÓN: Mapeamos 'alert_type' a 'type' para que el JavaScript lo entienda
        await self.send(text_data=json.dumps({
            'type': event.get('alert_type', ''),
            'message': event.get('message', ''),
            'severity': event.get('severity', 'LEVE')
        }))