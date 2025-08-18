# app/materiais/management/commands/reabrir_estoque.py

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from apps.materiais.models import FechamentoMensal
from apps.users.models import UsuarioSistema

class Command(BaseCommand):
    help = 'Reabre (cancela) o último período de estoque ativo.'

    def add_arguments(self, parser):
        parser.add_argument('--usuario_id', required=True, type=int, help='O ID do usuário que está realizando a reabertura.')

    def handle(self, *args, **options):
        usuario_id = options['usuario_id']
        try:
            responsavel_reabertura = UsuarioSistema.objects.get(pk=usuario_id)
        except UsuarioSistema.DoesNotExist:
            raise CommandError(f'Usuário com ID {usuario_id} não encontrado.')

        ultimo_fechamento = FechamentoMensal.objects.filter(status='ATIVO').order_by('-ano', '-mes').first()

        if not ultimo_fechamento:
            raise CommandError('Nenhum período ativo encontrado para reabrir.')

        mes, ano = ultimo_fechamento.mes, ultimo_fechamento.ano

        ultimo_fechamento.status = 'CANCELADO'
        ultimo_fechamento.cancelado_por = responsavel_reabertura
        ultimo_fechamento.data_cancelamento = timezone.now()
        ultimo_fechamento.save()

        self.stdout.write(self.style.SUCCESS(f'O período {mes:02d}/{ano} foi reaberto com sucesso.'))