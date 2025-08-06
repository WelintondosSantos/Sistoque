# Em apps/chat/admin.py

from django.contrib import admin
from .models import Conversa, Mensagem

@admin.register(Conversa)
class ConversaAdmin(admin.ModelAdmin):
    """
    Configuração de admin para o modelo Conversa.
    """
    list_display = ('id', '__str__', 'data_criacao')
    filter_horizontal = ('participantes',) # Usa um widget melhor para selecionar participantes
    search_fields = ('participantes__username',)

@admin.register(Mensagem)
class MensagemAdmin(admin.ModelAdmin):
    """
    Configuração de admin para o modelo Mensagem.
    """
    list_display = ('id', 'conversa', 'autor', 'texto', 'timestamp')
    list_filter = ('conversa', 'autor', 'timestamp')
    search_fields = ('texto', 'autor__username')
    
    # Tornamos o admin apenas para visualização, pois as mensagens devem ser criadas via chat
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
