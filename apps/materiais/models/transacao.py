# Em apps/materiais/models/transacao.py

from django.db import models
from django.conf import settings
from .catalogo import Produto
from django.urls import reverse
# Importações relativas
from .catalogo import Almoxarifado, Lote

class MovimentoEstoque(models.Model):
    TIPO_MOVIMENTO = (
        ('ENTRADA', 'Entrada'),
        ('SAIDA', 'Saída'),
        ('AJUSTE', 'Ajuste'),
    )

    # --- MUDANÇA PRINCIPAL ---
    # Adicionado null=True, blank=True para permitir que a migração funcione em dados existentes.
    lote = models.ForeignKey(
        Lote, 
        on_delete=models.PROTECT, 
        related_name='movimentos',
        null=True, # Permite que movimentos antigos não tenham um lote
        blank=True
    )
    
    almoxarifado = models.ForeignKey(Almoxarifado, on_delete=models.PROTECT, related_name="movimentos")
    quantidade = models.IntegerField(help_text="Para SAÍDAS, insira um valor positivo. O sistema o tornará negativo.")
    valor_unitario = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tipo = models.CharField(max_length=7, choices=TIPO_MOVIMENTO)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Usuário Responsável")
    data = models.DateTimeField(auto_now_add=True, verbose_name="Data do Movimento")
    observacao = models.TextField(blank=True, null=True, help_text="Ex: NF 1234, Requisição, Carga Inicial etc.")
    
    def save(self, *args, **kwargs):
        if self.tipo == 'SAIDA' and self.quantidade > 0:
            self.quantidade = -self.quantidade
        super().save(*args, **kwargs)

    def __str__(self):
        if self.lote:
            return f"{self.get_tipo_display()} de {self.lote.produto.nome_produto}"
        return f"Movimento #{self.id} (sem lote)"

    class Meta:
        verbose_name = "Movimento de Estoque"
        verbose_name_plural = "Movimentos de Estoque"
        ordering = ['-data']

# =====================================================================
# NOVOS MODELOS PARA O FECHAMENTO MENSAL
# =====================================================================

class FechamentoMensal(models.Model):
    STATUS_CHOICES = [
        ('ATIVO', 'Ativo'),
        ('CANCELADO', 'Cancelado'),
    ]

    mes = models.PositiveSmallIntegerField("Mês")
    ano = models.PositiveSmallIntegerField("Ano")
    data_fechamento = models.DateTimeField("Realizado em", auto_now_add=True)
    responsavel = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="Responsável", on_delete=models.PROTECT)

    # --- NOVOS CAMPOS ---
    status = models.CharField("Status", max_length=10, choices=STATUS_CHOICES, default='ATIVO')
    cancelado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Cancelado por",
        on_delete=models.PROTECT,
        related_name='fechamentos_cancelados',
        null=True, blank=True
    )
    data_cancelamento = models.DateTimeField("Data do Cancelamento", null=True, blank=True)

    class Meta:
        verbose_name = "Fechamento Mensal"
        verbose_name_plural = "Fechamentos Mensais"
        unique_together = ('mes', 'ano', 'status') # Ajuste para permitir um novo fechamento se o anterior for cancelado
        ordering = ['-ano', '-mes']

    def __str__(self):
        return f"Fechamento de {self.mes:02d}/{self.ano} ({self.get_status_display()})"
    
    def get_absolute_url_movimentacao(self):
        return reverse('relatorios:relatorio_fechamento_movimentacao', kwargs={'ano': self.ano, 'mes': self.mes})


class PosicaoEstoqueMensal(models.Model):
    """
    Armazena a 'fotografia' (snapshot) do estoque de um único produto
    no momento de um fechamento mensal.
    """
    fechamento = models.ForeignKey(
        FechamentoMensal,
        on_delete=models.CASCADE,
        related_name="posicoes",
        help_text="O fechamento ao qual esta fotografia de estoque pertence."
    )
    produto = models.ForeignKey(
        Produto, 
        on_delete=models.PROTECT,
        help_text="O produto que está sendo registrado."
    )
    quantidade_final = models.DecimalField(
        "Quantidade Final", 
        max_digits=10, 
        decimal_places=2,
        help_text="Saldo do produto no momento exato do fechamento."
    )
    custo_medio_final = models.DecimalField(
        "Custo Médio Final", 
        max_digits=10, 
        decimal_places=2,
        help_text="Custo médio do produto no momento do fechamento."
    )
    valor_total_final = models.DecimalField(
        "Valor Total Final (R$)", 
        max_digits=12, 
        decimal_places=2,
        help_text="Valor total em estoque (Quantidade * Custo Médio)."
    )

    class Meta:
        verbose_name = "Posição de Estoque Mensal"
        verbose_name_plural = "Posições de Estoque Mensais"
        # Garante que não haja registros duplicados para o mesmo produto no mesmo fechamento
        unique_together = ('fechamento', 'produto')

    def __str__(self):
        return f"{self.produto.nome_produto} em {self.fechamento}"        