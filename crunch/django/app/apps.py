from django.apps import AppConfig
from importlib import import_module

class CrunchConfig(AppConfig):
    name = "crunch"

    def ready(self):
        super().ready()
        import_module('crunch.django.app.admin') # needed because the autodiscover doesn't work unless admin.py is in top directory of app
