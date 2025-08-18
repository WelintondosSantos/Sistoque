# Em apps/materiais/models/catalogo.py

from django.db import models
from django.db.models import Sum, Case, When, F, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone


class Categoria(models.Model):
    # ... (código inalterado) ...
    nome = models.CharField(max_length=100, unique=True, verbose_name="Nome da Categoria")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")
    def __str__(self): return self.nome
    class Meta:
        verbose_name = "Categoria de Produto"
        verbose_name_plural = "Categorias de Produtos"
        ordering = ['nome']

class Almoxarifado(models.Model):
    # ... (código inalterado) ...
    nome = models.CharField(max_length=100, unique=True, verbose_name="Nome do Almoxarifado")
    codigo = models.CharField(max_length=20, unique=True, null=True, blank=True, verbose_name="Código")
    localizacao = models.TextField(blank=True, null=True, verbose_name="Localização/Descrição")
    ativo = models.BooleanField(default=True)
    def __str__(self): return self.nome
    class Meta:
        verbose_name = "Almoxarifado"
        verbose_name_plural = "Almoxarifados"
        ordering = ['nome']

class Classe(models.Model):
    """
    Representa a Classe de um material (ex: 7520 - Material de Papelaria).
    """
    codigo = models.CharField(max_length=20, unique=True, help_text="Código da classe do produto.")
    descricao = models.TextField(verbose_name="Descrição")

    class Meta:
        verbose_name = "Classe"
        verbose_name_plural = "Classes"
        ordering = ['codigo']

    def __str__(self):
        return f"{self.codigo} - {self.descricao}"

class PDM(models.Model):
    """
    Representa o Padrão Descritivo de Material.
    """
    codigo = models.CharField(max_length=20, unique=True, help_text="Código do PDM.")
    descricao = models.TextField(verbose_name="Descrição")

    class Meta:
        verbose_name = "PDM"
        verbose_name_plural = "PDMs"
        ordering = ['codigo']

    def __str__(self):
        return f"{self.codigo} - {self.descricao}"

class NaturezaDespesa(models.Model):
    """
    Representa a Natureza de Despesa associada a um produto.
    """
    codigo = models.CharField(max_length=20, unique=True, help_text="Código da Natureza de Despesa.")
    descricao = models.TextField(verbose_name="Descrição")

    class Meta:
        verbose_name = "Natureza de Despesa"
        verbose_name_plural = "Naturezas de Despesa"
        ordering = ['codigo']

    def __str__(self):
        return f"{self.codigo} - {self.descricao}"        


class Produto(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='produtos', verbose_name="Categoria")
    codigo_produto = models.CharField(max_length=50, unique=True, verbose_name="Código do Produto")
    nome_produto = models.CharField(max_length=255, verbose_name="Nome do Produto")
    descricao_detalhada = models.TextField(blank=True, null=True, verbose_name="Descrição Detalhada")
    unidade_medida = models.CharField(max_length=20, verbose_name="Unidade de Medida")
    estoque_minimo = models.PositiveIntegerField(default=0, verbose_name="Estoque Mínimo")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_cadastro = models.DateTimeField(default=timezone.now, verbose_name="Data de Cadastro")
    
    classe = models.ForeignKey(
        Classe,
        on_delete=models.PROTECT, # Impede a exclusão de uma classe se ela estiver em uso
        related_name='produtos',
        verbose_name="Classe",
        null=True, # Permite que o campo seja nulo no banco de dados
        blank=True # Permite que o campo seja vazio em formulários
    )
    pdm = models.ForeignKey(
        PDM,
        on_delete=models.PROTECT,
        related_name='produtos',
        verbose_name="PDM",
        null=True,
        blank=True
    )
    natureza_despesa = models.ForeignKey(
        NaturezaDespesa,
        on_delete=models.PROTECT,
        related_name='produtos',
        verbose_name="Natureza da Despesa",
        null=True,
        blank=True
    )
    
    def calcular_saldo_ate(self, data_limite):
        """
        Calcula o saldo total de um produto somando todas as ENTRADAS
        e subtraindo todas as SAÍDAS até uma data e hora específicas.
        """
        from .transacao import MovimentoEstoque

        if not timezone.is_aware(data_limite):
            data_limite = timezone.make_aware(data_limite)

        # --- CORREÇÃO APLICADA AQUI ---
        # O nome do campo foi corrigido de 'data_movimento' para 'data'.
        movimentos = MovimentoEstoque.objects.filter(
            lote__produto=self, 
            data__lte=data_limite  # <-- CAMPO CORRIGIDO
        )

        resultado = movimentos.aggregate(
            saldo=Sum(
                Case(
                    When(tipo='ENTRADA', then=F('quantidade')),
                    When(tipo='SAIDA', then=-F('quantidade')),
                    default=0,
                    output_field=DecimalField()
                )
            )
        )

        return resultado['saldo'] or 0

    def calcular_custo_medio_ate(self, data_limite):
        """
        Calcula o custo médio de um produto até uma data específica.
        Para este exemplo, retornaremos o custo médio atual do produto,
        mas esta lógica pode ser expandida para um cálculo histórico mais preciso.
        """
        # Lógica simplificada: retorna o custo médio atual.
        # Uma implementação mais complexa calcularia o custo médio ponderado
        # com base em todos os movimentos de ENTRADA até a data_limite.
        return self.custo_medio

    @property
    def saldo_total(self):
        """
        Calcula o saldo total do produto somando a quantidade de todos os seus lotes.
        """
        saldo = self.lotes.aggregate(total=Sum('quantidade_atual'))['total']
        return saldo if saldo is not None else 0

    # --- PROPRIEDADES DE CUSTO ADICIONADAS ---
    @property
    def custo_medio(self):
        """
        Calcula o Custo Médio Ponderado do produto.
        """
        # Importação local para evitar dependência circular
        from .transacao import MovimentoEstoque
        
        entradas = MovimentoEstoque.objects.filter(lote__produto=self, tipo='ENTRADA')
        
        agregado = entradas.aggregate(
            valor_total=Coalesce(Sum(F('quantidade') * F('valor_unitario')), 0, output_field=models.DecimalField()),
            quantidade_total=Coalesce(Sum('quantidade'), 0, output_field=models.DecimalField())
        )
        
        valor_total_entradas = agregado['valor_total']
        quantidade_total_entradas = agregado['quantidade_total']

        if quantidade_total_entradas == 0:
            return 0.00
        
        return valor_total_entradas / quantidade_total_entradas

    @property
    def valor_total_em_estoque(self):
        """
        Calcula o valor financeiro total do produto em estoque.
        """
        return self.saldo_total * self.custo_medio
    # --- FIM DAS PROPRIEDADES DE CUSTO ---

    def __str__(self):
        return f"{self.codigo_produto} - {self.nome_produto}"
    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"
        ordering = ['nome_produto']

class Lote(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='lotes')
    codigo_lote = models.CharField(max_length=100, blank=True, null=True, verbose_name="Código do Lote/Referência")
    data_validade = models.DateField(verbose_name="Data de Validade")
    quantidade_atual = models.PositiveIntegerField(default=0, verbose_name="Quantidade Atual no Lote")
    data_entrada = models.DateTimeField(default=timezone.now, verbose_name="Data de Entrada do Lote")

    def __str__(self):
        validade_formatada = self.data_validade.strftime('%d/%m/%Y')
        return f"Lote de {self.produto.nome_produto} (Val: {validade_formatada})"

    class Meta:
        unique_together = ('produto', 'data_validade')
        verbose_name = "Lote de Produto"
        verbose_name_plural = "Lotes de Produtos"
        ordering = ['data_validade']