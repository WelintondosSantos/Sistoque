# Em apps/materiais/models/requisicao.py

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum

# Importações relativas para aceder a modelos em outros ficheiros do mesmo pacote
from .catalogo import Produto
from apps.core.models import CentroCusto

class Requisicao(models.Model):
    # ... (seus campos existentes, como solicitante, status, etc.) ...
    STATUS_CHOICES = (
        ('ABERTO', 'Em Aberto'),
        ('FINALIZADA', 'Finalizada'),
        ('ATENDIDA', 'Atendida'),
        ('CANCELADA', 'Cancelada'),
    )
    solicitante = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='requisicoes')
    centro_custo = models.ForeignKey(CentroCusto, on_delete=models.PROTECT, null=True, blank=True, related_name='requisicoes', verbose_name="Centro de Custo")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ABERTO')
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_finalizacao = models.DateTimeField(null=True, blank=True)
    atendido_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='requisicoes_atendidas', null=True, blank=True, verbose_name="Atendido por")
    data_atendimento = models.DateTimeField(null=True, blank=True, verbose_name="Data do Atendimento")
    estornado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='requisicoes_estornadas', null=True, blank=True, verbose_name="Estornado por")
    data_estorno = models.DateTimeField(null=True, blank=True, verbose_name="Data do Estorno")
    motivo_estorno = models.TextField(null=True, blank=True, verbose_name="Motivo do Estorno")

    @property
    def valor_total_solicitado(self):
        """ Soma o valor solicitado de todos os itens da requisição. """
        return sum(item.valor_solicitado for item in self.itens.all())

    @property
    def valor_total_atendido(self):
        """ Soma o valor efetivamente atendido de todos os itens da requisição. """
        return sum(item.valor_atendido for item in self.itens.all())

    def __str__(self):
        return f"Requisição #{self.id} por {self.solicitante.username} ({self.get_status_display()})"

    class Meta:
        verbose_name = "Requisição"
        verbose_name_plural = "Requisições"
        ordering = ['-data_criacao']

class ItemRequisicao(models.Model):
    requisicao = models.ForeignKey(Requisicao, on_delete=models.CASCADE, related_name='itens')
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT)
    quantidade = models.PositiveIntegerField(verbose_name="Quantidade Solicitada")
    quantidade_atendida = models.PositiveIntegerField(null=True, blank=True, verbose_name="Quantidade Atendida")
    
    @property
    def valor_solicitado(self):
        """ Calcula o valor da quantidade solicitada com base no custo médio do produto. """
        return self.quantidade * self.produto.custo_medio

    @property
    def valor_atendido(self):
        """ Calcula o valor da quantidade atendida com base no custo médio do produto. """
        if self.quantidade_atendida is not None:
            return self.quantidade_atendida * self.produto.custo_medio
        return 0 # Retorna 0 se a quantidade atendida ainda não foi definida

    def __str__(self):
        return f"{self.quantidade} x {self.produto.nome_produto} na Requisição #{self.requisicao.id}"

    class Meta:
        verbose_name = "Item de Requisição"
        verbose_name_plural = "Itens de Requisição"
        unique_together = ('requisicao', 'produto')