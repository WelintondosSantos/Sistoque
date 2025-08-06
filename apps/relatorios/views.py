# Em apps/relatorios/views.py

from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Sum, F, Value, DecimalField, OuterRef, Subquery
from django.db.models.functions import Coalesce
import datetime
from django.utils import timezone

from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML

from .forms import ReportFilterForm
from apps.materiais.models import ItemRequisicao, MovimentoEstoque

class RelatorioConsumoView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'relatorios/relatorio_consumo.html'
    form_class = ReportFilterForm

    def test_func(self):
        user = self.request.user
        return user.is_superuser or user.groups.filter(name__in=['Administradores', 'Almoxarifes']).exists()

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form, 'page_title': 'Relatório de Consumo por Centro de Custo'})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        
        # --- LÓGICA DE AÇÃO ADICIONADA ---
        # Capturamos qual botão foi clicado
        action = request.POST.get('action')
        
        resultados_relatorio = None
        valor_total_geral = 0
        contexto_render = {
            'form': form,
            'page_title': 'Relatório de Consumo por Centro de Custo'
        }

        if form.is_valid():
            data_inicio_form = form.cleaned_data['data_inicio']
            data_fim_form = form.cleaned_data['data_fim']
            centros_de_custo = form.cleaned_data['centros_de_custo']

            start_of_day = datetime.time(0, 0, 0)
            dt_inicio_naive = datetime.datetime.combine(data_inicio_form, start_of_day)
            dt_fim_exclusive_naive = datetime.datetime.combine(data_fim_form + datetime.timedelta(days=1), start_of_day)
            data_inicio_aware = timezone.make_aware(dt_inicio_naive)
            data_fim_aware = timezone.make_aware(dt_fim_exclusive_naive)

            itens_consumidos = ItemRequisicao.objects.filter(
                requisicao__status='ATENDIDA',
                requisicao__data_atendimento__gte=data_inicio_aware,
                requisicao__data_atendimento__lt=data_fim_aware,
                requisicao__centro_custo__in=centros_de_custo
            ).select_related('produto', 'produto__categoria')

            entradas_valor_subquery = MovimentoEstoque.objects.filter(
                lote__produto_id=OuterRef('produto_id'), tipo='ENTRADA'
            ).values('lote__produto_id').annotate(total=Sum(F('quantidade') * F('valor_unitario'))).values('total')

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
                valor_total=F('quantidade_total') * F('custo_medio_calculado')
            ).order_by('produto__nome_produto')

            if resultados_relatorio:
                valor_total_geral = resultados_relatorio.aggregate(total_geral=Sum('valor_total'))['total_geral']

            # Adiciona os resultados ao contexto para serem exibidos no HTML
            contexto_render['resultados'] = resultados_relatorio
            contexto_render['valor_total_geral'] = valor_total_geral
            # Adiciona os dados validados para serem usados no formulário de PDF
            contexto_render['submitted_data'] = form.cleaned_data

            # --- LÓGICA DE EXPORTAÇÃO CORRIGIDA ---
            if action == 'exportar_pdf':
                contexto_pdf = {
                    'resultados': resultados_relatorio,
                    'valor_total_geral': valor_total_geral,
                    'data_inicio': data_inicio_form,
                    'data_fim': data_fim_form,
                    'centros_de_custo': centros_de_custo,
                }
                html_string = render_to_string('relatorios/relatorio_consumo_pdf.html', contexto_pdf)
                pdf = HTML(string=html_string).write_pdf()
                response = HttpResponse(pdf, content_type='application/pdf')
                response['Content-Disposition'] = 'inline; filename="relatorio_consumo.pdf"'
                return response

        return render(request, self.template_name, contexto_render)