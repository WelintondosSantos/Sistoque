# Em apps/users/forms.py

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from apps.core.models import Employee
from .models import UsuarioSistema

# Este formulário continua necessário por causa da nossa regra de negócio
# de validar a matrícula contra a tabela de funcionários.
class RegistrationForm(forms.Form):
    matricula = forms.CharField(
        label='Matrícula',
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Digite sua matrícula funcional'
        })
    )
    password_1 = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Crie uma senha'
        })
    )
    password_2 = forms.CharField(
        label='Confirme a Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite a senha novamente'
        })
    )

    def clean_matricula(self):
        matricula = self.cleaned_data.get('matricula')
        if not Employee.objects.filter(matricula=matricula).exists():
            raise ValidationError("Matrícula não encontrada. Verifique o número digitado.")
        if UsuarioSistema.objects.filter(username=matricula).exists():
            raise ValidationError("Esta matrícula já possui uma conta de acesso ao sistema.")
        return matricula

    def clean(self):
        cleaned_data = super().clean()
        password_1 = cleaned_data.get("password_1")
        password_2 = cleaned_data.get("password_2")
        if password_1 and password_2 and password_1 != password_2:
            self.add_error('password_2', "As senhas não conferem.")
        return cleaned_data

# Este formulário é útil para aplicarmos classes CSS do Bootstrap
# ao formulário de login padrão do Django.
class UserLoginForm(AuthenticationForm):
    username = forms.CharField(label='Usuário', widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Digite sua matrícula'
    }))
    password = forms.CharField(label='Senha', widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Digite sua senha'
    }))
