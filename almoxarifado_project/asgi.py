# Em seu_projeto/asgi.py

import os
from django.core.asgi import get_asgi_application
# --- MUDANÇA: Importações necessárias para o Channels ---
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import apps.chat.routing  # Importa as rotas WebSocket do seu app de chat


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'almoxarifado_project.settings.development')

# --- MUDANÇA: Esta é a configuração chave ---
# ProtocolTypeRouter primeiro inspeciona o tipo de conexão.
# Se for um WebSocket (ws:// ou wss://), ele passa a conexão para o AuthMiddlewareStack.
application = ProtocolTypeRouter({
    # Conexões HTTP são tratadas pelo Django normalmente
    "http": get_asgi_application(),

    # Conexões WebSocket são tratadas pelo nosso roteador de chat
    "websocket": AuthMiddlewareStack(
        URLRouter(
            # Aponta para as rotas definidas no seu app de chat
            apps.chat.routing.websocket_urlpatterns
        )
    ),
})

