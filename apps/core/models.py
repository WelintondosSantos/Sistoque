from django.db import models

# Create your models here.

# Modelo para Funcionários
class Employee(models.Model):
    # O campo 'matricula' é a chave primária natural desta tabela.

    matricula = models.CharField(primary_key=True, max_length=20, verbose_name="Matrícula")
    nome = models.CharField(max_length=100, verbose_name="Nome Completo")
    lotacao = models.CharField(max_length=100, blank=True, null=True, verbose_name="Lotação")
    gerencia_assessoria = models.CharField(max_length=100, blank=True, null=True, verbose_name="Gerência/Assessoria")
    diretoria = models.CharField(max_length=100, blank=True, null=True, verbose_name="Diretoria")
    email = models.EmailField(max_length=100, blank=True, null=True, verbose_name="E-mail")
    
    # Alterado para BooleanField, que é mais apropriado para flags de ativo/inativo.
    ativo = models.BooleanField(default=True, verbose_name="Ativo")

    def __str__(self):
        return f"{self.matricula} - {self.nome}"

    class Meta:
        # Link para a tabela existente.
        db_table = 'employees'
        verbose_name = "Funcionário"
        verbose_name_plural = "Funcionários"


# Modelo para Setores Requisitantes
class SetorRequisitante(models.Model):
    # O Django adiciona um 'id' autoincremental por padrão, que servirá como PK.
    nome_setor = models.CharField(unique=True, max_length=150, verbose_name="Nome do Setor")
    codigo_setor = models.CharField(unique=True, max_length=50, blank=True, null=True, verbose_name="Código do Setor")
    
    # Relação com o responsável. Você ajustará os detalhes da relação depois.
    responsavel_setor = models.ForeignKey(Employee, on_delete=models.SET_NULL, blank=True, null=True, db_column='id_responsavel_setor')
    
    ativo = models.BooleanField(default=True, verbose_name="Ativo")

    def __str__(self):
        return self.nome_setor

    class Meta:
        db_table = 'setoresrequisitantes'
        verbose_name = "Setor Requisitante"
        verbose_name_plural = "Setores Requisitantes"

# Em apps/core/models.py

from django.db import models

# ... seus outros modelos do app core (como Employee) ...

# --- ADICIONE O NOVO MODELO ABAIXO ---

class CentroCusto(models.Model):
    """
    Representa uma unidade organizacional (Diretoria, Lotação, Divisão).
    """
    nome = models.CharField(max_length=255, unique=True, verbose_name="Nome da Unidade")
    
    # Um ForeignKey para 'self' é o que nos permite criar a hierarquia.
    # Uma Divisão pode ter uma Lotação como 'parent', e uma Lotação pode ter uma Diretoria.
    parent = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, # Usamos SET_NULL para não apagar em cascata
        null=True, 
        blank=True, 
        related_name='children',
        verbose_name="Unidade Superior (Pai)"
    )

    class Meta:
        verbose_name = "Centro de Custo"
        verbose_name_plural = "Centros de Custo"
        ordering = ['nome']

    def __str__(self):
        return self.nome
