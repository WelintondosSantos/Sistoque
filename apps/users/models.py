# Em apps/users/models.py

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from apps.core.models import Employee, CentroCusto 

class UsuarioSistemaManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('O nome de usuário (matrícula) é obrigatório')
        
        email = self.normalize_email(extra_fields.pop('email', None))
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, password, **extra_fields)


class UsuarioSistema(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(unique=True, max_length=50, verbose_name="Login (Matrícula)")
    email = models.EmailField(
        verbose_name='endereço de e-mail',
        max_length=255,
        unique=True,
        null=True,
        blank=True
    )
    funcionario = models.OneToOneField(Employee, on_delete=models.CASCADE, db_column='matricula_funcionario', null=True)
    

    centro_custo = models.ForeignKey(
        CentroCusto, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True,
        verbose_name="Centro de Custo"
    )
    
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    is_staff = models.BooleanField(default=False, verbose_name="Acesso ao Admin")
    
    objects = UsuarioSistemaManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = "Usuário do Sistema"
        verbose_name_plural = "Usuários do Sistema"

    def __str__(self):
        return self.username

