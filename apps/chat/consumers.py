# Em apps/chat/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone

from .models import Mensagem, Conversa
from apps.users.models import UsuarioSistema

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversa_id = self.scope['url_route']['kwargs']['conversa_id']
        self.room_group_name = f'chat_{self.conversa_id}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_text = text_data_json['message']
        user = self.scope['user']

        if not user.is_authenticated:
            return

        message_data = await self.save_message(user, message_text)
        if not message_data:
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_data['texto'],
                'user': message_data['autor_nome'],
                'timestamp': message_data['timestamp']
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'user': event['user'],
            'timestamp': event['timestamp']
        }))

    @database_sync_to_async
    def save_message(self, user, message_text):
        try:
            conversa = Conversa.objects.get(id=self.conversa_id)
            message = Mensagem.objects.create(
                conversa=conversa,
                autor=user,
                texto=message_text
            )
            return {
                'texto': message.texto,
                'autor_nome': user.funcionario.nome if user.funcionario else user.username,
                'timestamp': message.timestamp.strftime('%d/%m/%Y %H:%M')
            }
        except Conversa.DoesNotExist:
            return None
