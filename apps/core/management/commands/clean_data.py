# apps/core/management/commands/clean_data.py

from django.core.management.base import BaseCommand
from django.db import transaction

# 1. Importe todos os modelos que serão limpos
from apps.chat.models import Mensagem, Conversa
from apps.materiais.models import (
    Categoria,
    FechamentoMensal,
    ItemRequisicao,
    Lote,
    MovimentoEstoque,
    PosicaoEstoqueMensal,
    Produto,
    Requisicao
)

class Command(BaseCommand):
    help = 'Limpa todas as tabelas de movimentação e catálogo para um novo ciclo de testes.'

    def _delete_model_data(self, model):
        """Função auxiliar para apagar dados de um modelo usando o método seguro .delete()."""
        self.stdout.write(f'Limpando {model._meta.verbose_name_plural.capitalize()}...')
        
        # CORREÇÃO FINAL: Usando o método .delete() padrão, que lida com todas as relações.
        # Ele retorna uma tupla (total_deletado, dicionario_de_tipos), por isso o desempacotamento.
        count, _ = model.objects.all().delete()
        
        self.stdout.write(self.style.SUCCESS(f'>> {count} registros apagados.'))

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING(
            'ATENÇÃO: Este comando irá apagar dados de produção. Iniciando limpeza...'
        ))

        # 2. Ordem de exclusão (dos 'filhos' para os 'pais')
        # Embora .delete() seja mais inteligente, manter a ordem é uma boa prática.
        models_to_clean = [
            # Chat
            Mensagem,
            Conversa, # .delete() agora vai cuidar da tabela de participantes automaticamente

            # Movimentações e Transações
            MovimentoEstoque,
            ItemRequisicao,
            Requisicao,
            PosicaoEstoqueMensal,
            FechamentoMensal,
            Lote,

            # Catálogo
            Produto,
            Categoria,
        ]

        # 3. Itere sobre a lista e execute a limpeza
        for model in models_to_clean:
            self._delete_model_data(model)

        self.stdout.write(self.style.SUCCESS(
            '\nLimpeza concluída com sucesso! O sistema está pronto para os testes.'
        ))