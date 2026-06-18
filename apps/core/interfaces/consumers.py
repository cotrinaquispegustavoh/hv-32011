import json
from channels.generic.websocket import AsyncWebsocketConsumer

class DirectorNotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if user.is_authenticated and user.role in ['DIRECTOR', 'SUBDIRECTOR', 'SUPERUSER']:
            await self.channel_layer.group_add("directors_group", self.channel_name)
            await self.accept()
            print(f"✅ WebSocket Conectado: {user.first_name} ({user.role})") # <-- NUEVO
        else:
            await self.close()
            print("❌ WebSocket Rechazado: Usuario no autorizado") # <-- NUEVO

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("directors_group", self.channel_name)
        print("⚠️ WebSocket Desconectado") # <-- NUEVO

    async def send_alert(self, event):
        print(f"🚀 Enviando alerta al navegador: {event['message']}") # <-- NUEVO
        await self.send(text_data=json.dumps({
            'type': event['alert_type'],
            'message': event['message'],
            'severity': event.get('severity', 'LEVE')
        }))