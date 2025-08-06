# Em apps/users/management/commands/criar_usuarios_teste.py

from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.models import Group

class Command(BaseCommand):
    help = 'Cria usuários de teste pré-cadastrados com grupos e centros de custo.'

    # --- DADOS DE TESTE ---
    # Você pode adicionar, remover ou editar os usuários nesta lista.
    # Certifique-se de que a 'matricula' e o 'centro_custo' já existem no banco de dados.
    USUARIOS_TESTE = [
        
        {
            'matricula': '001041', # Matrícula do Employee
            'senha': 'teste',
            'grupo': 'Requisitantes',
            'centro_custo': 'GTC - Grupo Técnico de Pariquera - Açu'
        },
    ]
    

    @transaction.atomic
    def handle(self, *args, **options):
        # --- IMPORTAÇÕES MOVIDAS PARA DENTRO DO HANDLE ---
        from django.contrib.auth.models import Group
        from apps.users.models import UsuarioSistema
        from apps.core.models import Employee, CentroCusto

        self.stdout.write(self.style.SUCCESS('--- Iniciando o pré-cadastro de usuários de teste ---'))

        for dados_usuario in self.USUARIOS_TESTE:
            matricula = dados_usuario['matricula']
            senha = dados_usuario['senha']
            nome_grupo = dados_usuario['grupo']
            nome_cc = dados_usuario['centro_custo']

            if UsuarioSistema.objects.filter(username=matricula).exists():
                self.stdout.write(self.style.WARNING(f'Usuário com matrícula {matricula} já existe. A saltar.'))
                continue

            try:
                employee = Employee.objects.get(matricula=matricula)
                centro_custo = CentroCusto.objects.get(nome=nome_cc)
                grupo = Group.objects.get(name=nome_grupo)
            except (Employee.DoesNotExist, CentroCusto.DoesNotExist, Group.DoesNotExist) as e:
                self.stderr.write(self.style.ERROR(f'ERRO: Dependência não encontrada para o usuário {matricula}. Detalhe: {e}'))
                continue

            try:
                user = UsuarioSistema.objects.create_user(
                    username=matricula,
                    password=senha,
                    email=employee.email,
                    funcionario=employee,
                    centro_custo=centro_custo
                )
                user.groups.add(grupo)
                self.stdout.write(self.style.SUCCESS(f'Usuário {matricula} criado com sucesso.'))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'ERRO inesperado ao criar o usuário {matricula}: {e}'))

        self.stdout.write(self.style.SUCCESS('--- Pré-cadastro concluído com sucesso! ---'))