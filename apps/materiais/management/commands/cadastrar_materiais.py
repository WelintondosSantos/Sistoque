# Em apps/materiais/management/commands/cadastrar_materiais.py

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import datetime

class Command(BaseCommand):
    help = 'Cadastra materiais e o seu estoque inicial em lotes a partir de uma lista pré-definida.'

    # --- DADOS DE TESTE ---
    MATERIAIS_INICIAIS = [
        {
            'codigo': '131342001',
            'nome': 'ENVELOPE PLÁSTICO 04 FUROS',
            'categoria': 'Material de Escritório',
            'unidade': 'Unidade',
            'estoque_minimo': 50,
            'saldo_inicial': 9000,
            'custo_unitario': 0.15,
            'data_validade': '2028-12-31' # Formato AAAA-MM-DD
        },
        {
            'codigo': '131221001',
            'nome': 'AÇÚCAR REFINADO',
            'categoria': 'Copa e Cozinha',
            'unidade': 'Kg',
            'estoque_minimo': 10,
            'saldo_inicial': 50,
            'custo_unitario': 4.50,
            'data_validade': '2026-10-20' # Formato AAAA-MM-DD
        },
        {
            'codigo': '131332001',
            'nome': 'ALFINETE PARA MAPAS',
            'categoria': 'Material de Escritório',
            'unidade': 'Caixa',
            'estoque_minimo': 5,
            'saldo_inicial': 20,
            'custo_unitario': 3.20,
            'data_validade': '2029-01-01' # Formato AAAA-MM-DD
        },
    ]

@transaction.atomic
def handle(self, *args, **options):
        # --- IMPORTAÇÕES MOVIDAS PARA DENTRO DO HANDLE ---
        from apps.materiais.models import Produto, Categoria, Almoxarifado, MovimentoEstoque, Lote
        from apps.users.models import UsuarioSistema

        self.stdout.write(self.style.SUCCESS('--- Iniciando o cadastro de materiais e lotes iniciais ---'))

        usuario_sistema, _ = UsuarioSistema.objects.get_or_create(username='sistema')
        almoxarifado_principal, _ = Almoxarifado.objects.get_or_create(nome="Almoxarifado Central")

        for dados_material in self.MATERIAIS_INICIAIS:
            nome_categoria = dados_material['categoria']
            codigo_produto = dados_material['codigo']
            
            try:
                categoria_obj = Categoria.objects.get(nome=nome_categoria)
            except Categoria.DoesNotExist:
                self.stderr.write(self.style.ERROR(f'ERRO: Categoria "{nome_categoria}" não encontrada. A saltar produto "{dados_material["nome"]}".'))
                continue

            produto, created = Produto.objects.update_or_create(
                codigo_produto=codigo_produto,
                defaults={
                    'nome_produto': dados_material['nome'],
                    'categoria': categoria_obj,
                    'unidade_medida': dados_material['unidade'],
                    'estoque_minimo': dados_material['estoque_minimo'],
                    'ativo': True,
                    'data_cadastro': timezone.now()
                }
            )

            if created:
                self.stdout.write(f'  [PRODUTO CRIADO] {produto.nome_produto}')
                if dados_material['saldo_inicial'] > 0:
                    validade_str = dados_material['data_validade']
                    validade_obj = datetime.strptime(validade_str, '%Y-%m-%d').date()
                    lote = Lote.objects.create(
                        produto=produto,
                        data_validade=validade_obj,
                        quantidade_atual=dados_material['saldo_inicial']
                    )
                    self.stdout.write(f"    -> [LOTE CRIADO] Validade: {lote.data_validade.strftime('%d/%m/%Y')}")
                    MovimentoEstoque.objects.create(
                        lote=lote,
                        almoxarifado=almoxarifado_principal,
                        quantidade=dados_material['saldo_inicial'],
                        valor_unitario=dados_material['custo_unitario'],
                        tipo='ENTRADA',
                        usuario=usuario_sistema,
                        observacao="Carga Inicial do Sistema"
                    )
                    self.stdout.write(self.style.SUCCESS(f"    -> [ESTOQUE INICIAL] Lançado: {dados_material['saldo_inicial']} unidades."))
            else:
                self.stdout.write(self.style.WARNING(f'  [PRODUTO ATUALIZADO] {produto.nome_produto}. O estoque inicial não foi alterado.'))

        self.stdout.write(self.style.SUCCESS('--- Cadastro de materiais concluído com sucesso! ---'))   