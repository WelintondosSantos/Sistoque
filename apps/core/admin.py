from django.contrib import admin

# Em apps/core/admin.py

from django.contrib import admin
# Certifique-se de que os seus modelos estão importados
from .models import Employee, CentroCusto

# Se você já tem um admin para Employee, mantenha-o.
# @admin.register(Employee)
# class EmployeeAdmin(admin.ModelAdmin):
#     ...

# --- ADICIONE O CÓDIGO ABAIXO ---

@admin.register(CentroCusto)
class CentroCustoAdmin(admin.ModelAdmin):
    """
    Configuração de admin para o modelo CentroCusto.
    """
    list_display = ('nome', 'parent')
    search_fields = ('nome',)
    list_filter = ('parent',)
    ordering = ('nome',)

