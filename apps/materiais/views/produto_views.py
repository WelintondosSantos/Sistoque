# Em apps/materiais/views/produto_views.py

from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin

# As importações de modelos e formulários agora usam '..' para subir um nível de diretório.
from ..models import Produto

class ProdutoListView(LoginRequiredMixin, ListView):
    """
    Esta view lista todos os produtos cadastrados no sistema.
    """
    model = Produto
    template_name = 'materiais/produto_list.html'
    context_object_name = 'object_list'
    paginate_by = 20

    def get_queryset(self):
        """
        Otimiza a consulta para melhorar a performance.
        """
        return Produto.objects.select_related('categoria').order_by('nome_produto')

    def get_context_data(self, **kwargs):
        """
        Adiciona contexto extra ao template.
        """
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Posição de Estoque'
        return context
