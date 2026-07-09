from django.apps import AppConfig

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    verbose_name = 'Gestão de Usuários'

    def ready(self):
        # Esse código roda APÓS todos os apps estarem carregados perfeitamente
        from django.apps import apps
        try:
            apps.get_app_config('admin_honeypot').verbose_name = 'Tentativas de Invasão'
        except LookupError:
            pass  # Evita quebrar se o admin_honeypot não estiver instalado por algum motivo