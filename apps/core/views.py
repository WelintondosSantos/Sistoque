# apps/core/views.py

from django.db.models import Prefetch
from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required

User = get_user_model()

@login_required
def dashboard_view(request):
    """
    Renderiza a página principal/dashboard, incluindo o contexto para o chat.
    """
    
    # --- Início da Lógica do Chat ---
    
    # 1. Buscar conversas ativas, otimizando a consulta para o template.
    # Usamos prefetch_related para evitar múltiplas consultas ao banco de dados
    # ao buscar os nomes dos participantes no template.
    conversas_ativas = request.user.conversas.prefetch_related('participantes').all()

    # 2. Buscar usuários para iniciar novas conversas.
    user_groups = request.user.groups.values_list('name', flat=True)
    
    if "Requisitantes" in user_groups:
        usuarios_para_chat = User.objects.filter(groups__name__in=["Almoxarifes", "Administradores"])
    elif "Almoxarifes" in user_groups or "Administradores" in user_groups:
        usuarios_para_chat = User.objects.all()
    else:
        usuarios_para_chat = User.objects.none() # Garante que a variável sempre exista

    # Exclui o próprio usuário e usuários com quem já há conversa
    usuarios_com_conversa_ativa = User.objects.filter(conversas__in=conversas_ativas)
    usuarios_para_chat = usuarios_para_chat.exclude(pk=request.user.pk).exclude(pk__in=usuarios_com_conversa_ativa)

    # --- Fim da Lógica do Chat ---

    # Contexto principal da dashboard
    context = {
        'page_title': 'Painel de Controle Principal',
        'urgent_alerts': [],
        'general_notices': [],
        'conversas_ativas': conversas_ativas,
        'usuarios_para_chat': usuarios_para_chat,
    }

    return render(request, 'core/home.html', context)