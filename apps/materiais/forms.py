# Em apps/materiais/forms.py

from django import forms
from django.forms import modelformset_factory
from .models import Produto, ItemRequisicao

# ... (seu RequisicaoForm e AtendimentoFormSet existentes) ...
class RequisicaoForm(forms.Form):
    produto = forms.ModelChoiceField(
        queryset=Produto.objects.filter(ativo=True).order_by('nome_produto'),
        label="Produto",
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="--- Selecione um produto ---"
    )
    quantidade = forms.IntegerField(
        label="Quantidade",
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 5'})
    )

    def clean_quantidade(self):
        quantidade_pedida = self.cleaned_data.get('quantidade')
        produto_selecionado = self.cleaned_data.get('produto')
        if produto_selecionado and quantidade_pedida:
            saldo_disponivel = produto_selecionado.saldo_total
            if quantidade_pedida > saldo_disponivel:
                raise forms.ValidationError(
                    f"Saldo insuficiente. Saldo atual: {saldo_disponivel}. Você pediu {quantidade_pedida}."
                )
        return quantidade_pedida


class AtendimentoItemForm(forms.ModelForm):
    class Meta:
        model = ItemRequisicao
        fields = ['quantidade_atendida']
        widgets = {
            'quantidade_atendida': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'min': 0})
        }

    def clean_quantidade_atendida(self):
        item = self.instance
        quantidade_atendida = self.cleaned_data.get('quantidade_atendida')
        if quantidade_atendida is None:
            quantidade_atendida = 0
        if quantidade_atendida < 0:
            raise forms.ValidationError("A quantidade não pode ser negativa.")
        if quantidade_atendida > item.produto.saldo_total:
            raise forms.ValidationError(
                f"Saldo insuficiente. Saldo atual de '{item.produto.nome_produto}': {item.produto.saldo_total}."
            )
        return quantidade_atendida

AtendimentoFormSet = modelformset_factory(
    ItemRequisicao,
    form=AtendimentoItemForm,
    extra=0,
    can_delete=False
)


class EntradaForm(forms.Form):
    """
    Formulário para o almoxarife registrar a entrada de materiais,
    agora incluindo informações de lote e validade.
    """
    produto = forms.ModelChoiceField(
        queryset=Produto.objects.filter(ativo=True).order_by('nome_produto'),
        label="Produto",
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="--- Selecione um produto ---"
    )
    quantidade = forms.IntegerField(
        label="Quantidade Recebida",
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    valor_unitario = forms.DecimalField(
        label="Valor Unitário (R$)",
        min_value=0.01,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 15.50'})
    )
    # --- NOVOS CAMPOS ADICIONADOS ---
    data_validade = forms.DateField(
        label="Data de Validade",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    codigo_lote = forms.CharField(
        label="Código do Lote/Referência",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    observacao = forms.CharField(
        label="Observação (Ex: Nota de Empenho, Fornecedor)",
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
