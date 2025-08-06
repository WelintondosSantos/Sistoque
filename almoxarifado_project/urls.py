# Em almoxarifado_project/urls.py

from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('apps.users.urls', namespace='authentication')),
    path('chat/', include('apps.chat.urls', namespace='chat')),

    # ALTERAÇÃO: Agora, o dashboard e outras páginas do app 'core'
    # serão acessadas a partir de /home/
    path('home/', include('apps.core.urls', namespace='core')),

    # MELHOR PRÁTICA: Redireciona a raiz do site ('/') para a nova página inicial ('/home/')
    # permanent=True informa aos navegadores que essa mudança é definitiva.
    path('', RedirectView.as_view(url='/home/', permanent=True)),

     # Todas as URLs de materiais serão prefixadas com 'materiais/'
    path('materiais/', include('apps.materiais.urls', namespace='materiais')),
     # Todas as URLs de relatorios serão prefixadas com 'relatorios/'
    path('relatorios/', include('apps.relatorios.urls', namespace='relatorios')),
]