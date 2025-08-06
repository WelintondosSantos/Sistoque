# Em apps/chat/routing.py

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # --- MUDANÇA: A URL agora captura o ID da conversa ---
    re_path(r'ws/chat/(?P<conversa_id>\d+)/$', consumers.ChatConsumer.as_asgi()),
]