# Em apps/users/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import UsuarioSistema

@admin.register(UsuarioSistema)
class UsuarioSistemaAdmin(BaseUserAdmin):
    """Define a configuração de admin para o modelo customizado UsuarioSistema."""
    list_display = ('username', 'get_full_name', 'centro_custo', 'is_active', 'is_staff')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'groups', 'centro_custo')
    
    search_fields = ('username', 'funcionario__nome', 'email', 'centro_custo__nome')
    ordering = ('username',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informações Pessoais', {'fields': ('funcionario', 'email', 'centro_custo')}),
        ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Datas Importantes', {'fields': ('last_login',)}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'funcionario', 'centro_custo'),
        }),
    )
    
    readonly_fields = ('last_login',)

    @admin.display(description='Nome Completo')
    def get_full_name(self, obj):
        if obj.funcionario:
            return obj.funcionario.nome
        return "N/A"

