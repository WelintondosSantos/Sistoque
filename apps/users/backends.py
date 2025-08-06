# Em apps/users/backends.py

from .models import UsuarioSistema

class UsuarioSistemaBackend:
    """
    Backend de autenticação refatorado para funcionar com o modelo
    UsuarioSistema que herda de AbstractBaseUser.
    """
    def authenticate(self, request, username=None, password=None):
        try:
            # 1. Busca o usuário pelo username (matrícula)
            user = UsuarioSistema.objects.get(username=username)

            # 2. Usa o método check_password() do próprio modelo, que já sabe
            #    como comparar a senha fornecida com o hash no banco.
            if user.check_password(password) and user.is_active:
                return user
            
            # Se a senha estiver incorreta ou o usuário inativo, retorna None.
            return None
        except UsuarioSistema.DoesNotExist:
            # Se o usuário não existe, retorna None.
            return None

    def get_user(self, user_id):
        """
        Busca um usuário pelo seu ID (usado pelo Django para gerenciar a sessão).
        """
        try:
            return UsuarioSistema.objects.get(pk=user_id)
        except UsuarioSistema.DoesNotExist:
            return None