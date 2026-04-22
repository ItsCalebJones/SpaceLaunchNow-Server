from django.apps import AppConfig


class SlnApiConfig(AppConfig):
    name = "sln_api"
    verbose_name = "SLN API"

    def ready(self):
        pass
