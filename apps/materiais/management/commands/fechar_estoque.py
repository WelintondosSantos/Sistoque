# app/materiais/management/commands/fechar_estoque.py

import calendar
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from apps.materiais.models import Produto, FechamentoMensal, PosicaoEstoqueMensal
from apps.users.models import UsuarioSistema

class Command(BaseCommand):
    help = 'Executa o fechamento mensal do estoque para um determinado mês e ano.'

    def add_arguments(self, parser):
        parser.add_argument('--mes', required=True, type=int, help='O mês (1-12) para o fechamento.')
        parser.add_argument('--ano', required=True, type=int, help='O ano (ex: 2025) para o fechamento.')
        parser.add_argument('--usuario_id', required=True, type=int, help='O ID do usuário responsável pelo fechamento.')

    @transaction.atomic
    def handle(self, *args, **options):
        mes = options['mes']
        ano = options['ano']
        usuario_id = options['usuario_id']

        try:
            responsavel = UsuarioSistema.objects.get(pk=usuario_id)
        except UsuarioSistema.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Usuário com ID {usuario_id} não encontrado.'))
            return

        if FechamentoMensal.objects.filter(mes=mes, ano=ano).exists():
            self.stdout.write(self.style.ERROR(f'O período {mes:02d}/{ano} já foi fechado.'))
            return

        self.stdout.write(f'Iniciando o fechamento de {mes:02d}/{ano} por {responsavel.username}...')

        # Cria o registro principal do fechamento
        fechamento = FechamentoMensal.objects.create(mes=mes, ano=ano, responsavel=responsavel)

        # Define o momento exato do "fim do mês"
        _, ultimo_dia = calendar.monthrange(ano, mes)
        fim_do_periodo = timezone.datetime(ano, mes, ultimo_dia, 23, 59, 59, tzinfo=timezone.get_current_timezone())

        produtos = Produto.objects.filter(ativo=True)
        for produto in produtos:
            saldo_final = produto.calcular_saldo_ate(fim_do_periodo)
            custo_medio_final = produto.calcular_custo_medio_ate(fim_do_periodo)

            PosicaoEstoqueMensal.objects.create(
                fechamento=fechamento,
                produto=produto,
                quantidade_final=saldo_final,
                custo_medio_final=custo_medio_final,
                valor_total_final=saldo_final * custo_medio_final
            )

        self.stdout.write(self.style.SUCCESS(f'Fechamento de {mes:02d}/{ano} concluído com sucesso para {produtos.count()} produtos.'))