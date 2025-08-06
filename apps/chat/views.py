# Em apps/chat/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.urls import reverse
from django.http import JsonResponse

from .models import Conversa

UsuarioSistema = get_user_model()

class ChatHomeView(LoginRequiredMixin, View):
    template_name = 'chat/chat_home.html'

    def get(self, request, *args, **kwargs):
        conversas_existentes = Conversa.objects.filter(participantes=request.user).prefetch_related('participantes')
        user = request.user
        usuarios_contactaveis = UsuarioSistema.objects.none()
        user_groups = [group.name for group in user.groups.all()]

        if 'Almoxarifes' in user_groups or 'Administradores' in user_groups or user.is_superuser:
            usuarios_contactaveis = UsuarioSistema.objects.exclude(pk=user.pk)
        elif 'Requisitantes' in user_groups:
            usuarios_contactaveis = UsuarioSistema.objects.filter(
                Q(groups__name='Almoxarifes') | Q(groups__name='Administradores') | Q(is_superuser=True)
            ).distinct()

        contexto = {
            'page_title': 'Chat Interno',
            'conversas': conversas_existentes,
            'usuarios_contactaveis': usuarios_contactaveis
        }
        return render(request, self.template_name, contexto)


class IniciarConversaView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        outro_usuario_id = self.kwargs.get('user_id')
        outro_usuario = get_object_or_404(UsuarioSistema, pk=outro_usuario_id)
        
        conversa = Conversa.objects.filter(participantes=request.user).filter(participantes=outro_usuario)
        
        if conversa.exists():
            conversa_id = conversa.first().id
        else:
            nova_conversa = Conversa.objects.create()
            nova_conversa.participantes.add(request.user, outro_usuario)
            conversa_id = nova_conversa.id

        url_base = reverse('chat:chat_home')
        url_com_parametro = f"{url_base}?conversa_id={conversa_id}"
        return redirect(url_com_parametro)

# --- NOVA VIEW PARA O HISTÓRICO ---
class ConversaHistoryView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        conversa_id = self.kwargs.get('conversa_id')
        conversa = get_object_or_404(Conversa, pk=conversa_id, participantes=request.user)
        
        mensagens = conversa.mensagens.order_by('timestamp').select_related('autor__funcionario')
        
        # Formata os dados para serem enviados como JSON
        historico = []
        for msg in mensagens:
            historico.append({
                'user': msg.autor.funcionario.nome if msg.autor.funcionario else msg.autor.username,
                'message': msg.texto,
                'timestamp': msg.timestamp.strftime('%d/%m/%Y %H:%M')
            })
            
        return JsonResponse({'historico': historico})