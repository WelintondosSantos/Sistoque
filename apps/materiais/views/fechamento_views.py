# apps/materiais/views/fechamento_views.py

from django.shortcuts import redirect
from django.views.generic import ListView
from django.views import View
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from ..models.transacao import FechamentoMensal, PosicaoEstoqueMensal
from ..models.catalogo import Produto

# ... Sua view que lista os fechamentos (FechamentoListView) precisa ser ajustada ...
# Em apps/materiais/views/fechamento.py

class FechamentoListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = FechamentoMensal
    template_name = 'materiais/painel_fechamento.html' 
    context_object_name = 'fechamentos'
    

    def test_func(self):
        # Apenas Admins podem ver a página de fechamentos
        return self.request.user.groups.filter(name='Administradores').exists()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Adiciona a variável para controlar o botão de reabertura
        context['pode_reabrir'] = FechamentoMensal.objects.filter(status='ATIVO').exists()
        return context


# --- VIEW PARA EXECUTAR O FECHAMENTO ---
class FazerFechamentoView(LoginRequiredMixin, UserPassesTestMixin, View):
    
    def test_func(self):
        # Apenas Admins podem executar o fechamento
        return self.request.user.groups.filter(name='Administradores').exists()

    def post(self, request, *args, **kwargs):
        # 1. Determinar o próximo período a ser fechado
        ultimo_fechamento = FechamentoMensal.objects.filter(status='ATIVO').order_by('ano', 'mes').last()
        
        if ultimo_fechamento:
            mes = ultimo_fechamento.mes + 1
            ano = ultimo_fechamento.ano
            if mes > 12:
                mes = 1
                ano += 1
        else:
            # Primeiro fechamento do sistema, pode ser o mês atual ou anterior
            hoje = timezone.now().date()
            mes = hoje.month
            ano = hoje.year

        # 2. Verificar se o fechamento já não existe e está ativo
        if FechamentoMensal.objects.filter(ano=ano, mes=mes, status='ATIVO').exists():
            messages.error(request, f"O fechamento para {mes:02d}/{ano} já foi realizado.")
            return redirect('materiais:painel_fechamento')
            
        # 3. Criar o registro de Fechamento
        fechamento = FechamentoMensal.objects.create(
            ano=ano,
            mes=mes,
            responsavel=request.user
        )

        # 4. Criar o "Snapshot" do estoque (PosicaoEstoqueMensal)
        produtos = Produto.objects.filter(ativo=True)
        for produto in produtos:
            saldo_final = produto.saldo_total # Usando a @property que você já tem
            custo_medio = produto.custo_medio # Usando a @property

            if saldo_final > 0:
                PosicaoEstoqueMensal.objects.create(
                    fechamento=fechamento,
                    produto=produto,
                    quantidade_final=saldo_final,
                    custo_medio_final=custo_medio,
                    valor_total_final=saldo_final * custo_medio
                )

        messages.success(request, f"Fechamento de {mes:02d}/{ano} realizado com sucesso!")
        return redirect('materiais:painel_fechamento')


# --- VIEW PARA REABRIR O ÚLTIMO FECHAMENTO ---
class ReabrirUltimoFechamentoView(LoginRequiredMixin, UserPassesTestMixin, View):
    
    def test_func(self):
        # Apenas Admins podem reabrir períodos
        return self.request.user.groups.filter(name='Administradores').exists()

    def post(self, request, *args, **kwargs):
        ultimo_fechamento_ativo = FechamentoMensal.objects.filter(status='ATIVO').order_by('ano', 'mes').last()

        if not ultimo_fechamento_ativo:
            messages.error(request, "Não há nenhum período de fechamento ativo para ser reaberto.")
            return redirect('materiais:painel_fechamento')

        # Atualiza o status e registra quem e quando cancelou
        ultimo_fechamento_ativo.status = 'CANCELADO'
        ultimo_fechamento_ativo.cancelado_por = request.user
        ultimo_fechamento_ativo.data_cancelamento = timezone.now()
        ultimo_fechamento_ativo.save()

        messages.warning(request, f"O período de fechamento de {ultimo_fechamento_ativo.mes:02d}/{ultimo_fechamento_ativo.ano} foi reaberto (cancelado).")
        return redirect('materiais:painel_fechamento')