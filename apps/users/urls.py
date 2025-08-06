# apps/users/urls.py 

from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from .views import login_view, logout_view, register_view, RequisitanteDashboardView
from . import views

app_name = 'authentication'

urlpatterns = [
    # Rotas de Login / Registro / Logout (permanecem as mesmas, pois usam nossas views customizadas)
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # URL para o painel de controle do requisitante.
    path(
        'dashboard/requisitante/', 
        RequisitanteDashboardView.as_view(), 
        name='dashboard_requisitante'
    ),
    path('dashboard/requisitante/', RequisitanteDashboardView.as_view(), name='dashboard_requisitante'),


    # --- Rotas de Redefinição de Senha (agora usando as views padrão sem customizações) ---

    # 1. Formulário para pedir o reset
    path(
        'password_reset/',
        auth_views.PasswordResetView.as_view(
            template_name="registration/password_reset_form.html",
            email_template_name='registration/password_reset_email.html', # Template para o corpo do e-mail
            subject_template_name='registration/password_reset_subject.txt', # Template para o assunto do e-mail
            success_url=reverse_lazy('authentication:password_reset_done')
        ),
        name='password_reset'
    ),

    # 2. Página de sucesso após pedir o reset
    path(
        'password_reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name="registration/password_reset_done.html"
        ),
        name='password_reset_done'
    ),

    # 3. Link do e-mail, onde o usuário define a nova senha
    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name="registration/password_reset_confirm.html",
            success_url=reverse_lazy('authentication:password_reset_complete')
        ),
        name='password_reset_confirm'
    ),

    # 4. Página de sucesso após a senha ser alterada
    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name="registration/password_reset_complete.html"
        ),
        name='password_reset_complete'
    ),
]