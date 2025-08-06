# Em apps/relatorios/forms.py

from django import forms
from apps.core.models import CentroCusto

class ReportFilterForm(forms.Form):
    """
    Formulário para filtrar os dados do relatório de consumo.
    """
    data_inicio = forms.DateField(
        label="Data de Início",
        required=True,
        widget=forms.DateInput(
            attrs={
                'class': 'form-control',
                'type': 'date' # Usa o seletor de data nativo do navegador
            }
        ),
        help_text="Início do período de análise."
    )

    data_fim = forms.DateField(
        label="Data de Fim",
        required=True,
        widget=forms.DateInput(
            attrs={
                'class': 'form-control',
                'type': 'date'
            }
        ),
        help_text="Fim do período de análise."
    )

    # Usamos um ModelMultipleChoiceField para permitir a seleção de um ou mais Centros de Custo.
    centros_de_custo = forms.ModelMultipleChoiceField(
        label="Centros de Custo",
        queryset=CentroCusto.objects.all().order_by('nome'),
        required=True,
        widget=forms.SelectMultiple(
            attrs={
                'class': 'form-select',
                'size': '8' # Define a altura da caixa de seleção
            }
        ),
        help_text="Selecione um ou mais centros de custo (mantenha Ctrl ou Shift pressionado para selecionar vários)."
    )

    def clean(self):
        """
        Validação para garantir que a data de início não seja posterior à data de fim.
        """
        cleaned_data = super().clean()
        data_inicio = cleaned_data.get("data_inicio")
        data_fim = cleaned_data.get("data_fim")

        if data_inicio and data_fim:
            if data_inicio > data_fim:
                raise forms.ValidationError(
                    "A data de início não pode ser posterior à data de fim."
                )
        
        return cleaned_data