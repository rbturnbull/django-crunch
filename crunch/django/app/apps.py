from django.apps import AppConfig

class CrunchConfig(AppConfig):
    name = "crunch"

    def ready(self):
        super().ready()
        
        # needed because the autodiscover doesn't work unless admin.py is in top directory of app
        from . import admin, tokens
