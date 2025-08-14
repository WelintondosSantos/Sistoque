from django import template

# Cria uma instância da biblioteca de templates onde nossos filtros serão registrados
register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name):
    """
    Verifica se um usuário pertence a um grupo específico.
    Uso no template: {% if user|has_group:'NomeDoGrupo' %}
    """
    # Retorna True se o usuário tiver um grupo com o nome passado, senão False
    return user.groups.filter(name=group_name).exists()