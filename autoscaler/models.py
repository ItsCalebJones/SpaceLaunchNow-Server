from django.db import models

from spacelaunchnow.base_models import SingletonModel


class AutoscalerSettings(SingletonModel):
    enabled = models.BooleanField(default=False)
    custom_worker_count = models.IntegerField(null=True, blank=True, default=None)
    current_workers = models.IntegerField(null=True, blank=True, default=None)
    max_workers = models.IntegerField(null=False, blank=False, default=5)

    def __str__(self):
        return "Autoscaler Settings"
