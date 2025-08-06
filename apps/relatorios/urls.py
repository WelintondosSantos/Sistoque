# Em apps/relatorios/urls.py

from django.urls import path
from .views import RelatorioConsumoView

app_name = 'relatorios'

urlpatterns = [
    # URL para a nossa página de relatório de consumo
    path('consumo/', RelatorioConsumoView.as_view(), name='relatorio_consumo'),
]