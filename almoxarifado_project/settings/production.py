from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DEBUG', default=False)

# Domínios permitidos em produção. Lê a variável do .env
# Ex: "meusite.com,www.meusite.com"
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')

# Configuração do Channel Layer para produção (usando Redis)
# A URL do Redis será lida do arquivo .env
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [env('REDIS_URL')],
        },
    },
}

# Configurações de segurança para produção
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 ano
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Diretório para onde o `collectstatic` vai copiar os arquivos estáticos
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')