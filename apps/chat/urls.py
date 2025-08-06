# Em apps/chat/urls.py

from django.urls import path
from .views import ChatHomeView, IniciarConversaView, ConversaHistoryView

app_name = 'chat'

urlpatterns = [
    path('', ChatHomeView.as_view(), name='chat_home'),
    path('iniciar/<int:user_id>/', IniciarConversaView.as_view(), name='iniciar_conversa'),
    path('historico/<int:conversa_id>/', ConversaHistoryView.as_view(), name='historico_conversa'),
]