# Em apps/users/views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.contrib.auth.models import Group
from .forms import RegistrationForm, UserLoginForm
from apps.core.models import Employee
from .models import UsuarioSistema
from apps.materiais.models import Requisicao 
def login_view(request):
    """
    Processa o login do usuário, redirecionando sempre para o painel principal.
    A navegação específica para cada perfil é controlada pelos menus nos templates.
    """
    if request.user.is_authenticated:
        # Se o usuário já está logado, envia-o para o painel principal.
        return redirect('core:dashboard')

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                
                # 1. Prioridade máxima: Se o usuário tentava aceder a uma página
                # específica antes do login, é para lá que ele deve ir.
                # Esta lógica foi mantida.
                next_page = request.GET.get('next')
                if next_page:
                    return redirect(next_page)
                
                # --- MUDANÇA PRINCIPAL ---
                # 2. Rota padrão: Após o login, todos os usuários são enviados
                # para o mesmo painel principal.
                return redirect('core:dashboard')

    else:
        form = UserLoginForm()
        
    return render(request, 'registration/login.html', {'form': form})


def register_view(request):
    """
    Processa o registro de um novo usuário, associando-o a um funcionário
    e adicionando-o automaticamente ao grupo 'Requisitantes'.
    """
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            matricula = form.cleaned_data['matricula']
            password = form.cleaned_data['password_1']
            
            try:
                employee = Employee.objects.get(matricula=matricula)
                # A linha que criava o 'perfil_padrao' foi removida.

                # O campo 'perfil' foi removido da criação do usuário.
                user = UsuarioSistema.objects.create_user(
                    username=matricula,
                    password=password,
                    funcionario=employee,
                    email=employee.email
                )

                # A lógica de adicionar ao grupo 'Requisitantes' permanece.
                try:
                    grupo_requisitantes = Group.objects.get(name='Requisitantes')
                    user.groups.add(grupo_requisitantes)
                except Group.DoesNotExist:
                    messages.error(request, 'Erro crítico de configuração: O grupo "Requisitantes" não foi encontrado. Contate o administrador.')
                    user.delete()
                    return redirect('authentication:register')

                messages.success(request, 'Conta criada com sucesso! Por favor, faça o login.')
                return redirect('authentication:login')
            
            except Employee.DoesNotExist:
                form.add_error('matricula', 'Matrícula não encontrada na base de dados de funcionários.')
            except Exception as e:
                messages.error(request, f'Ocorreu um erro inesperado: {e}')
    else:
        form = RegistrationForm()

    return render(request, 'registration/register.html', {'form': form})


@login_required # Garante que apenas usuários logados possam acessar a URL de logout
def logout_view(request):
    """
    Processa o logout do usuário. Responde apenas a requisições POST por segurança.
    """
    if request.method == 'POST':
        logout(request)
        messages.success(request, "Você saiu do sistema com segurança.")
    
    # Após o logout (ou se o acesso for GET), redireciona sempre para a página de login.
    return redirect('authentication:login')

class RequisitanteDashboardView(LoginRequiredMixin, TemplateView):
    """
    Exibe o painel de controle principal para os usuários do grupo 'Requisitantes'.
    """
    template_name = 'users/dashboard_requisitante.html'

    def get_context_data(self, **kwargs):
        """
        Adiciona contexto extra ao template, como o título da página.
        """
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Painel do Requisitante'
        # Futuramente, aqui buscaremos o histórico de requisições deste usuário.
        # context['minhas_requisicoes'] = ...
        return context
    
class RequisitanteDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'users/dashboard_requisitante.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Painel do Requisitante'
        # Busca todas as requisições feitas pelo usuário logado,
        # ordenando pelas mais recentes primeiro.
        context['minhas_requisicoes'] = Requisicao.objects.filter(
            solicitante=self.request.user
        ).order_by('-data_criacao')
        
        return context   

