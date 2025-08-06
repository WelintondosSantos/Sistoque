# Em apps/materiais/views/entrada_views.py

from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction

# As importações de modelos e formulários agora usam '..' para subir um nível de diretório.
from ..models import MovimentoEstoque, Almoxarifado, Lote
from ..forms import EntradaForm

class EntradaCreateView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'materiais/entrada_form.html'
    form_class = EntradaForm

    def test_func(self):
        user = self.request.user
        return user.is_superuser or user.groups.filter(name__in=['Administradores', 'Almoxarifes']).exists()

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form, 'page_title': 'Registrar Entrada de Material'})

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            produto = form.cleaned_data['produto']
            quantidade = form.cleaned_data['quantidade']
            valor_unitario = form.cleaned_data['valor_unitario']
            data_validade = form.cleaned_data['data_validade']
            codigo_lote = form.cleaned_data['codigo_lote']
            observacao = form.cleaned_data['observacao']
            
            almoxarifado_padrao = Almoxarifado.objects.filter(ativo=True).first()
            if not almoxarifado_padrao:
                messages.error(request, "Erro: Nenhum almoxarifado ativo encontrado.")
                return render(request, self.template_name, {'form': form})

            # --- LÓGICA DE LOTE IMPLEMENTADA ---
            # 1. Encontra ou cria o lote para este produto e data de validade.
            lote, created = Lote.objects.get_or_create(
                produto=produto,
                data_validade=data_validade,
                defaults={
                    'codigo_lote': codigo_lote,
                    'quantidade_atual': 0 # A quantidade será adicionada a seguir
                }
            )
            
            # 2. Atualiza a quantidade do lote.
            lote.quantidade_atual += quantidade
            # Se o lote já existia, podemos atualizar o código dele se um novo foi fornecido.
            if not created and codigo_lote:
                lote.codigo_lote = codigo_lote
            lote.save()

            # 3. Cria o Movimento de Estoque ligado ao LOTE.
            MovimentoEstoque.objects.create(
                lote=lote, # <-- CORRIGIDO
                almoxarifado=almoxarifado_padrao,
                quantidade=quantidade,
                valor_unitario=valor_unitario,
                tipo='ENTRADA',
                usuario=request.user,
                observacao=observacao
            )
            
            messages.success(request, f"Entrada de {quantidade} unidade(s) de '{produto.nome_produto}' no lote com validade em {data_validade.strftime('%d/%m/%Y')} registrada com sucesso!")
            return redirect('materiais:lista_produtos')

        return render(request, self.template_name, {'form': form})
