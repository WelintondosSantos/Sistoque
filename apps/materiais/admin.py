# Em apps/materiais/admin.py

from django.contrib import admin
from .models import (
    Produto, Categoria, Almoxarifado, Lote, MovimentoEstoque, 
    Requisicao, ItemRequisicao
)

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao')
    search_fields = ('nome',)

@admin.register(Almoxarifado)
class AlmoxarifadoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'codigo', 'ativo')
    search_fields = ('nome', 'codigo')

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('codigo_produto', 'nome_produto', 'categoria', 'saldo_total', 'estoque_minimo', 'ativo')
    list_filter = ('ativo', 'categoria')
    search_fields = ('codigo_produto', 'nome_produto', 'categoria__nome')
    readonly_fields = ('saldo_total',)

# --- NOVO ADMIN PARA O MODELO LOTE ---
@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'produto', 'data_validade', 'quantidade_atual', 'codigo_lote')
    list_filter = ('produto', 'data_validade')
    search_fields = ('produto__nome_produto', 'codigo_lote')
    readonly_fields = ('quantidade_atual',) # A quantidade é atualizada por movimentos

# --- CLASSE MOVIMENTOESTOQUEADMIN CORRIGIDA ---
@admin.register(MovimentoEstoque)
class MovimentoEstoqueAdmin(admin.ModelAdmin):
    list_display = ('data', 'get_produto', 'lote', 'tipo', 'quantidade', 'valor_unitario', 'usuario')
    list_filter = ('tipo', 'almoxarifado', 'data')
    search_fields = ('lote__produto__nome_produto', 'observacao', 'usuario__username')
    
    #list_editable = ('quantidade', 'valor_unitario') # Desativado temporariamente durante a refatoração

    def has_add_permission(self, request):
        # Movimentos devem ser criados pelos fluxos do sistema, não manualmente
        return False

    @admin.display(description='Produto', ordering='lote__produto__nome_produto')
    def get_produto(self, obj):
        return obj.lote.produto.nome_produto

# Admins para o fluxo de requisição (para visualização e depuração)
@admin.register(Requisicao)
class RequisicaoAdmin(admin.ModelAdmin):
    list_display = ('id', 'solicitante', 'status', 'centro_custo', 'data_criacao', 'data_finalizacao')
    list_filter = ('status', 'centro_custo')
    search_fields = ('solicitante__username', 'centro_custo__nome')

@admin.register(ItemRequisicao)
class ItemRequisicaoAdmin(admin.ModelAdmin):
    list_display = ('requisicao', 'produto', 'quantidade', 'quantidade_atendida')
    search_fields = ('requisicao__id', 'produto__nome_produto')