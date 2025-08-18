# Em apps/relatorios/urls.py

from django.urls import path
from .views import RelatorioConsumoView
from . import views 

app_name = 'relatorios'

urlpatterns = [
    # URL para a nossa página de relatório de consumo
    path('consumo/', RelatorioConsumoView.as_view(), name='relatorio_consumo'),
    path('fechamento/<int:pk>/inventario/', views.RelatorioInventarioView.as_view(), name='relatorio_fechamento_inventario'),
    path('fechamento/<int:ano>/<int:mes>/movimentacao/', views.RelatorioMovimentacaoView.as_view(), name='relatorio_fechamento_movimentacao'),
]