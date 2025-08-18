# Em apps/relatorios/views.py

import datetime
from django.shortcuts import render
from django.views import View
from django.views.generic import DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import (
    Sum, F, Value, DecimalField, OuterRef, Subquery, ExpressionWrapper
)
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML

from apps.materiais.models import (
    FechamentoMensal, MovimentoEstoque, ItemRequisicao
)
from .forms import ReportFilterForm


class RelatorioBaseView(LoginRequiredMixin, UserPassesTestMixin):
    """Classe base para garantir a segurança em todos os relatórios."""
    def test_func(self):
        user = self.request.user
        return user.is_superuser or user.groups.filter(name__in=['Administradores', 'Almoxarifes']).exists()


class RelatorioConsumoView(RelatorioBaseView, View):
    template_name = 'relatorios/relatorio_consumo.html'
    form_class = ReportFilterForm

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form, 'page_title': 'Relatório de Consumo'})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        action = request.POST.get('action')
        contexto_render = {
            'form': form,
            'page_title': 'Relatório de Consumo por Centro de Custo'
        }

        if form.is_valid():
            data_inicio = form.cleaned_data['data_inicio']
            data_fim = form.cleaned_data['data_fim']
            centros_de_custo = form.cleaned_data['centros_de_custo']

            # Define o intervalo de datas com fuso horário
            dt_inicio_aware = timezone.make_aware(datetime.datetime.combine(data_inicio, datetime.time.min))
            dt_fim_aware = timezone.make_aware(datetime.datetime.combine(data_fim, datetime.time.max))

            itens_consumidos = ItemRequisicao.objects.filter(
                requisicao__status='ATENDIDA',
                requisicao__data_atendimento__range=(dt_inicio_aware, dt_fim_aware),
                requisicao__centro_custo__in=centros_de_custo
            ).select_related('produto', 'produto__categoria')

            # =====================================================================
            # CORREÇÃO 1: Adicionada ExpressionWrapper na subquery de valor
            # =====================================================================
            entradas_valor_subquery = MovimentoEstoque.objects.filter(
                lote__produto_id=OuterRef('produto_id'), tipo='ENTRADA'
            ).values('lote__produto_id').annotate(
                total=Sum(
                    ExpressionWrapper(F('quantidade') * F('valor_unitario'), output_field=DecimalField())
                )
            ).values('total')

            entradas_qtd_subquery = MovimentoEstoque.objects.filter(
                lote__produto_id=OuterRef('produto_id'), tipo='ENTRADA'
            ).values('lote__produto_id').annotate(total=Sum('quantidade')).values('total')

            resultados_relatorio = itens_consumidos.values(
                'produto__nome_produto', 'produto__unidade_medida', 'produto_id'
            ).annotate(
                quantidade_total=Sum('quantidade_atendida'),
                custo_medio_calculado=Coalesce(
                    Subquery(entradas_valor_subquery, output_field=DecimalField()) /
                    Subquery(entradas_qtd_subquery, output_field=DecimalField()),
                    Value(0), output_field=DecimalField()
                )
            ).annotate(
                # =====================================================================
                # CORREÇÃO 2: Adicionada ExpressionWrapper no cálculo do valor total
                # =====================================================================
                valor_total=ExpressionWrapper(
                    F('quantidade_total') * F('custo_medio_calculado'),
                    output_field=DecimalField()
                )
            ).order_by('produto__nome_produto')

            valor_total_geral = resultados_relatorio.aggregate(
                total_geral=Sum('valor_total')
            )['total_geral'] or 0

            contexto_render['resultados'] = resultados_relatorio
            contexto_render['valor_total_geral'] = valor_total_geral
            contexto_render['submitted_data'] = form.cleaned_data

            if action == 'exportar_pdf':
                contexto_pdf = {
                    'resultados': resultados_relatorio,
                    'valor_total_geral': valor_total_geral,
                    'data_inicio': data_inicio,
                    'data_fim': data_fim,
                    'centros_de_custo': centros_de_custo,
                }
                html_string = render_to_string('relatorios/relatorio_consumo_pdf.html', contexto_pdf)
                pdf = HTML(string=html_string).write_pdf()
                response = HttpResponse(pdf, content_type='application/pdf')
                response['Content-Disposition'] = 'inline; filename="relatorio_consumo.pdf"'
                return response

        return render(request, self.template_name, contexto_render)


class RelatorioInventarioView(RelatorioBaseView, DetailView):
    model = FechamentoMensal
    template_name = 'relatorios/relatorio_inventario.html'
    context_object_name = 'fechamento'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        fechamento = self.get_object()
        context['page_title'] = f"Relatório de Inventário - {fechamento.mes:02d}/{fechamento.ano}"
        total_inventario = fechamento.posicoes.aggregate(
            total=Coalesce(Sum('valor_total_final'), Value(0))
        )['total']
        context['total_inventario'] = total_inventario
        return context


class RelatorioMovimentacaoView(RelatorioBaseView, TemplateView):
    template_name = 'relatorios/relatorio_movimentacao.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ano = self.kwargs['ano']
        mes = self.kwargs['mes']
        context['page_title'] = f"Relatório de Movimentação - {mes:02d}/{ano}"
        context['periodo'] = f"{mes:02d}/{ano}"

        movimentos = MovimentoEstoque.objects.filter(data__year=ano, data__month=mes)
        
        entradas = movimentos.filter(tipo='ENTRADA').order_by('data')
        total_entradas = entradas.aggregate(
            total=Coalesce(Sum(ExpressionWrapper(F('quantidade') * F('valor_unitario'), output_field=DecimalField())), Value(0))
        )['total']
        
        saidas = movimentos.filter(tipo='SAIDA').order_by('data')
        total_saidas = saidas.aggregate(
            total=Coalesce(Sum(ExpressionWrapper(F('quantidade') * F('lote__custo_unitario'), output_field=DecimalField())), Value(0))
        )['total']

        context['entradas'] = entradas
        context['total_entradas'] = total_entradas
        context['saidas'] = saidas
        context['total_saidas'] = total_saidas
        return context