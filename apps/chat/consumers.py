# Em apps/chat/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils.timezone import localtime # ✅ IMPORTAÇÃO PARA CORRIGIR O FUSO HORÁRIO

from .models import Mensagem, Conversa

class ChatConsumer(AsyncWebsocketConsumer):
    """
    Consumer que gerencia as conexões WebSocket para o chat em tempo real.
    """
    async def connect(self):
        """
        Chamado quando a conexão WebSocket é iniciada.
        Valida o usuário, junta-o ao grupo da conversa e envia o histórico.
        """
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
            return

        self.conversa_id = self.scope['url_route']['kwargs']['conversa_id']
        self.room_group_name = f'chat_{self.conversa_id}'

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        await self.send_message_history()

    async def disconnect(self, close_code):
        """
        Chamado quando a conexão WebSocket é fechada.
        """
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        """
        Recebe uma nova mensagem do cliente, salva e a transmite para o grupo.
        """
        text_data_json = json.loads(text_data)
        message_text = text_data_json.get('message', '')

        if not message_text.strip():
            return # Ignora mensagens vazias

        new_message_data = await self.save_message(message_text)
        if new_message_data:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message_data': new_message_data
                }
            )

    async def chat_message(self, event):
        """
        Recebe uma mensagem transmitida do grupo e a envia ao cliente WebSocket.
        Calcula o campo 'is_me' para cada destinatário.
        """
        message_data = event['message_data']
        is_me = (self.user.username == message_data.get('author_username'))
        
        payload = message_data.copy()
        payload['is_me'] = is_me
        
        await self.send(text_data=json.dumps(payload))
    
    @database_sync_to_async
    def get_message_history(self):
        """
        Busca o histórico de mensagens no banco de dados, convertendo o
        timestamp para o fuso horário local.
        """
        try:
            conversa = Conversa.objects.get(id=self.conversa_id)
            if self.user not in conversa.participantes.all():
                return None

            mensagens = conversa.mensagens.order_by('timestamp').select_related('autor__funcionario', 'autor')
            
            history = []
            for msg in mensagens:
                autor_nome = msg.autor.funcionario.nome if hasattr(msg.autor, 'funcionario') and msg.autor.funcionario else msg.autor.username
                
                # ✅ CONVERSÃO DO FUSO HORÁRIO APLICADA
                timestamp_local = localtime(msg.timestamp).strftime('%d/%m/%Y %H:%M')
                
                history.append({
                    'user': autor_nome,
                    'message': msg.texto,
                    'timestamp': timestamp_local,
                    'is_me': msg.autor == self.user
                })
            return history
        except Conversa.DoesNotExist:
            return None

    async def send_message_history(self):
        """
        Envia o histórico de mensagens formatado para o cliente que acabou de se conectar.
        """
        history = await self.get_message_history()
        if history is not None:
            await self.send(text_data=json.dumps({
                'type': 'message_history',
                'history': history
            }))

    @database_sync_to_async
    def save_message(self, message_text):
        """
        Salva uma nova mensagem no banco de dados e retorna um dicionário
        com os dados formatados, incluindo o timestamp no fuso horário local.
        """
        try:
            conversa = Conversa.objects.get(id=self.conversa_id)
            message = Mensagem.objects.create(
                conversa=conversa,
                autor=self.user,
                texto=message_text
            )
            autor_nome = self.user.funcionario.nome if hasattr(self.user, 'funcionario') and self.user.funcionario else self.user.username
            
            # ✅ CONVERSÃO DO FUSO HORÁRIO APLICADA
            timestamp_local = localtime(message.timestamp).strftime('%d/%m/%Y %H:%M')

            return {
                'user': autor_nome,
                'message': message.texto,
                'timestamp': timestamp_local,
                'author_username': self.user.username
            }
        except Conversa.DoesNotExist:
            return None
