# Em apps/materiais/urls.py

from django.urls import path
from .views import RequisicaoPDFView
from . import views

app_name = 'materiais'

urlpatterns = [
    # --- Rotas de Produto ---
    path('produtos/', views.ProdutoListView.as_view(), name='lista_produtos'),

    # --- Rotas de Entrada ---
    path('entradas/registrar/', views.EntradaCreateView.as_view(), name='registrar_entrada'),

    # --- Rotas de Requisição (Ciclo do Requisitante) ---
    path('requisitar/', views.RequisicaoCreateView.as_view(), name='fazer_requisicao'),
    path('requisicao/<int:pk>/', views.RequisicaoDetailView.as_view(), name='detalhe_requisicao'),
    path('requisicao/finalizar/<int:pk>/', views.RequisicaoFinalizarView.as_view(), name='finalizar_requisicao'),
    path('requisicao/cancelar/<int:pk>/', views.RequisicaoDeleteView.as_view(), name='cancelar_requisicao'),
    path('item/excluir/<int:pk>/', views.ItemRequisicaoDeleteView.as_view(), name='excluir_item_requisicao'),
    
    # --- Rotas do Almoxarifado (Ciclo de Atendimento) ---
    path('requisicoes/pendentes/', views.RequisicaoPendenteListView.as_view(), name='lista_requisicoes_pendentes'),
    path('requisicao/estornar/<int:pk>/', views.RequisicaoEstornarView.as_view(), name='estornar_requisicao'),
    
    # Mantemos apenas a URL 'atendimento_requisicao', que aponta para a view correta com o FormSet.
    path('requisicao/atendimento/<int:pk>/', views.RequisicaoAtendimentoView.as_view(), name='atendimento_requisicao'),
    # Url dos Pdfs.
    path('requisicao/<int:pk>/pdf/', RequisicaoPDFView.as_view(), name='requisicao_pdf'),

        # --- Rota para o Painel de Fechamento Mensal ---
    path('fechamento/painel/', views.FechamentoListView.as_view(), name='painel_fechamento'),
    path('fechamentos/fazer/', views.FazerFechamentoView.as_view(), name='fazer_fechamento'),
    path('fechamentos/reabrir/', views.ReabrirUltimoFechamentoView.as_view(), name='reabrir_ultimo_fechamento'),
]


