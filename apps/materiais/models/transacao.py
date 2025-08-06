# Em apps/materiais/models/transacao.py

from django.db import models
from django.conf import settings

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