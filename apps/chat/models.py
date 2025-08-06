# Em apps/chat/models.py

from django.db import models
from django.conf import settings

# A importação da Requisição foi removida, pois a Conversa agora é independente.
# from apps.materiais.models import Requisicao

class Conversa(models.Model):
    """
    Representa uma sala de chat entre dois ou mais participantes.
    """
    participantes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='conversas',
        verbose_name="Participantes"
    )
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        nomes_participantes = ", ".join([user.username for user in self.participantes.all()])
        return f"Conversa entre: {nomes_participantes}"

    class Meta:
        verbose_name = "Conversa"
        verbose_name_plural = "Conversas"
        ordering = ['-data_criacao']


class Mensagem(models.Model):
    """
    Representa uma única mensagem dentro de uma Conversa.
    """
    conversa = models.ForeignKey(
        Conversa,
        on_delete=models.CASCADE,
        related_name='mensagens'
    )
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mensagens_chat'
    )
    texto = models.TextField(verbose_name="Texto da Mensagem")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Enviada em")

    def __str__(self):
        return f"Mensagem de {self.autor.username} em {self.timestamp.strftime('%d/%m/%Y %H:%M')}"

    class Meta:
        verbose_name = "Mensagem"
        verbose_name_plural = "Mensagens"
        ordering = ['timestamp']
