# Em apps/materiais/views/requisicao_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import DetailView, DeleteView, ListView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.db import transaction
from django.utils import timezone
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML

# As importações de modelos e formulários agora usam '..' para subir um nível de diretório.
from ..models import MovimentoEstoque, Almoxarifado, Requisicao, ItemRequisicao, Produto, Lote
from ..forms import RequisicaoForm, AtendimentoFormSet, EntradaForm

# ... (outras views como ProdutoListView, RequisicaoCreateView, etc., permanecem as mesmas) ...
class ProdutoListView(LoginRequiredMixin, ListView):
    model = Produto
    template_name = 'materiais/produto_list.html'
    context_object_name = 'object_list'
    paginate_by = 20

    def get_queryset(self):
        return Produto.objects.select_related('categoria').order_by('nome_produto')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Posição de Estoque'
        return context

class RequisicaoCreateView(LoginRequiredMixin, View):
    template_name = 'materiais/requisicao_form.html'
    form_class = RequisicaoForm

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form, 'page_title': 'Adicionar Item à Requisição'})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            produto = form.cleaned_data['produto']
            quantidade = form.cleaned_data['quantidade']
            
            if not request.user.centro_custo:
                messages.error(request, "A sua conta não está associada a um Centro de Custo. Por favor, contacte o administrador.")
                return render(request, self.template_name, {'form': form})

            requisicao_aberta, created = Requisicao.objects.get_or_create(
                solicitante=request.user,
                status='ABERTO',
                defaults={'centro_custo': request.user.centro_custo}
            )
            item, item_created = ItemRequisicao.objects.get_or_create(
                requisicao=requisicao_aberta,
                produto=produto,
                defaults={'quantidade': quantidade}
            )
            if not item_created:
                item.quantidade += quantidade
                item.save()
                messages.info(request, f"Quantidade do item '{produto.nome_produto}' atualizada na sua requisição.")
            else:
                messages.success(request, f"Item '{produto.nome_produto}' adicionado à sua requisição.")
            return redirect('materiais:detalhe_requisicao', pk=requisicao_aberta.pk)
        return render(request, self.template_name, {'form': form, 'page_title': 'Adicionar Item à Requisição'})

class RequisicaoDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Requisicao
    template_name = 'materiais/requisicao_detalhe.html'
    context_object_name = 'requisicao'

    def test_func(self):
        requisicao = self.get_object()
        user = self.request.user
        if user == requisicao.solicitante:
            return True
        if user.is_superuser or user.groups.filter(name__in=['Administradores', 'Almoxarifes']).exists():
            return True
        return False
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f"Detalhes da Requisição #{self.object.pk}"
        return context

    
class ItemRequisicaoDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = ItemRequisicao
    
    def test_func(self):
        item = self.get_object()
        return self.request.user == item.requisicao.solicitante and item.requisicao.status == 'ABERTO'

    def get_success_url(self):
        item = self.get_object()
        messages.success(self.request, f"Item '{item.produto.nome_produto}' removido da requisição.")
        return reverse_lazy('materiais:detalhe_requisicao', kwargs={'pk': item.requisicao.pk})

    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)


class RequisicaoFinalizarView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        requisicao = get_object_or_404(Requisicao, pk=self.kwargs.get('pk'))
        return self.request.user == requisicao.solicitante and requisicao.status == 'ABERTO'

    def post(self, request, *args, **kwargs):
        requisicao_id = self.kwargs.get('pk')
        requisicao = get_object_or_404(Requisicao, pk=requisicao_id)

        if not requisicao.itens.exists():
            messages.error(request, "Não é possível finalizar uma requisição vazia.")
            return redirect('materiais:detalhe_requisicao', pk=requisicao.pk)

        requisicao.status = 'FINALIZADA'
        requisicao.data_finalizacao = timezone.now()
        requisicao.save()

        messages.success(request, f"Requisição #{requisicao.id} finalizada e enviada para o almoxarifado com sucesso!")
        return redirect('authentication:dashboard_requisitante')
        
class RequisicaoPendenteListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Requisicao
    template_name = 'materiais/requisicao_pendente_list.html'
    context_object_name = 'requisicoes_pendentes'
    paginate_by = 20

    def test_func(self):
        user = self.request.user
        return user.is_superuser or \
               user.groups.filter(name='Administradores').exists() or \
               user.groups.filter(name='Almoxarifes').exists()

    def get_queryset(self):
        return Requisicao.objects.filter(status='FINALIZADA').order_by('data_finalizacao')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Requisições Pendentes de Atendimento'
        return context        

class RequisicaoDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Requisicao
    template_name = 'materiais/requisicao_confirm_delete.html'
    success_url = reverse_lazy('authentication:dashboard_requisitante')

    def test_func(self):
        requisicao = self.get_object()
        return self.request.user == requisicao.solicitante and requisicao.status == 'ABERTO'

    def form_valid(self, form):
        messages.success(self.request, f"Requisição #{self.object.pk} foi cancelada com sucesso.")
        return super().form_valid(form)

class RequisicaoEstornarView(LoginRequiredMixin, UserPassesTestMixin, View):

    def test_func(self):
        user = self.request.user
        return user.is_superuser or user.groups.filter(name__in=['Administradores', 'Almoxarifes']).exists()

    def post(self, request, *args, **kwargs):
        requisicao = get_object_or_404(Requisicao, pk=self.kwargs.get('pk'))
        motivo = request.POST.get('motivo_estorno', 'Cancelamento realizado pelo almoxarifado.')

        # Apenas requisições 'FINALIZADA' podem ser canceladas desta forma.
        if requisicao.status != 'FINALIZADA':
            messages.error(request, "Esta requisição não pode ser cancelada/estornada pois não está no estado 'Finalizada'.")
            return redirect('materiais:detalhe_requisicao', pk=requisicao.pk)

        try:
            # NENHUM MOVIMENTO DE ESTOQUE É NECESSÁRIO AQUI.
            # Apenas atualizamos o status e os dados de auditoria.
            requisicao.status = 'CANCELADA'
            requisicao.estornado_por = request.user # Reutilizamos o campo para saber quem cancelou
            requisicao.data_estorno = timezone.now()
            requisicao.motivo_estorno = motivo
            requisicao.save()

            messages.success(request, f"Requisição #{requisicao.id} cancelada com sucesso! Nenhum item foi retirado do estoque.")
            return redirect('materiais:lista_requisicoes_pendentes')

        except Exception as e:
            messages.error(request, f"Ocorreu um erro inesperado durante o cancelamento: {e}")
            return redirect('materiais:detalhe_requisicao', pk=requisicao.pk)

class RequisicaoAtendimentoView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'materiais/requisicao_atendimento_form.html'

    def test_func(self):
        user = self.request.user
        return user.is_superuser or user.groups.filter(name__in=['Administradores', 'Almoxarifes']).exists()

    def get(self, request, *args, **kwargs):
        requisicao = get_object_or_404(Requisicao, pk=self.kwargs.get('pk'))
        formset = AtendimentoFormSet(queryset=requisicao.itens.all())
        
        for form in formset:
            form.initial['quantidade_atendida'] = form.instance.quantidade

        return render(request, self.template_name, {
            'requisicao': requisicao,
            'formset': formset,
            'page_title': f'Atender Requisição #{requisicao.pk}'
        })

    def post(self, request, *args, **kwargs):
        requisicao = get_object_or_404(Requisicao, pk=self.kwargs.get('pk'))
        formset = AtendimentoFormSet(request.POST, queryset=requisicao.itens.all())

        if formset.is_valid():
            try:
                with transaction.atomic():
                    almoxarifado_padrao = Almoxarifado.objects.filter(ativo=True).first()
                    if not almoxarifado_padrao:
                        raise ValueError("Nenhum almoxarifado ativo encontrado.")
                    
                    formset.save() # Salva as quantidades atendidas nos itens

                    # --- LÓGICA FEFO (First-Expire, First-Out) ---
                    for item in requisicao.itens.all():
                        quantidade_a_atender = item.quantidade_atendida
                        if not quantidade_a_atender or quantidade_a_atender <= 0:
                            continue

                        # Busca os lotes do produto com saldo, ordenados pela data de validade
                        lotes_disponiveis = Lote.objects.filter(
                            produto=item.produto,
                            quantidade_atual__gt=0
                        ).order_by('data_validade')

                        for lote in lotes_disponiveis:
                            if quantidade_a_atender <= 0:
                                break # Já atendemos a quantidade necessária para este item

                            quantidade_a_retirar = min(lote.quantidade_atual, quantidade_a_atender)
                            
                            # Cria o movimento de SAÍDA ligado ao LOTE específico
                            MovimentoEstoque.objects.create(
                                lote=lote, # <-- CORRIGIDO
                                almoxarifado=almoxarifado_padrao,
                                quantidade=quantidade_a_retirar,
                                tipo='SAIDA',
                                usuario=request.user,
                                observacao=f"Atendimento da Requisição #{requisicao.id}"
                            )
                            
                            # Atualiza o saldo do lote
                            lote.quantidade_atual -= quantidade_a_retirar
                            lote.save()
                            
                            # Decrementa a quantidade que ainda falta atender
                            quantidade_a_atender -= quantidade_a_retirar
                    
                    requisicao.status = 'ATENDIDA'
                    requisicao.atendido_por = request.user
                    requisicao.data_atendimento = timezone.now()
                    requisicao.save()

                    messages.success(request, f"Requisição #{requisicao.id} atendida com sucesso!")
                    return redirect('materiais:lista_requisicoes_pendentes')

            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f"Ocorreu um erro inesperado: {e}")
        
        return render(request, self.template_name, {
            'requisicao': requisicao,
            'formset': formset,
            'page_title': f'Atender Requisição #{requisicao.pk}'
        })
    
class RequisicaoPDFView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        # A mesma lógica de permissão da DetailView
        user = self.request.user
        requisicao = get_object_or_404(Requisicao, pk=self.kwargs.get('pk'))
        if user == requisicao.solicitante: return True
        if user.is_superuser or user.groups.filter(name__in=['Administradores', 'Almoxarifes']).exists(): return True
        return False

    def get(self, request, *args, **kwargs):
        requisicao = get_object_or_404(Requisicao, pk=self.kwargs.get('pk'))
        
        # Renderiza o template HTML para uma string
        html_string = render_to_string('materiais/requisicao_pdf.html', {'requisicao': requisicao})
        
        # Gera o PDF a partir da string HTML
        pdf = HTML(string=html_string).write_pdf()
        
        # Cria a resposta HTTP com o conteúdo do PDF
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="requisicao_{requisicao.pk}.pdf"'
        
        return response    